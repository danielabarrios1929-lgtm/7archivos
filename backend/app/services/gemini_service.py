"""
GeminiService v2 — Motor Principal con Chunking Inteligente
============================================================
Mejoras sobre v1:
  1. Chunking POR DOCUMENTO: cada doc se analiza en su propio contexto
     → la IA no pierde el hilo entre documentos
  2. Procesamiento PARALELO: todos los chunks se envian a la vez (asyncio)
     → tiempo total = tiempo del chunk mas lento, no la suma
  3. Sintesis final con IA: Groq (rapido) fusiona los hallazgos de todos
     los chunks en un resultado cohesivo y sin redundancias
  4. Retry automatico con backoff para errores de rate-limit
"""

import os
import json
import asyncio
import logging
from typing import List, Dict
import google.generativeai as genai
from app.services.groq_service import SYSTEM_PROMPT, groq_service

logger = logging.getLogger(__name__)

# ── Umbrales ───────────────────────────────────────────────────────────────────
GROQ_THRESHOLD_CHARS = 40_000   # < esto → Groq directo (rapido)
GEMINI_MAX_CHARS     = 500_000  # Limite seguro por peticion unica (~125k tokens)
GEMINI_CHUNK_SIZE    = 460_000  # Tamaño de chunk con margen de seguridad

# ── Modelo ─────────────────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.5-flash"

# ── Prompt de Sintesis (para fusionar resultados de chunks con Groq) ───────────
SYNTHESIS_SYSTEM_PROMPT = """Eres un SINTETIZADOR DE AUDITORIAS PEDAGOGICAS.
Recibes multiples analisis parciales de diferentes fragmentos de documentos institucionales
y debes fusionarlos en un UNICO resultado cohesivo y completo.

REGLAS:
1. Responde UNICAMENTE con JSON valido, sin texto adicional.
2. Para cada categoria de la matrix, selecciona y COMBINA los hallazgos mas relevantes de cada fragmento.
3. Para cada pilar de calidad, PROMEDIA los scores y COMBINA las recomendaciones, eliminando duplicados.
4. El resultado debe tener EXACTAMENTE 6 categorias en matrix y EXACTAMENTE 5 pilares en quality_report.
5. Cita siempre el documento fuente original en evidencia.

Devuelve el mismo formato JSON que los analisis parciales:
{"matrix": [...], "quality_report": [...]}"""


class GeminiService:
    """Motor de analisis Gemini 2.5 Flash con chunking por documento y paralelismo."""

    def __init__(self):
        self._model = None

    @property
    def model(self):
        if self._model is None:
            api_key = os.environ.get("GOOGLE_API_KEY", "")
            if not api_key:
                raise Exception(
                    "GOOGLE_API_KEY no esta configurada. "
                    "Agregala en .env o en Vercel → Settings → Environment Variables."
                )
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=8192,
                    response_mime_type="application/json",
                ),
                system_instruction=SYSTEM_PROMPT,
            )
            logger.info(f"[GEMINI] Modelo listo: {GEMINI_MODEL}")
        return self._model

    # ── Llamada a Gemini con retry ──────────────────────────────────────────────

    def _parse_json_response(self, raw_text: str) -> dict:
        """Parsea JSON robusto desde respuesta de Gemini."""
        raw_text = raw_text.strip()
        # Limpiar bloques markdown
        if raw_text.startswith("```"):
            parts = raw_text.split("```")
            raw_text = parts[1] if len(parts) > 1 else raw_text
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        return json.loads(raw_text.strip())

    async def _call_gemini_async(self, prompt: str, retries: int = 3) -> dict:
        """
        Llama a Gemini de forma asincrona usando executor para no bloquear el event loop.
        Incluye retry automatico con backoff exponencial para errores 429 / 503.
        """
        loop = asyncio.get_event_loop()

        for attempt in range(1, retries + 1):
            try:
                # Ejecutar el SDK sincrono en un thread separado
                response = await loop.run_in_executor(
                    None,
                    lambda: self.model.generate_content(prompt)
                )
                return self._parse_json_response(response.text)

            except json.JSONDecodeError as e:
                raise Exception(f"Gemini devolvio JSON invalido: {e}")
            except Exception as e:
                error_str = str(e).lower()
                is_rate_limit = "429" in error_str or "quota" in error_str or "resource_exhausted" in error_str
                if is_rate_limit and attempt < retries:
                    wait_seconds = 2 ** attempt  # 2s, 4s, 8s
                    logger.warning(
                        f"[GEMINI] Rate limit (intento {attempt}/{retries}). "
                        f"Esperando {wait_seconds}s..."
                    )
                    await asyncio.sleep(wait_seconds)
                else:
                    raise

    # ── Chunking Inteligente ────────────────────────────────────────────────────

    def _build_doc_groups(self, documents_text: str) -> List[str]:
        """
        Divide el texto en grupos inteligentes:
        - Intenta mantener documentos completos juntos en un chunk
        - Si un documento es mas grande que GEMINI_CHUNK_SIZE, lo divide internamente
        """
        # Detectar separadores de documentos (los marcamos en processor.py)
        doc_separator = "=" * 60
        raw_docs = documents_text.split(doc_separator)

        # Reconstruir fragmentos de documentos con su separador
        doc_fragments = []
        for i in range(1, len(raw_docs), 2):  # Cada doc tiene: sep + contenido + sep
            fragment = doc_separator + raw_docs[i] + (doc_separator if i + 1 < len(raw_docs) else "")
            doc_fragments.append(fragment)

        # Si no pudimos separar bien (formato diferente), usar chunks de tamaño fijo
        if not doc_fragments:
            logger.info("[GEMINI] No se detectaron separadores de documentos. Usando chunks de tamano fijo.")
            return [
                documents_text[i: i + GEMINI_CHUNK_SIZE]
                for i in range(0, len(documents_text), GEMINI_CHUNK_SIZE)
            ]

        # Agrupar documentos en chunks que no superen GEMINI_CHUNK_SIZE
        groups = []
        current_group = ""
        for fragment in doc_fragments:
            fragment_size = len(fragment)
            # Si el fragmento solo ya es mas grande que el chunk → dividirlo
            if fragment_size > GEMINI_CHUNK_SIZE:
                if current_group:
                    groups.append(current_group)
                    current_group = ""
                for i in range(0, fragment_size, GEMINI_CHUNK_SIZE):
                    groups.append(fragment[i: i + GEMINI_CHUNK_SIZE])
            # Si agrego el fragmento se supera el chunk → cerrar grupo y empezar nuevo
            elif len(current_group) + fragment_size > GEMINI_CHUNK_SIZE:
                groups.append(current_group)
                current_group = fragment
            else:
                current_group += "\n" + fragment

        if current_group:
            groups.append(current_group)

        logger.info(
            f"[GEMINI] {len(doc_fragments)} documentos agrupados en {len(groups)} chunks."
        )
        return groups

    # ── Sintesis con IA (Groq rapido) ─────────────────────────────────────────

    async def _synthesize_with_ai(self, chunk_results: List[dict]) -> dict:
        """
        Usa Groq (rapido, 128k contexto) para sintetizar multiples analisis
        parciales en un resultado final cohesivo.
        """
        partial_analyses = json.dumps(chunk_results, ensure_ascii=False, indent=2)
        synthesis_prompt = (
            f"Tienes {len(chunk_results)} analisis parciales de fragmentos de documentos institucionales. "
            f"Fusionalos en un unico resultado JSON completo y sin redundancias:\n\n"
            f"ANALISIS PARCIALES:\n{partial_analyses}"
        )

        logger.info(f"[GEMINI] Sintetizando {len(chunk_results)} analisis con Groq...")

        # Inyectar temporalmente el system prompt de sintesis en Groq
        loop = asyncio.get_event_loop()
        try:
            completion = await loop.run_in_executor(
                None,
                lambda: groq_service.client.chat.completions.create(
                    model=groq_service.model,
                    messages=[
                        {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
                        {"role": "user", "content": synthesis_prompt},
                    ],
                    temperature=0.05,
                    max_tokens=4096,
                    response_format={"type": "json_object"},
                )
            )
            result = json.loads(completion.choices[0].message.content)
            logger.info("[GROQ SINTESIS OK] Resultado fusionado exitosamente.")
            return result
        except Exception as e:
            logger.warning(f"[GROQ SINTESIS] Error en sintesis: {e}. Usando merge manual.")
            return self._merge_manual(chunk_results)

    def _merge_manual(self, results: List[dict]) -> dict:
        """Merge de respaldo (sin IA) si la sintesis Groq falla."""
        if len(results) == 1:
            return results[0]

        merged_matrix = {}
        for result in results:
            for item in result.get("matrix", []):
                cat = item.get("category_name", "Desconocida")
                if cat not in merged_matrix or len(item.get("hallazgo", "")) > len(merged_matrix[cat].get("hallazgo", "")):
                    merged_matrix[cat] = item

        merged_quality = {}
        for result in results:
            for item in result.get("quality_report", []):
                pillar = item.get("pillar_name", "Desconocido")
                if pillar not in merged_quality:
                    merged_quality[pillar] = {**item, "_scores": [item.get("score", 5)]}
                else:
                    merged_quality[pillar]["_scores"].append(item.get("score", 5))
                    existing = set(merged_quality[pillar].get("recommendations", []))
                    new = set(item.get("recommendations", []))
                    merged_quality[pillar]["recommendations"] = list(existing | new)

        for p in merged_quality.values():
            scores = p.pop("_scores", [5])
            p["score"] = round(sum(scores) / len(scores))

        return {"matrix": list(merged_matrix.values()), "quality_report": list(merged_quality.values())}

    # ── Metodo Principal ────────────────────────────────────────────────────────

    async def analyze_documents(self, documents_text: str) -> dict:
        """
        Analiza documentos con Gemini 2.5 Flash.

        Flujo:
          1. Si cabe en una sola peticion → peticion directa
          2. Si no cabe → chunking inteligente por documento + paralelo
          3. Sintesis final con Groq para fusionar resultados
        """
        total_size = len(documents_text)
        logger.info(
            f"[GEMINI] Texto recibido: {total_size:,} chars "
            f"(~{total_size // 4:,} tokens est.)"
        )

        # ── Caso 1: Peticion unica (texto dentro del limite) ───────────────────
        if total_size <= GEMINI_MAX_CHARS:
            logger.info("[GEMINI] Modo: PETICION UNICA")
            prompt = (
                "INICIA AUDITORIA PEDAGOGICA. Analiza los siguientes documentos institucionales "
                "y genera la matriz de 6 categorias y el reporte de 5 pilares de calidad "
                "segun el formato indicado.\n\n"
                f"DOCUMENTOS:\n{documents_text}"
            )
            result = await self._call_gemini_async(prompt)
            if "matrix" not in result or "quality_report" not in result:
                raise ValueError(f"JSON incompleto de Gemini. Keys: {list(result.keys())}")
            logger.info(f"[GEMINI OK] {len(result['matrix'])} cats., {len(result['quality_report'])} pilares")
            return result

        # ── Caso 2: Chunking inteligente + paralelo ────────────────────────────
        groups = self._build_doc_groups(documents_text)
        n_groups = len(groups)
        logger.info(
            f"[GEMINI] Modo: CHUNKING PARALELO ({n_groups} grupos). "
            f"Enviando todos a la vez..."
        )

        async def process_chunk(idx: int, chunk: str) -> dict | None:
            prompt = (
                f"AUDITORIA PEDAGOGICA — FRAGMENTO {idx+1} DE {n_groups}.\n"
                "Analiza este fragmento de documentos institucionales segun el formato indicado. "
                "Si no encuentras evidencia de alguna categoria en este fragmento especifico, "
                "escribe 'No detectado en este fragmento'.\n\n"
                f"DOCUMENTOS (FRAGMENTO {idx+1}):\n{chunk}"
            )
            try:
                result = await self._call_gemini_async(prompt, retries=3)
                logger.info(f"[GEMINI] Fragmento {idx+1}/{n_groups} ✓")
                return result
            except Exception as e:
                logger.warning(f"[GEMINI] Fragmento {idx+1} fallo: {e}")
                return None

        # Ejecutar TODOS los chunks en paralelo
        tasks = [process_chunk(i, chunk) for i, chunk in enumerate(groups)]
        raw_results = await asyncio.gather(*tasks, return_exceptions=False)

        # Filtrar resultados exitosos
        chunk_results = [
            r for r in raw_results
            if r is not None
            and isinstance(r, dict)
            and "matrix" in r
            and "quality_report" in r
        ]

        if not chunk_results:
            raise Exception(
                "Gemini no pudo procesar ningun fragmento. "
                "Verifica que los archivos tengan texto legible y no esten protegidos."
            )

        logger.info(
            f"[GEMINI] {len(chunk_results)}/{n_groups} fragmentos exitosos. "
            f"Iniciando sintesis..."
        )

        # Sintesis final con IA (Groq) o merge manual de respaldo
        if len(chunk_results) == 1:
            final = chunk_results[0]
        else:
            final = await self._synthesize_with_ai(chunk_results)

        logger.info(
            f"[GEMINI OK - PARALELO] Sintesis completa: "
            f"{len(final.get('matrix', []))} categorias, "
            f"{len(final.get('quality_report', []))} pilares."
        )
        return final


gemini_service = GeminiService()
