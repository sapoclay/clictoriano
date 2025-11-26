#!/bin/bash
# Script de ayuda para ejecutar el programa ClicToriano

cd "$(dirname "$0")"

# Verificar si existe el entorno virtual
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
    echo "⬇️  Instalando dependencias..."
    ./venv/bin/pip install -r requirements.txt
fi

# Asegurar que ChromeDriver esté instalado y coincida con Chrome
echo "🔍 Comprobando ChromeDriver..."
./venv/bin/python3 -c "from run_selector import ensure_chromedriver; ensure_chromedriver()"

# Ejecutar el programa
./venv/bin/python3 click_enlaces.py "$@"
