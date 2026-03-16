from groq import Groq
import os
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Eres un AUDITOR PEDAGÓGICO SENIOR del Ministerio de Educación de Colombia.
Tu misión: analizar documentos institucionales y devolver un JSON estructurado con EXACTAMENTE el formato indicado.

REGLAS ABSOLUTAS:
1. Responde ÚNICAMENTE con JSON válido, sin texto adicional.
2. La clave "matrix" debe tener EXACTAMENTE 6 objetos, uno por cada categoría listada.
3. La clave "quality_report" debe tener EXACTAMENTE 5 objetos, uno por cada pilar listado.
4. Si no encuentras evidencia, escribe "No detectado en los documentos analizados" pero NUNCA omitas la categoría/pilar.
5. Cita siempre el documento fuente y la página aproximada.

ESTRUCTURA JSON OBLIGATORIA:
{
  "matrix": [
    {
      "category_name": "Contexto Territorial",
      "hallazgo": "descripcion del hallazgo principal",
      "evidencia": {"text": "cita textual del documento", "document_name": "nombre del doc", "page": 1},
      "interpretacion": "analisis pedagogico del hallazgo",
      "implicacion_pfi": "como impacta al Plan de Formacion Integral"
    },
    {
      "category_name": "Intereses Estudiantiles",
      "hallazgo": "...", "evidencia": {"text": "...", "document_name": "...", "page": 1},
      "interpretacion": "...", "implicacion_pfi": "..."
    },
    {
      "category_name": "Fortalezas Institucionales",
      "hallazgo": "...", "evidencia": {"text": "...", "document_name": "...", "page": 1},
      "interpretacion": "...", "implicacion_pfi": "..."
    },
    {
      "category_name": "Problematicas Educativas",
      "hallazgo": "...", "evidencia": {"text": "...", "document_name": "...", "page": 1},
      "interpretacion": "...", "implicacion_pfi": "..."
    },
    {
      "category_name": "Cultura y Saberes Locales",
      "hallazgo": "...", "evidencia": {"text": "...", "document_name": "...", "page": 1},
      "interpretacion": "...", "implicacion_pfi": "..."
    },
    {
      "category_name": "Infraestructura",
      "hallazgo": "...", "evidencia": {"text": "...", "document_name": "...", "page": 1},
      "interpretacion": "...", "implicacion_pfi": "..."
    }
  ],
  "quality_report": [
    {
      "pillar_name": "Pertinencia Contextual",
      "score": 8,
      "analysis": "Analiza si la institución responde al territorio (Relación escuela-comunidad, Problemáticas, Intereses, Saberes locales).",
      "recommendations": ["recomendacion 1", "recomendacion 2"]
    },
    {
      "pillar_name": "Coherencia Institucional",
      "score": 7, 
      "analysis": "Analiza si los documentos (PEI, Proyectos, Centros de Interés) están articulados con la formación integral.", 
      "recommendations": ["...", "..."]
    },
    {
      "pillar_name": "Articulación Curricular",
      "score": 7, 
      "analysis": "Evidencia relación entre Áreas académicas, Centros de interés y Proyectos para superar fragmentación.", 
      "recommendations": ["...", "..."]
    },
    {
      "pillar_name": "Participación de la Comunidad",
      "score": 6, 
      "analysis": "Nivel de inclusión de estudiantes, docentes, directivos y familias en el diagnóstico.", 
      "recommendations": ["...", "..."]
    },
    {
      "pillar_name": "Condiciones para implementar PFI",
      "score": 7, 
      "analysis": "Disponibilidad de liderazgo, tiempos en horario, recursos pedagógicos y compromiso docente.", 
      "recommendations": ["...", "..."]
    }
  ]
}"""


class GroqService:
    def __init__(self):
        # NO crear el cliente aquí - se crea lazy (cuando se necesita)
        # Esto evita el error en Vercel donde las env vars cargan después de los imports
        self._client = None
        self.model = "llama-3.3-70b-versatile"

    @property
    def client(self):
        """Lazy initialization: crea el cliente solo cuando se necesita."""
        if self._client is None:
            api_key = settings.GROQ_API_KEY
            if not api_key:
                raise Exception("GROQ_API_KEY no está configurada. Agrégala en Vercel → Settings → Environment Variables.")
            self._client = Groq(api_key=api_key)
            logger.info("Cliente Groq inicializado correctamente.")
        return self._client

    async def analyze_documents(self, documents_text: str):
        """
        Analiza documentos usando Groq (Llama 3.3-70b).
        Limite: 128k tokens. Usamos los primeros 80k chars (~20k tokens) de forma segura.
        Para textos muy grandes, el orquestador deberia usar Gemini con chunking.
        """
        GROQ_CHAR_LIMIT = 30_000

        if len(documents_text) > GROQ_CHAR_LIMIT:
            logger.warning(
                f"[GROQ] Texto truncado: {len(documents_text):,} chars -> {GROQ_CHAR_LIMIT:,} chars. "
                f"Para analisis completo de documentos grandes, usar Gemini."
            )
        truncated_text = documents_text[:GROQ_CHAR_LIMIT]

        user_prompt = (
            "INICIA AUDITORÍA PEDAGÓGICA. Analiza los siguientes documentos institucionales y genera "
            "la matriz de 6 categorías y el reporte de 5 pilares de calidad según el formato indicado.\n\n"
            f"DOCUMENTOS:\n{truncated_text}"
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=4096,
                response_format={"type": "json_object"},
            )
            raw = completion.choices[0].message.content
            result = json.loads(raw)

            if "matrix" not in result or "quality_report" not in result:
                raise ValueError(f"Respuesta JSON incompleta: faltan claves. Keys: {list(result.keys())}")

            logger.info(
                f"[GROQ OK] {len(result['matrix'])} categorias, "
                f"{len(result['quality_report'])} pilares"
            )
            return result

        except json.JSONDecodeError as e:
            logger.error(f"[GROQ] JSON invalido: {e}")
            raise Exception(f"El motor Groq devolvio una respuesta con formato invalido: {e}")
        except Exception as e:
            logger.error(f"[GROQ] Error: {str(e)}")
            raise e


groq_service = GroqService()

