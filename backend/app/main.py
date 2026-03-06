from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api import analysis
from app.core.config import settings

app = FastAPI(
    title="PTAFI-AI API",
    description="Sistema de Procesamiento Analítico Multidocumental Concurrente para Educación",
    version="1.0.0"
)

# Configuración de CORS para el frontend en Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajustar en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "PTAFI-AI Engine Running", "version": "1.0.0"}

# Incluir rutas de análisis
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
