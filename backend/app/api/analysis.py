from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Dict
from app.services.processor import processor
from app.services.ai_orchestrator import ai_orchestrator   # ← Orquestador Híbrido
from app.services.reporter import pdf_reporter
import logging
import base64

logger = logging.getLogger(__name__)
router = APIRouter()

from app.models.schemas import AnalysisResponse

@router.post("/process", response_model=AnalysisResponse)
async def process_analysis(
    files: List[UploadFile] = File(...),
    institution_name: str = Form(...),
    tutor_name: str = Form(...)
):
    """
    Endpoint de análisis pedagógico con Arquitectura Híbrida IA.
    - Gemini 1.5 Pro: Motor PRINCIPAL para documentos grandes (>40k chars)
    - Groq Llama 3.3: Apoyo y motor directo para documentos pequeños
    - Fallback automático si algún motor falla.
    """
    logger.info(f"[API] Iniciando auditoría para: {institution_name}")

    # 1. Cargar archivos (cualquier formato soportado)
    documents: Dict[str, bytes] = {}
    for file in files:
        documents[file.filename] = await file.read()
        logger.info(f"[API] Archivo cargado: {file.filename} ({len(documents[file.filename]):,} bytes)")

    # 2. Checklist informativo (no bloqueante)
    missing = processor.validate_integrity(documents)

    # 3. Preparar contexto multi-formato
    context = processor.prepare_context_for_ai(documents)
    logger.info(f"[API] Contexto preparado: {len(context):,} chars totales")

    # Si es modo DEMO (por la palabra demo en la institución), forzamos Groq siempre
    is_demo = "demo" in institution_name.lower()

    # 4. ── Orquestador IA: Gemini principal + Groq de apoyo ──────────────────
    try:
        raw_analysis = await ai_orchestrator.analyze(context, force_groq=is_demo)

        # Meta-info del motor usado (para debugging / transparencia)
        engine_used = raw_analysis.pop("_engine_used", "desconocido")
        engine_reason = raw_analysis.pop("_engine_reason", "")
        engine_warning = raw_analysis.pop("_warning", None)
        logger.info(f"[API] Motor usado: {engine_used} | Razón: {engine_reason}")

        # 5. Estructurar respuesta final
        response_data = {
            "institution_info": {
                "name": institution_name,
                "tutor": tutor_name
            },
            "matrix": raw_analysis.get("matrix", []),
            "quality_report": raw_analysis.get("quality_report", []),
            "integrity_check": {
                "missing": missing,
                "status": "partial" if missing else "complete"
            },
            "ai_engine": {
                "used": engine_used,
                "reason": engine_reason,
                "warning": engine_warning
            },
            "status": "success"
        }

        # 6. Generar PDF (Base64)
        try:
            pdf_bytes = pdf_reporter.generate_pdf(response_data)
            response_data["pdf_base64"] = base64.b64encode(pdf_bytes).decode('utf-8')
        except Exception as pdf_err:
            logger.error(f"[API] Error generando PDF: {str(pdf_err)}")
            response_data["pdf_base64"] = None

        return response_data

    except Exception as e:
        logger.error(f"[API] Error crítico en Motor IA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fallo en Auditoría IA: {str(e)}")
