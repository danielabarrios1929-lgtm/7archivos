from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Dict, Optional
from app.services.processor import processor
from app.services.ai_orchestrator import ai_orchestrator   # ← Orquestador Híbrido
from app.services.reporter import pdf_reporter
import logging
import base64
import os

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

        # 6. Generar Documentos (PDF y DOCX)
        try:
            pdf_bytes = pdf_reporter.generate_pdf(response_data)
            response_data["pdf_base64"] = base64.b64encode(pdf_bytes).decode('utf-8')
        except Exception as pdf_err:
            logger.error(f"[API] Error generando PDF: {str(pdf_err)}")
            response_data["pdf_base64"] = None

        try:
            docx_bytes = pdf_reporter.generate_docx(response_data)
            response_data["docx_base64"] = base64.b64encode(docx_bytes).decode('utf-8')
        except Exception as docx_err:
            logger.error(f"[API] Error generando DOCX: {str(docx_err)}")
            response_data["docx_base64"] = None

        return response_data

    except Exception as e:
        logger.error(f"[API] Error crítico en Motor IA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fallo en Auditoría IA: {str(e)}")

@router.post("/process-local-folder", response_model=AnalysisResponse)
async def process_local_folder(
    institution_name: str = Form(...),
    tutor_name: str = Form(...)
):
    """
    Endpoint especial para pruebas (Desarrollo).
    Carga automáticamente todos los archivos desde la carpeta local '7 archivos'
    sin necesidad de subirlos mediante el formulario.
    """
    logger.info(f"[API] Iniciando auditoría desde carpeta local: {institution_name}")

    # Calcular la ruta a la carpeta '7 archivos' (3 niveles arriba del archivo actual, o desde el directorio raíz)
    # asumiendo ejecutado desde /backend
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    folder_path = os.path.join(base_dir, "7 archivos")

    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail=f"No se encontró la carpeta: {folder_path}. Asegúrate de crearla en la raíz del proyecto al lado del backend.")

    documents: Dict[str, bytes] = {}
    valid_extensions = {
        '.pdf', '.docx', '.doc', '.txt', '.md',
        '.xlsx', '.xls', '.csv',
        '.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif',
        '.pptx', '.ppt',
    }

    try:
        for filename in os.listdir(folder_path):
            ext = os.path.splitext(filename)[1].lower()
            if ext in valid_extensions:
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    with open(file_path, 'rb') as f:
                        documents[filename] = f.read()
                        logger.info(f"[API] Archivo auto-cargado: {filename} ({len(documents[filename]):,} bytes)")
    except Exception as e:
        logger.error(f"[API] Error leyendo carpeta local: {e}")
        raise HTTPException(status_code=500, detail=f"Error leyendo archivos locales: {e}")

    if not documents:
        raise HTTPException(status_code=400, detail="La carpeta '7 archivos' está vacía o no tiene formatos válidos.")

    missing = processor.validate_integrity(documents)
    context = processor.prepare_context_for_ai(documents)
    logger.info(f"[API] Contexto local preparado: {len(context):,} chars totales")

    is_demo = "demo" in institution_name.lower()

    try:
        raw_analysis = await ai_orchestrator.analyze(context, force_groq=is_demo)

        engine_used = raw_analysis.pop("_engine_used", "desconocido")
        engine_reason = raw_analysis.pop("_engine_reason", "")
        engine_warning = raw_analysis.pop("_warning", None)

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

        # 6. Generar Documentos (PDF y DOCX)
        try:
            pdf_bytes = pdf_reporter.generate_pdf(response_data)
            response_data["pdf_base64"] = base64.b64encode(pdf_bytes).decode('utf-8')
        except Exception as pdf_err:
            logger.error(f"[API] Error generando PDF: {str(pdf_err)}")
            response_data["pdf_base64"] = None

        try:
            docx_bytes = pdf_reporter.generate_docx(response_data)
            response_data["docx_base64"] = base64.b64encode(docx_bytes).decode('utf-8')
        except Exception as docx_err:
            logger.error(f"[API] Error generando DOCX: {str(docx_err)}")
            response_data["docx_base64"] = None

        return response_data

    except Exception as e:
        logger.error(f"[API] Error crítico en Motor IA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fallo en Auditoría IA desde carpeta: {str(e)}")
