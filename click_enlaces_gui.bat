@echo off
REM Script para ejecutar ClicToriano GUI en Windows

cd /d "%~dp0"

REM Verificar si existe el entorno virtual
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
    echo Instalando dependencias...
    venv\Scripts\pip install -r requirements.txt
)

REM Ejecutar la interfaz gráfica
start venv\Scripts\pythonw click_enlaces_gui.py
