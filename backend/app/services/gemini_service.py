"""
GeminiService v3 — Chunking Robusto y Estable
==============================================
Fixes v3:
  - Chunks mucho mas pequenos (80k chars) para evitar JSON truncado
  - Eliminado response_mime_type (no soportado en gemini-2.5-flash)
  - Sintesis liviana: solo envia resumen reducido a Groq (no JSON completo)
  - Retry mas agresivo con mayor espera entre intentos
"""

import os
import json
import asyncio
import logging
import re
from typing import List
import google.generativeai as genai
from app.services.groq_service import SYSTEM_PROMPT, groq_service

logger = logging.getLogger(__name__)

# ── Umbrales ───────────────────────────────────────────────────────────────────
# CONSERVADORES para tier gratuito de Gemini
GROQ_THRESHOLD_CHARS = 25_000   # < esto → Groq directo (rapido)
GEMINI_MAX_CHARS     = 65_000   # Limite seguro peticion unica (~16k tokens)
GEMINI_CHUNK_SIZE    = 60_000   # Tamano de cada chunk (~15k tokens, margen seguro)

# ── Modelo ─────────────────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.5-flash"

# ── Prompt de Sintesis Liviano ──────────────────────────────────────────────────
SYNTHESIS_SYSTEM_PROMPT = """Eres un SINTETIZADOR DE AUDITORIAS PEDAGOGICAS.
Recibes multiples analisis parciales de fragmentos de documentos y debes
fusionarlos en UN UNICO resultado JSON cohesivo.

REGLAS:
1. Responde UNICAMENTE con JSON valido, SIN texto adicional, SIN markdown.
2. matrix: EXACTAMENTE 6 objetos (uno por categoria).
3. quality_report: EXACTAMENTE 5 objetos (uno por pilar).
4. Combina hallazgos de todos los fragmentos, eliminando redundancias.
5. Para scores: calcula el promedio de todos los fragmentos.

Formato de salida:
{"matrix": [...6 items...], "quality_report": [...5 items...]}"""


class GeminiService:
    """Motor Gemini 2.5 Flash con chunking robusto y procesamiento paralelo."""

    def __init__(self):
        self._model = None

    @property
    def model(self):
        if self._model is None:
            api_key = os.environ.get("GOOGLE_API_KEY", "")
            if not api_key:
                raise Exception("GOOGLE_API_KEY no configurada.")
            genai.configure(api_key=api_key)
            # SIN response_mime_type — no soportado en gemini-2.5-flash
            self._model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=4096,
                ),
                system_instruction=SYSTEM_PROMPT,
            )
            logger.info(f"[GEMINI] Modelo listo: {GEMINI_MODEL}")
        return self._model

    # ── Parser JSON Robusto ─────────────────────────────────────────────────────

    def _parse_json(self, raw_text: str) -> dict:
        """
        Parsea JSON de forma robusta:
        1. Intenta parseo directo
        2. Si falla, busca el bloque JSON dentro del texto
        3. Si falla, intenta reparar JSON truncado
        """
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

        # Intento 2: buscar el primer bloque { ... } del texto
        brace_start = raw.find('{')
        brace_end = raw.rfind('}')
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            try:
                return json.loads(raw[brace_start:brace_end + 1])
            except json.JSONDecodeError:
                pass

        # Intento 3: JSON truncado — intentar encontrar el ultimo objeto completo
        # Buscar hasta donde el JSON es valido
        for end in range(len(raw), 0, -1):
            candidate = raw[:end]
            # Cerrar brackets abiertos
            open_braces = candidate.count('{') - candidate.count('}')
            open_brackets = candidate.count('[') - candidate.count(']')
            candidate += '}' * open_braces + ']' * open_brackets
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

        raise json.JSONDecodeError("No se pudo parsear el JSON de Gemini", raw, 0)

    # ── Llamada a Gemini con retry ──────────────────────────────────────────────

    async def _call_gemini(self, prompt: str, retries: int = 3) -> dict:
        """Llama a Gemini async con retry exponencial."""
        loop = asyncio.get_event_loop()

        for attempt in range(1, retries + 1):
            try:
                response = await loop.run_in_executor(
                    None,
                    lambda p=prompt: self.model.generate_content(p)
                )
                result = self._parse_json(response.text)
                return result

            except json.JSONDecodeError as e:
                if attempt < retries:
                    logger.warning(f"[GEMINI] JSON invalido (intento {attempt}), reintentando...")
                    await asyncio.sleep(2)
                else:
                    raise Exception(f"Gemini devolvio JSON invalido tras {retries} intentos: {e}")

            except Exception as e:
                error_str = str(e).lower()
                is_rate_limit = any(x in error_str for x in ["429", "quota", "resource_exhausted", "rate"])
                if is_rate_limit and attempt < retries:
                    wait = 15 * attempt  # 15s, 30s, 45s (Rate limit de Gemini requiere mucho tiempo)
                    logger.warning(f"[GEMINI] Rate limit detectado (intento {attempt}). Esperando {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    raise

    # ── Division inteligente del texto ─────────────────────────────────────────

    def _split_into_chunks(self, text: str) -> List[str]:
        """
        Divide el texto en chunks de GEMINI_CHUNK_SIZE caracteres,
        intentando cortar en saltos de parrafo para no partir frases.
        """
        chunks = []
        start = 0
        total = len(text)

        while start < total:
            end = min(start + GEMINI_CHUNK_SIZE, total)

            # Si no llegamos al final, intentar cortar en un parrafo
            if end < total:
                # Buscar ultimo "\n\n" dentro del chunk para cortar limpiamente
                cut = text.rfind('\n\n', start, end)
                if cut > start + GEMINI_CHUNK_SIZE // 2:
                    end = cut

            chunks.append(text[start:end])
            start = end

        return chunks

    # ── Sintesis Liviana ────────────────────────────────────────────────────────

    async def _synthesize(self, results: List[dict]) -> dict:
        """
        Fusiona N resultados parciales.
        Envia solo los campos esenciales a Groq para mantener el payload pequeno.
        """
        if len(results) == 1:
            return results[0]

        # Extraer solo los campos clave para reducir el payload a Groq
        compact_results = []
        for i, r in enumerate(results):
            compact = {
                "fragmento": i + 1,
                "matrix": [
                    {
                        "category_name": item.get("category_name"),
                        "hallazgo": item.get("hallazgo", "")[:300],  # Max 300 chars por hallazgo
                        "interpretacion": item.get("interpretacion", "")[:200],
                        "implicacion_pfi": item.get("implicacion_pfi", "")[:200],
                        "evidencia": item.get("evidencia", {}),
                    }
                    for item in r.get("matrix", [])
                ],
                "quality_report": [
                    {
                        "pillar_name": item.get("pillar_name"),
                        "score": item.get("score", 5),
                        "analysis": item.get("analysis", "")[:300],
                        "recommendations": item.get("recommendations", [])[:3],
                    }
                    for item in r.get("quality_report", [])
                ]
            }
            compact_results.append(compact)

        synthesis_text = json.dumps(compact_results, ensure_ascii=False)

        # Si aun es muy grande, usar merge manual
        if len(synthesis_text) > 20_000:
            logger.warning("[SINTESIS] Payload demasiado grande para Groq, usando merge manual.")
            return self._merge_manual(results)

        prompt = (
            f"Fusiona estos {len(results)} analisis parciales en un unico JSON:\n\n"
            f"{synthesis_text}"
        )

        logger.info(f"[SINTESIS] Enviando {len(synthesis_text):,} chars a Groq para fusionar...")

        loop = asyncio.get_event_loop()
        try:
            completion = await loop.run_in_executor(
                None,
                lambda: groq_service.client.chat.completions.create(
                    model=groq_service.model,
                    messages=[
                        {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.05,
                    max_tokens=4096,
                    response_format={"type": "json_object"},
                )
            )
            return json.loads(completion.choices[0].message.content)
        except Exception as e:
            logger.warning(f"[SINTESIS] Groq fallo ({e}). Usando merge manual.")
            return self._merge_manual(results)

    def _merge_manual(self, results: List[dict]) -> dict:
        """Merge de respaldo sin IA."""
        merged_matrix = {}
        for r in results:
            for item in r.get("matrix", []):
                cat = item.get("category_name", "?")
                if cat not in merged_matrix or len(item.get("hallazgo", "")) > len(merged_matrix[cat].get("hallazgo", "")):
                    merged_matrix[cat] = item

        merged_quality = {}
        for r in results:
            for item in r.get("quality_report", []):
                pillar = item.get("pillar_name", "?")
                if pillar not in merged_quality:
                    merged_quality[pillar] = {**item, "_scores": [item.get("score", 5)]}
                else:
                    merged_quality[pillar]["_scores"].append(item.get("score", 5))
                    ex = set(merged_quality[pillar].get("recommendations", []))
                    nw = set(item.get("recommendations", []))
                    merged_quality[pillar]["recommendations"] = list(ex | nw)[:4]

        for p in merged_quality.values():
            scores = p.pop("_scores", [5])
            p["score"] = round(sum(scores) / len(scores))

        return {
            "matrix": list(merged_matrix.values()),
            "quality_report": list(merged_quality.values())
        }

    # ── Metodo Principal ────────────────────────────────────────────────────────

    async def analyze_documents(self, documents_text: str) -> dict:
        """
        Analiza documentos con chunking robusto y paralelo.
        Chunks de 70k chars para garantizar respuesta JSON completa.
        """
        total = len(documents_text)
        logger.info(f"[GEMINI] Texto: {total:,} chars (~{total//4:,} tokens)")

        # ── Peticion unica ─────────────────────────────────────────────────────
        if total <= GEMINI_MAX_CHARS:
            logger.info("[GEMINI] Modo UNICO")
            prompt = (
                "INICIA AUDITORIA PEDAGOGICA. Analiza los documentos y genera "
                "la matriz de 6 categorias y 5 pilares. "
                "Responde SOLO con JSON valido, sin texto adicional.\n\n"
                f"DOCUMENTOS:\n{documents_text}"
            )
            result = await self._call_gemini(prompt)
            if "matrix" not in result or "quality_report" not in result:
                raise ValueError("JSON incompleto de Gemini.")
            logger.info(f"[GEMINI OK] {len(result['matrix'])} cats, {len(result['quality_report'])} pilares")
            return result

        # ── Chunking paralelo ──────────────────────────────────────────────────
        chunks = self._split_into_chunks(documents_text)
        n = len(chunks)
        logger.info(f"[GEMINI] Modo PARALELO: {n} chunks de ~{GEMINI_CHUNK_SIZE:,} chars c/u")

        async def process_chunk(idx: int, chunk: str):
            prompt = (
                f"AUDITORIA PEDAGOGICA — PARTE {idx+1} DE {n}.\n"
                "Analiza este fragmento. Responde SOLO con JSON valido, sin texto adicional.\n"
                "Si no hay evidencia de una categoria, usa 'No detectado en este fragmento'.\n\n"
                f"FRAGMENTO {idx+1}:\n{chunk}"
            )
            try:
                r = await self._call_gemini(prompt, retries=3)
                if "matrix" not in r or "quality_report" not in r:
                    logger.warning(f"[GEMINI] Chunk {idx+1} JSON incompleto.")
                    return None
                logger.info(f"[GEMINI] Chunk {idx+1}/{n} OK")
                return r
            except Exception as e:
                logger.warning(f"[GEMINI] Chunk {idx+1} fallo crítico: {e}")
                return None

        # Procesamiento SECUENCIAL CONTROLADO (para no reventar Gemini Free Tier - 15 RPM)
        # en vez de asyncio.gather (paralelo) que satura la cuota gratuita de inmediato
        logger.info(f"[GEMINI] Iniciando escaneo profundo secuencial de {n} partes. Esto tomará un momento...")
        raw = []
        for i, c in enumerate(chunks):
            r = await process_chunk(i, c)
            raw.append(r)
            if i < len(chunks) - 1:
                # Retardo protector de 5s entre peticiones = max ~12 req/minuto (debajo de 15)
                logger.info(f"[GEMINI] Pausa de protección de cuota (5s)...")
                await asyncio.sleep(5)
        
        good = [r for r in raw if r is not None]

        if not good:
            raise Exception(
                f"Gemini no pudo procesar ningun fragmento ({n} intentos). "
                "El archivo puede estar protegido, escaneado sin OCR, o ser demasiado grande."
            )

        logger.info(f"[GEMINI] {len(good)}/{n} fragmentos OK. Sintetizando...")
        final = await self._synthesize(good)
        logger.info(
            f"[GEMINI OK TOTAL] {len(final.get('matrix',[]))} cats, "
            f"{len(final.get('quality_report',[]))} pilares"
        )
        return final


gemini_service = GeminiService()
