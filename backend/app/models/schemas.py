from pydantic import BaseModel, Field
from typing import List, Optional

class FindingEvidence(BaseModel):
    text: Optional[str] = Field(None, description="Fragmento textual del hallazgo")
    document_name: Optional[str] = Field(None, description="Nombre del documento fuente")
    page: Optional[int] = Field(None, description="Número de página")

class MatrixCategory(BaseModel):
    category_name: Optional[str] = None
    hallazgo: Optional[str] = None
    evidencia: Optional[FindingEvidence] = None
    interpretacion: Optional[str] = None
    implicacion_pfi: Optional[str] = None

class QualityPillar(BaseModel):
    pillar_name: Optional[str] = None
    score: Optional[int] = Field(None, ge=0, le=10)
    analysis: Optional[str] = None
    recommendations: Optional[List[str]] = None

class AnalysisResponse(BaseModel):
    institution_info: Optional[dict] = None
    matrix: List[MatrixCategory] = []
    quality_report: List[QualityPillar] = []
    integrity_check: Optional[dict] = None
    pdf_base64: Optional[str] = None
    status: str = "success"
