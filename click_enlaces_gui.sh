#!/bin/bash
# Script para ejecutar la interfaz gráfica de ClicToriano

cd "$(dirname "$0")"

# Asegurar que ~/.local/bin esté en PATH para geckodriver
export PATH="$HOME/.local/bin:$PATH"

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

# Ejecutar la interfaz gráfica
./venv/bin/python3 click_enlaces_gui.py
