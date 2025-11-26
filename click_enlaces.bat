@echo off
REM Script para ejecutar ClicToriano en Windows (CLI)

cd /d "%~dp0"

REM Verificar si existe el entorno virtual
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
    echo Instalando dependencias...
    venv\Scripts\pip install -r requirements.txt
)

REM Ejecutar el programa
venv\Scripts\python click_enlaces.py %*

pause
