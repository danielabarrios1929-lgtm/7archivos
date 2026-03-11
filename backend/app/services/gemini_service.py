"""
GeminiService — Motor Principal de Análisis Pedagógico
=======================================================
Usa Google Gemini 2.5 Flash para analizar documentos institucionales.
Implementa chunking automatico cuando el texto supera el limite de la API.

Arquitectura:
  - Texto <= 600k chars  -> Una peticion unica a Gemini
  - Texto  > 600k chars  -> Chunking: divide, analiza cada parte y fusiona
  - Groq = Soporte / Fallback si Gemini falla completamente
"""

import os
import json
import logging
import google.generativeai as genai
from app.services.groq_service import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# ── Umbrales ───────────────────────────────────────────────────────────────────
GROQ_THRESHOLD_CHARS = 40_000      # Menor a esto -> Groq directo (rapido)
GEMINI_MAX_CHARS     = 600_000     # Limite seguro para una peticion unica a Gemini (~150k tokens)
GEMINI_CHUNK_SIZE    = 550_000     # Tamaño de cada chunk con margen de seguridad

# ── Modelo ─────────────────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.5-flash"


class GeminiService:
    """Motor de analisis basado en Gemini 2.5 Flash con chunking automatico."""

    def __init__(self):
        self._model = None

    @property
    def model(self):
        """Lazy init: crea el modelo solo cuando se necesita."""
        if self._model is None:
            api_key = os.environ.get("GOOGLE_API_KEY", "")
            if not api_key:
                raise Exception(
                    "GOOGLE_API_KEY no esta configurada. "
                    "Agregala en el archivo .env o en Vercel -> Settings -> Environment Variables."
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
            logger.info(f"[GEMINI] Modelo inicializado: {GEMINI_MODEL}")
        return self._model

    def _call_gemini(self, prompt: str) -> dict:
        """Llama a Gemini y parsea el JSON de respuesta."""
        response = self.model.generate_content(prompt)
        raw_text = response.text.strip()

        # Limpiar bloques markdown que Gemini puede anadir
        if raw_text.startswith("```"):
            parts = raw_text.split("```")
            raw_text = parts[1] if len(parts) > 1 else raw_text
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]

        return json.loads(raw_text.strip())

    def _merge_results(self, results: list) -> dict:
        """
        Fusiona multiples resultados de chunks en un solo resultado final.
        - Matrix: selecciona el hallazgo mas completo por categoria.
        - Quality Report: promedia scores y une recomendaciones unicas.
        """
        if len(results) == 1:
            return results[0]

        logger.info(f"[GEMINI] Fusionando {len(results)} resultados de chunks...")

        # Fusionar Matrix
        merged_matrix = {}
        for result in results:
            for item in result.get("matrix", []):
                cat = item.get("category_name", "Desconocida")
                if cat not in merged_matrix:
                    merged_matrix[cat] = item
                else:
                    # Conservar el hallazgo mas informativo
                    if len(item.get("hallazgo", "")) > len(merged_matrix[cat].get("hallazgo", "")):
                        merged_matrix[cat] = item

        # Fusionar Quality Report
        merged_quality = {}
        for result in results:
            for item in result.get("quality_report", []):
                pillar = item.get("pillar_name", "Desconocido")
                if pillar not in merged_quality:
                    merged_quality[pillar] = {**item, "_scores": [item.get("score", 5)]}
                else:
                    merged_quality[pillar]["_scores"].append(item.get("score", 5))
                    # Combinar recomendaciones unicas
                    existing_recs = set(merged_quality[pillar].get("recommendations", []))
                    new_recs = set(item.get("recommendations", []))
                    merged_quality[pillar]["recommendations"] = list(existing_recs | new_recs)
                    # Conservar analisis mas detallado
                    if len(item.get("analysis", "")) > len(merged_quality[pillar].get("analysis", "")):
                        merged_quality[pillar]["analysis"] = item["analysis"]

        # Promedio de scores
        for pillar_data in merged_quality.values():
            scores = pillar_data.pop("_scores", [5])
            pillar_data["score"] = round(sum(scores) / len(scores))

        return {
            "matrix": list(merged_matrix.values()),
            "quality_report": list(merged_quality.values())
        }

    async def analyze_documents(self, documents_text: str) -> dict:
        """
        Analiza documentos con Gemini 2.5 Flash.
        Si el texto es muy grande, divide en chunks y fusiona los resultados.
        """
        total_size = len(documents_text)
        logger.info(
            f"[GEMINI] Texto recibido: {total_size:,} chars "
            f"(~{total_size // 4:,} tokens est.)"
        )

        # ── Peticion unica (texto dentro del limite) ───────────────────────────
        if total_size <= GEMINI_MAX_CHARS:
            logger.info("[GEMINI] Texto dentro del limite -> peticion unica")
            prompt = (
                "INICIA AUDITORIA PEDAGOGICA. Analiza los siguientes documentos institucionales "
                "y genera la matriz de 6 categorias y el reporte de 5 pilares de calidad "
                "segun el formato indicado.\n\n"
                f"DOCUMENTOS:\n{documents_text}"
            )
            try:
                result = self._call_gemini(prompt)
                if "matrix" not in result or "quality_report" not in result:
                    raise ValueError(f"JSON incompleto de Gemini. Keys: {list(result.keys())}")
                logger.info(
                    f"[GEMINI OK] {len(result['matrix'])} categorias, "
                    f"{len(result['quality_report'])} pilares"
                )
                return result
            except json.JSONDecodeError as e:
                raise Exception(f"Gemini devolvio formato invalido: {e}")

        # ── Chunking (texto demasiado grande) ──────────────────────────────────
        chunks = [
            documents_text[i: i + GEMINI_CHUNK_SIZE]
            for i in range(0, total_size, GEMINI_CHUNK_SIZE)
        ]
        n_chunks = len(chunks)
        logger.info(
            f"[GEMINI] Texto grande ({total_size:,} chars). "
            f"Dividiendo en {n_chunks} chunks de ~{GEMINI_CHUNK_SIZE:,} chars."
        )

        chunk_results = []
        for idx, chunk in enumerate(chunks, 1):
            logger.info(f"[GEMINI] Procesando chunk {idx}/{n_chunks} ({len(chunk):,} chars)...")
            prompt = (
                f"AUDITORIA PEDAGOGICA — PARTE {idx} DE {n_chunks}.\n"
                "Analiza este fragmento de documentos institucionales y genera la matriz "
                "de 6 categorias y el reporte de 5 pilares segun el formato indicado. "
                "Si no encuentras evidencia en este fragmento, escribe "
                "'No detectado en este fragmento'.\n\n"
                f"DOCUMENTOS (PARTE {idx}):\n{chunk}"
            )
            try:
                result = self._call_gemini(prompt)
                if "matrix" not in result or "quality_report" not in result:
                    logger.warning(f"[GEMINI] Chunk {idx} devolvio JSON incompleto, omitiendo.")
                    continue
                chunk_results.append(result)
                logger.info(f"[GEMINI] Chunk {idx}/{n_chunks} procesado OK.")
            except Exception as e:
                logger.warning(f"[GEMINI] Chunk {idx} fallo: {e}. Continuando...")

        if not chunk_results:
            raise Exception(
                "Gemini no pudo procesar ningun chunk del documento. "
                "Verifica que los archivos tengan texto extraible y no esten corruptos."
            )

        merged = self._merge_results(chunk_results)
        logger.info(
            f"[GEMINI OK - CHUNKED] {len(chunk_results)}/{n_chunks} chunks exitosos. "
            f"Resultado: {len(merged.get('matrix', []))} categorias, "
            f"{len(merged.get('quality_report', []))} pilares."
        )
        return merged


gemini_service = GeminiService()
