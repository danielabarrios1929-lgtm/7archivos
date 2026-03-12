@echo off
chcp 65001 >nul
title PTAFI-AI — Sistema Completo

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║          PTAFI-AI — INICIO AUTOMATICO COMPLETO             ║
echo  ║  Carga los 7 archivos y los analiza con IA                 ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

:: ─── Ir al directorio del proyecto ────────────────────────────────
cd /d "%~dp0"

:: ─── Verificar Python ─────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python no encontrado. Instala Python 3.10+
    pause
    exit /b 1
)

:: ─── Activar entorno virtual ──────────────────────────────────────
if exist "backend\venv\Scripts\activate.bat" (
    echo  [OK] Activando entorno virtual...
    call backend\venv\Scripts\activate.bat
) else (
    echo  [INFO] Sin entorno virtual, usando Python global
)

:: ─── Instalar dependencias si faltan ──────────────────────────────
echo  [INFO] Verificando dependencias...
pip install requests --quiet 2>nul

:: ─── Mostrar archivos disponibles ─────────────────────────────────
echo.
echo  ─────────────────────────────────────────────────────────────
echo   ARCHIVOS EN LA CARPETA "7 archivos":
echo  ─────────────────────────────────────────────────────────────
dir "7 archivos" /b 2>nul
echo  ─────────────────────────────────────────────────────────────
echo.

:: ─── Opción: Solo cargar o iniciar todo ───────────────────────────
echo  ¿Qué deseas hacer?
echo.
echo   [1] Iniciar backend + Enviar 7 archivos al análisis IA
echo   [2] Solo ver qué archivos se cargarían (sin procesar)
echo   [3] Solo iniciar el backend (sin enviar archivos)
echo   [4] Solo enviar archivos (backend ya está corriendo)
echo.
set /p OPCION="  Elige una opción [1-4]: "

if "%OPCION%"=="2" goto solo_listar
if "%OPCION%"=="3" goto solo_backend
if "%OPCION%"=="4" goto solo_enviar
goto iniciar_completo

:iniciar_completo
:: ─── Iniciar Backend en ventana separada ──────────────────────────
echo.
echo  [1/3] Iniciando Backend PTAFI-AI...
start "PTAFI-AI Backend" cmd /k "cd /d "%~dp0backend" && call venv\Scripts\activate.bat 2>nul && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

:: Esperar a que el backend esté listo
echo  [2/3] Esperando que el backend inicie (15 segundos)...
timeout /t 15 /nobreak >nul

:: ─── Ingresar nombre de institución ───────────────────────────────
echo.
echo  ─────────────────────────────────────────────────────────────
set /p INSTITUCION="  Nombre de la institución [Guaimaral]: "
if "%INSTITUCION%"=="" set INSTITUCION=Institución Educativa Guaimaral

set /p TUTOR="  Nombre del tutor [Tutor PTAFI]: "
if "%TUTOR%"=="" set TUTOR=Tutor PTAFI

:: ─── Enviar archivos al análisis ──────────────────────────────────
echo.
echo  [3/3] Enviando 7 archivos al motor de análisis IA...
python auto_cargar_7archivos.py --institucion "%INSTITUCION%" --tutor "%TUTOR%"
goto fin

:solo_listar
echo.
echo  Archivos que se procesarían:
python auto_cargar_7archivos.py --solo-listar
goto fin

:solo_backend
echo.
echo  Iniciando solo el backend...
cd backend
call venv\Scripts\activate.bat 2>nul
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
goto fin

:solo_enviar
echo.
set /p INSTITUCION="  Nombre de la institución [Guaimaral]: "
if "%INSTITUCION%"=="" set INSTITUCION=Institución Educativa Guaimaral
set /p TUTOR="  Nombre del tutor [Tutor PTAFI]: "
if "%TUTOR%"=="" set TUTOR=Tutor PTAFI
python auto_cargar_7archivos.py --institucion "%INSTITUCION%" --tutor "%TUTOR%"

:fin
echo.
echo  ─────────────────────────────────────────────────────────────
echo   El resultado se guardó en: resultado_analisis.json
echo  ─────────────────────────────────────────────────────────────
echo.
pause
