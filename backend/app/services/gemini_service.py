"""
GeminiService — Motor Principal de Análisis Pedagógico
=======================================================
Usa Google Gemini 1.5 Pro (contexto 1M tokens) para analizar
documentos institucionales grandes sin necesidad de truncar.

Arquitectura:
  - Gemini = Principal (documentos grandes, contexto completo)
  - Groq   = Soporte / Fallback (documentos pequeños o si Gemini falla)
"""

import os
import json
import logging
import google.generativeai as genai
from app.services.groq_service import SYSTEM_PROMPT  # Reutilizamos el mismo prompt

logger = logging.getLogger(__name__)

# ─── Umbral para decidir qué motor usar ───────────────────────────────────────
# Si el texto tiene menos de 40.000 caracteres (~10k tokens) → Groq (más rápido)
# Si supera ese umbral → Gemini (más contexto)
GROQ_THRESHOLD_CHARS = 40_000

# ─── Modelo Gemini ─────────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.5-flash"


class GeminiService:
    """Motor de análisis basado en Gemini 1.5 Pro con soporte de 1M tokens."""

    def __init__(self):
        self._model = None

    @property
    def model(self):
        """Lazy init: crea el modelo solo cuando se necesita."""
        if self._model is None:
            api_key = os.environ.get("GOOGLE_API_KEY", "")
            if not api_key:
                raise Exception(
                    "GOOGLE_API_KEY no está configurada. "
                    "Agrégala en el archivo .env o en Vercel → Settings → Environment Variables."
                )
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=8192,
                    response_mime_type="application/json",  # Fuerza respuesta JSON
                ),
                system_instruction=SYSTEM_PROMPT,
            )
            logger.info(f"Modelo Gemini inicializado: {GEMINI_MODEL}")
        return self._model

    async def analyze_documents(self, documents_text: str) -> dict:
        """
        Analiza documentos con Gemini 1.5 Pro.
        Soporta contexto completo sin truncar (hasta ~750k tokens de texto).
        """
        user_prompt = (
            "INICIA AUDITORÍA PEDAGÓGICA. Analiza los siguientes documentos institucionales "
            "y genera la matriz de 6 categorías y el reporte de 5 pilares de calidad "
            "según el formato indicado.\n\n"
            f"DOCUMENTOS:\n{documents_text}"
        )

        logger.info(
            f"[GEMINI] Enviando {len(documents_text):,} chars "
            f"(~{len(documents_text)//4:,} tokens estimados)"
        )

        try:
            # Gemini SDK es síncrono — llamamos directamente
            response = self.model.generate_content(user_prompt)
            raw_text = response.text.strip()

            # Limpiar posibles bloques markdown que Gemini a veces añade
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]

            result = json.loads(raw_text)

            # Validar estructura mínima
            if "matrix" not in result or "quality_report" not in result:
                raise ValueError(
                    f"Respuesta JSON incompleta de Gemini. Keys: {list(result.keys())}"
                )

            logger.info(
                f"[GEMINI OK] {len(result['matrix'])} categorías, "
                f"{len(result['quality_report'])} pilares"
            )
            return result

        except json.JSONDecodeError as e:
            logger.error(f"[GEMINI] JSON inválido: {e}")
            raise Exception(f"Gemini devolvió formato inválido: {e}")
        except Exception as e:
            logger.error(f"[GEMINI] Error: {str(e)}")
            raise


gemini_service = GeminiService()
