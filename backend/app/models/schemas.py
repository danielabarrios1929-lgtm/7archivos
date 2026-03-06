from pydantic import BaseModel, Field
from typing import List, Optional

class FindingEvidence(BaseModel):
    text: str = Field(..., description="Fragmento textual del hallazgo")
    document_name: str = Field(..., description="Nombre del documento fuente")
    page: Optional[int] = Field(None, description="NÃºmero de pÃ¡gina")

class MatrixCategory(BaseModel):
    category_name: str
    hallazgo: str
    evidencia: FindingEvidence
    interpretacion: str
    implicacion_pfi: str

class QualityPillar(BaseModel):
    pillar_name: str
    score: int = Field(..., ge=1, le=10)
    analysis: str
    recommendations: List[str]

class AnalysisResponse(BaseModel):
    institution_info: dict
    matrix: List[MatrixCategory]
    quality_report: List[QualityPillar]
    integrity_check: Optional[dict] = None
    status: str = "success"
