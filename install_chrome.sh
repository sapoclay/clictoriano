#!/bin/bash
# Script de instalación de Google Chrome y ChromeDriver

echo "🔧 Instalando Google Chrome..."

# Descargar Google Chrome stable
wget -q -O /tmp/google-chrome-stable_current_amd64.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

# Instalar Google Chrome
sudo dpkg -i /tmp/google-chrome-stable_current_amd64.deb || sudo apt-get install -f -y

# Limpiar
rm /tmp/google-chrome-stable_current_amd64.deb

echo "✓ Google Chrome instalado correctamente"

# Verificar versión
google-chrome --version
chromedriver --version

echo ""
echo "✅ Instalación completada"
echo "Ahora puedes ejecutar: ./click_enlaces.sh https://example.com"
echo "También se puede ejecutar: ./click_enlaces_gui.sh para abrir la interfaz gráfica"
