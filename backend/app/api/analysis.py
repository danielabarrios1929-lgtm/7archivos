from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Dict
from app.services.processor import processor
from app.services.groq_service import groq_service
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
    Endpoint ultra-rápido: Procesa documentos con Groq Llama 3.3.
    Sin restricciones de integridad obligatorias para permitir flexibilidad de archivos.
    """
    logger.info(f"Procesando auditoría para: {institution_name}")
    
    # 1. Cargar archivos (Cualquier formato)
    documents: Dict[str, bytes] = {}
    for file in files:
        # Usamos el nombre completo del archivo para soportar extensiones
        documents[file.filename] = await file.read()

    # 2. Checklist informativo (No bloqueante)
    missing = processor.validate_integrity(documents)

    # 3. Preparar Contexto Multi-formato
    context = processor.prepare_context_for_ai(documents)

    # 4. Inferencia con Motor Groq (Llama 3.3-70b)
    try:
        # Solo usamos Groq por decisión del usuario
        raw_analysis = await groq_service.analyze_documents(context)
        
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
            "status": "success"
        }
        
        # 6. Generar PDF (Base64)
        try:
            pdf_bytes = pdf_reporter.generate_pdf(response_data)
            response_data["pdf_base64"] = base64.b64encode(pdf_bytes).decode('utf-8')
        except Exception as pdf_err:
            logger.error(f"Error generando PDF: {str(pdf_err)}")
            response_data["pdf_base64"] = None
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error crítico en Motor de IA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fallo en Auditoría IA: {str(e)}")
