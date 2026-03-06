@echo off
setlocal
title PTAFI-AI: MOTOR DE AUDITORÍA LOCAL
color 0b

echo ===========================================
echo       PTAFI-AI: AUDITORÍA PEDAGÓGICA
echo ===========================================
echo Cargando motor local (Sin dependencias externas)...
echo.

:: 1. Backend: Asegurar entorno virtual y dependencias
echo [1/2] Configurando Backend (FastAPI + Groq)...
cd backend
if not exist venv (
    echo Creando entorno virtual local...
    python -m venv venv
)

:: Activar e instalar dependencias silenciosamente
call venv\Scripts\activate
echo Instalando/Actualizando librerías necesarias...
pip install -r requirements.txt --quiet
pip install python-docx pandas openpyxl Pillow --quiet

:: Lanzar Backend en una ventana aparte
echo Lanzando Servidor de Inteligencia Artificial...
start "BACKEND - PTAFI AI" cmd /k "title BACKEND AI && cd backend && venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: 2. Frontend: Iniciar
echo [2/2] Iniciando Interfaz de Usuario (Next.js)...
cd ..
cd ptafi-frontend

:: Verificar node_modules
if not exist node_modules (
    echo Instalando dependencias de interfaz (Esto puede tardar un poco)...
    npm install
)

echo.
echo ===========================================
echo CONFIGURACIÓN COMPLETADA
echo El sistema se abrirá en tu navegador en breve.
echo URL: http://localhost:3000
echo ===========================================
echo.

npm run dev

pause
