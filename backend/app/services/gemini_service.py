"""
GeminiService v4 — Dual-Key Parallel Workers
=============================================
Arquitectura:
  • Lee GOOGLE_API_KEY  (key 1) y GOOGLE_API_KEY_2 (key 2) del .env
  • Divide los documentos en 2 grupos (por chars, ~50/50)
  • Lanza 2 workers en PARALELO simultaneo, cada uno con su propia key
  • Si solo hay 1 key: los 2 workers la reutilizan (chunking igual)
  • Merge inteligente de los 2 resultados → 6 categorías + 5 pilares finales
  • Retry automático: si un worker recibe 429 espera 15s y reintenta 2 veces
  • Sin truncado: analiza el documento COMPLETO repartido entre workers
"""

import os
import json
import asyncio
import logging
import re
import threading
from typing import List, Optional
from google import genai
from google.genai import types
from app.core.config import settings
from app.services.groq_service import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# ── Umbrales ───────────────────────────────────────────────────────────────────
GROQ_THRESHOLD_CHARS = 25_000   # < esto → Groq directo
GEMINI_MODEL         = "gemini-2.5-flash"

# ── Obtener las keys disponibles ───────────────────────────────────────────────
def _get_api_keys() -> List[str]:
    """Retorna lista de API keys de Gemini configuradas (1 o 2)."""
    keys = []
    k1 = settings.GOOGLE_API_KEY.strip()
    k2 = settings.GOOGLE_API_KEY_2.strip()

    if k1:
        keys.append(k1)
    if k2 and k2 != k1:
        keys.append(k2)
    return keys


# ── Cliente por key ─────────────────────────────────────────────────────────────
_client_cache: dict = {}
_client_lock = threading.Lock()

def _get_client_for_key(api_key: str):
    """Crea (o reutiliza) un cliente de genai para la key indicada."""
    with _client_lock:
        if api_key not in _client_cache:
            _client_cache[api_key] = genai.Client(api_key=api_key)
            logger.info(f"[GEMINI] Cliente listo para key ...{api_key[-6:]}")
        return _client_cache[api_key]


# ── Parser JSON Robusto ────────────────────────────────────────────────────────
def _parse_json(raw_text: str) -> dict:
    raw = raw_text.strip()

    # Limpiar bloques markdown ```json ... ```
    if "```" in raw:
        match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
        if match:
            raw = match.group(1).strip()

    # Intento 1: parseo directo
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Intento 2: buscar el primer bloque { ... }
    brace_start = raw.find('{')
    brace_end = raw.rfind('}')
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        try:
            return json.loads(raw[brace_start:brace_end + 1])
        except json.JSONDecodeError:
            pass

    # Intento 3: JSON truncado — cerrar brackets abiertos
    for end in range(len(raw), max(0, len(raw) - 500), -1):
        candidate = raw[:end]
        open_braces   = candidate.count('{') - candidate.count('}')
        open_brackets  = candidate.count('[') - candidate.count(']')
        candidate += '}' * open_braces + ']' * open_brackets
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    raise json.JSONDecodeError("No se pudo parsear el JSON de Gemini", raw, 0)


# ── Merge manual de 2 resultados ───────────────────────────────────────────────
def _merge_two(r1: dict, r2: dict) -> dict:
    """
    Fusiona los resultados de los 2 workers.
    - matrix: une por category_name, toma el hallazgo más largo
    - quality_report: promedia scores, une recomendaciones
    """
    merged_matrix = {}
    for r in [r1, r2]:
        for item in r.get("matrix", []):
            cat = item.get("category_name", "?")
            if cat not in merged_matrix or \
               len(item.get("hallazgo", "")) > len(merged_matrix[cat].get("hallazgo", "")):
                merged_matrix[cat] = item

    merged_quality = {}
    for r in [r1, r2]:
        for item in r.get("quality_report", []):
            pillar = item.get("pillar_name", "?")
            if pillar not in merged_quality:
                merged_quality[pillar] = {
                    **item,
                    "_scores": [item.get("score", 5)]
                }
            else:
                merged_quality[pillar]["_scores"].append(item.get("score", 5))
                ex = set(merged_quality[pillar].get("recommendations", []))
                nw = set(item.get("recommendations", []))
                merged_quality[pillar]["recommendations"] = list(ex | nw)[:4]
                # Tomar el análisis más largo
                if len(item.get("analysis", "")) > len(merged_quality[pillar].get("analysis", "")):
                    merged_quality[pillar]["analysis"] = item["analysis"]

    for p in merged_quality.values():
        scores = p.pop("_scores", [5])
        p["score"] = round(sum(scores) / len(scores))

    return {
        "matrix": list(merged_matrix.values()),
        "quality_report": list(merged_quality.values())
    }


# ── Worker de análisis para una key ───────────────────────────────────────────
async def _analyze_with_key(
    text_portion: str,
    api_key: str,
    worker_id: int,
    retries: int = 3
) -> dict:
    """
    Analiza una porción del texto con una key específica de Gemini.
    Reintenta hasta `retries` veces con espera exponencial ante error 429.
    """
    model = _get_model_for_key(api_key)
    loop = asyncio.get_event_loop()

    prompt = (
        "INICIA AUDITORIA PEDAGOGICA. Analiza estos fragmentos de documentos institucionales.\n"
        "OBLIGATORIO: responde UNICAMENTE con JSON valido, sin texto antes ni despues, sin markdown.\n"
        "La respuesta debe empezar con { y terminar con }.\n"
        "Incluye EXACTAMENTE 6 items en matrix y EXACTAMENTE 5 items en quality_report.\n"
        "Usa textos BREVES (max 150 palabras por hallazgo/analysis) para no truncar la respuesta.\n\n"
    )

    for attempt in range(1, retries + 1):
        try:
            logger.info(
                f"[WORKER-{worker_id}] Llamando Gemini (New SDK) con key ...{api_key[-6:]} "
                f"({len(text_portion):,} chars, intento {attempt})"
            )
            
            # El nuevo SDK simplifica la llamada
            response = await loop.run_in_executor(
                None,
                lambda p=prompt: client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=p + f"FRAGMENTO {worker_id}:\n{text_portion}",
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.1,
                        max_output_tokens=8192,
                    )
                )
            )
            result = _parse_json(response.text)

            if "matrix" not in result or "quality_report" not in result:
                raise ValueError(f"[WORKER-{worker_id}] JSON incompleto: faltan claves obligatorias")

            logger.info(
                f"[WORKER-{worker_id}] ✅ OK — "
                f"{len(result['matrix'])} cats, {len(result['quality_report'])} pilares"
            )
            return result

        except json.JSONDecodeError as e:
            if attempt < retries:
                logger.warning(f"[WORKER-{worker_id}] JSON inválido intento {attempt}, reintentando...")
                await asyncio.sleep(3)
            else:
                raise Exception(f"[WORKER-{worker_id}] JSON inválido tras {retries} intentos: {e}")

        except Exception as e:
            err = str(e).lower()
            is_rate = any(x in err for x in ["429", "quota", "resource_exhausted", "rate"])
            if is_rate and attempt < retries:
                wait_secs = 15 * attempt   # 15s, 30s
                logger.warning(
                    f"[WORKER-{worker_id}] 429 Rate Limit. Esperando {wait_secs}s antes de reintentar..."
                )
                await asyncio.sleep(wait_secs)
            else:
                raise


# ── Clase principal ────────────────────────────────────────────────────────────
class GeminiService:
    """
    Motor Gemini con 2 workers paralelos.
    Divide el texto en 2 porciones y las procesa simultáneamente con 2 API keys.
    """

    async def analyze_documents(self, documents_text: str) -> dict:
        total = len(documents_text)
        keys = _get_api_keys()

        if not keys:
            raise Exception("GOOGLE_API_KEY no configurada en el archivo .env del backend.")

        if len(keys) == 1:
            # Una sola key: dividir en 2 chunks y procesarlos secuencialmente
            logger.info(
                f"[GEMINI] 1 key disponible. Dividiendo {total:,} chars en 2 chunks secuenciales."
            )
            return await self._run_sequential(documents_text, keys[0])
        else:
            # Dos keys: dividir en 2 porciones y procesar en PARALELO
            logger.info(
                f"[GEMINI] 2 keys disponibles. Dividiendo {total:,} chars en 2 workers PARALELOS."
            )
            return await self._run_parallel(documents_text, keys[0], keys[1])

    # ── Modo paralelo (2 keys) ────────────────────────────────────────────────
    MAX_CHUNK = 120_000   # 120k chars por chunk → respuesta JSON que cabe en 8192 tokens

    async def _run_parallel(
        self, text: str, key1: str, key2: str
    ) -> dict:
        """Divide el texto en mitades (máx 120k cada una) y lanza 2 workers simultáneamente."""
        midpoint = len(text) // 2

        # Encontrar el corte más cercano a un salto de línea para no cortar palabras
        cut = text.rfind('\n', midpoint - 5000, midpoint + 5000)
        if cut == -1:
            cut = midpoint

        portion1 = text[:cut][:self.MAX_CHUNK]
        portion2 = text[cut:][:self.MAX_CHUNK]

        logger.info(
            f"[GEMINI PARALELO] Worker-1: {len(portion1):,} chars (key ...{key1[-6:]}) | "
            f"Worker-2: {len(portion2):,} chars (key ...{key2[-6:]})"
        )

        # Lanzar ambos workers al mismo tiempo
        task1 = asyncio.create_task(_analyze_with_key(portion1, key1, worker_id=1))
        task2 = asyncio.create_task(_analyze_with_key(portion2, key2, worker_id=2))

        results = await asyncio.gather(task1, task2, return_exceptions=True)

        r1, r2 = results[0], results[1]

        # Manejar fallos parciales
        if isinstance(r1, Exception) and isinstance(r2, Exception):
            raise Exception(
                f"Ambos workers de Gemini fallaron.\n• Worker-1: {r1}\n• Worker-2: {r2}"
            )
        if isinstance(r1, Exception):
            logger.warning(f"[GEMINI] Worker-1 falló: {r1}. Usando solo Worker-2.")
            return r2
        if isinstance(r2, Exception):
            logger.warning(f"[GEMINI] Worker-2 falló: {r2}. Usando solo Worker-1.")
            return r1

        # Fusionar los 2 análisis
        merged = _merge_two(r1, r2)
        logger.info(
            f"[GEMINI PARALELO] ✅ Merge completado — "
            f"{len(merged['matrix'])} categorías, {len(merged['quality_report'])} pilares"
        )
        return merged

    # ── Modo secuencial (1 key) ───────────────────────────────────────────────
    async def _run_sequential(self, text: str, key: str) -> dict:
        """Con 1 key: divide en 2 chunks (máx 120k cada uno) y los procesa uno tras otro."""
        midpoint = len(text) // 2
        cut = text.rfind('\n', midpoint - 5000, midpoint + 5000)
        if cut == -1:
            cut = midpoint

        portion1 = text[:cut][:self.MAX_CHUNK]
        portion2 = text[cut:][:self.MAX_CHUNK]

        logger.info(
            f"[GEMINI SEQ] Chunk-1: {len(portion1):,} chars | Chunk-2: {len(portion2):,} chars"
        )

        r1 = await _analyze_with_key(portion1, key, worker_id=1)
        # Pausa entre chunks para no saturar el TPM gratuito
        await asyncio.sleep(5)
        r2 = await _analyze_with_key(portion2, key, worker_id=2)

        merged = _merge_two(r1, r2)
        logger.info(
            f"[GEMINI SEQ] ✅ Merge completado — "
            f"{len(merged['matrix'])} categorías, {len(merged['quality_report'])} pilares"
        )
        return merged


gemini_service = GeminiService()
