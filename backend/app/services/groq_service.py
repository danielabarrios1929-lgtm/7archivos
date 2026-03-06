from groq import Groq
from app.core.config import settings
import json
import logging

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
      "analysis": "analisis detallado del pilar",
      "recommendations": ["recomendacion 1", "recomendacion 2"]
    },
    {
      "pillar_name": "Coherencia Pedagogica",
      "score": 7, "analysis": "...", "recommendations": ["...", "..."]
    },
    {
      "pillar_name": "Articulacion Documental",
      "score": 7, "analysis": "...", "recommendations": ["...", "..."]
    },
    {
      "pillar_name": "Participacion Comunitaria",
      "score": 6, "analysis": "...", "recommendations": ["...", "..."]
    },
    {
      "pillar_name": "Condiciones para el Aprendizaje",
      "score": 7, "analysis": "...", "recommendations": ["...", "..."]
    }
  ]
}"""


class GroqService:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            logger.warning("GROQ_API_KEY no configurada.")
            self.client = None
            return
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    async def analyze_documents(self, documents_text: str):
        """
        Analiza el contexto usando Groq (Llama 3.3-70b).
        Genera exactamente 6 categorías de matriz y 5 pilares de calidad.
        """
        if not self.client:
            raise Exception("Groq no está configurado. Verifica GROQ_API_KEY en el .env")

        # Groq llama-3.3-70b soporta hasta 128k tokens, truncamos a 80k chars (~20k tokens)
        truncated_text = documents_text[:80000]

        user_prompt = (
            "INICIA AUDITORÍA PEDAGÓGICA. Analiza los siguientes documentos institutionales y genera "
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

            # Validar que tiene la estructura correcta
            if "matrix" not in result or "quality_report" not in result:
                raise ValueError(f"Respuesta JSON incompleta: faltan claves. Keys: {list(result.keys())}")

            logger.info(
                f"Groq OK: {len(result['matrix'])} categorias, "
                f"{len(result['quality_report'])} pilares"
            )
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Groq devolvio JSON invalido: {e}")
            raise Exception(f"El motor Groq devolvio una respuesta con formato invalido: {e}")
        except Exception as e:
            logger.error(f"Error en GroqService: {str(e)}")
            raise e


groq_service = GroqService()
