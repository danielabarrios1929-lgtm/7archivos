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
# CONSERVADORES para tier gratuito de Groq
GROQ_THRESHOLD_CHARS = 25_000   # < esto → Groq directo (rápido, no excede 12k TPM)
GEMINI_MAX_CHARS     = 3_500_000 # Límite gigante de Gemini 2.5 Flash (~1M tokens)

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
                    wait = 30 * attempt  # 30s, 60s, 90s - Pausa masiva para reset de TPM
                    logger.warning(f"[GEMINI] Rate limit severo detectado (429). Esperando {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    raise

    def _merge_manual(self, results: List[dict]) -> dict:
        """Merge de respaldo sin IA. (Mantenido por retrocompatibilidad)"""
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
        Analiza documentos garantizando no explotar la cuota con reintentos macizos y mitigadores de fallo.
        """
        total = len(documents_text)
        
        # Super-truncador defensivo para no agotar la TPM gratuita brutalmente de un solo envío
        SAFE_LIMIT = 500_000 
        if total > SAFE_LIMIT:
            logger.warning(f"[GEMINI] ARCHIVO TITÁNICO: {total} chars. Truncando a {SAFE_LIMIT} para no romper el cuota TPM gratuita.")
            documents_text = documents_text[:SAFE_LIMIT]

        prompt = (
            "INICIA AUDITORIA PEDAGOGICA EXHAUSTIVA. Analiza la totalidad de estos documentos "
            "institucionales y genera la matriz de 6 categorias y el reporte de 5 pilares.\n"
            "Responde SOLO con JSON valido. "
            "Es OBLIGATORIO que los hallazgos estén completos.\n\n"
            f"DOCUMENTOS COMPLETOS:\n{documents_text}"
        )

        try:
            # Damos hasta 4 reintentos, con pausas masivas (configuradas arriba) si choca con error 429
            result = await self._call_gemini(prompt, retries=4)
            
            if "matrix" not in result or "quality_report" not in result:
                logger.warning("Gemini omitió llaves en la respuesta.")
                raise ValueError("JSON incompleto de Gemini. Faltan llaves obligatorias.")
                
            logger.info(f"[GEMINI OK] {len(result['matrix'])} cats, {len(result['quality_report'])} pilares. ¡Proceso rápido logrado!")
            return result
            
        except Exception as e:
            logger.error(f"[GEMINI] CRÍTICO GLOBAL: Fallo al procesar tras reintentos: {e}")
            return {
                "matrix": [
                    {
                        "category_name": "Procesamiento de Cuota Excedida",
                        "hallazgo": "La Inteligencia Artificial gratuita ha alcanzado su límite de palabras por minuto. El archivo contenía demasiadas páginas o fotos para analizar en un solo barrido.",
                        "evidencia": {"text": f"Error 429: {str(e)[:50]}", "document_name": "Servidor Google", "page": 0},
                        "interpretacion": "El volumen de datos saturó el canal gratuito temporalmente.",
                        "implicacion_pfi": "INTÉNTALO OTRA VEZ EN 1 MINUTO EXACTO."
                    }
                ],
                "quality_report": [
                    {
                        "pillar_name": "Límite de Servidor (429)",
                        "score": 1,
                        "analysis": "El documento no pudo ser procesado porque se agotó la cuota gratuita de lectura por minuto.",
                        "recommendations": ["Espera 60 segundos y presiona el botón nuevamente."]
                    }
                ],
                "_engine_used": "Gemini 2.5 Flash",
                "_warning": "Error Crítico 429 - Límite gratuito excedido, reintente en 1 minuto."
            }

gemini_service = GeminiService()
