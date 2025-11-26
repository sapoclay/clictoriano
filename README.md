# ClicToriano

<img width="768" height="768" alt="logo" src="https://github.com/user-attachments/assets/92a7848c-14a3-4805-8426-25d6886b8f14" />

ClicToriano es una herramienta en Python que carga una página web en Chrome/Chromium y realiza clics automáticos en enlaces (puede abrir enlaces externos en nuevas pestañas), para un uso en particular. Incluye modo CLI y una interfaz gráfica ligera.
Consulta la documentación en español en `docs/USO.md` para instrucciones detalladas sobre instalación y uso, incluyendo pasos específicos para Windows.
**Contenido del repositorio**
- `click_enlaces.py`: lógica principal (Selenium + Chrome)
- `click_enlaces_gui.py`: GUI (CustomTkinter) para lanzar el proceso desde escritorio
- `run_selector.py`: selector de ejecución y ayudante para asegurar/instalar ChromeDriver
- `click_enlaces.sh`, `click_enlaces_gui.sh`: scripts para lanzar en Linux
- `install_chrome.sh`: script auxiliar para instalar Google Chrome en Linux (según distro)
- `requirements.txt`: dependencias Python

**Requisitos**
- Python 3.8+ (probado con Python 3.12)
- `pip` y opcionalmente `virtualenv`/`venv`
- Google Chrome o Chromium instalado
- ChromeDriver que coincida con la versión de Chrome (el repositorio incluye lógica para descargar/instalarlo automáticamente en Linux)

Instalación rápida (recomendado en Linux/macOS)
1. Crear y activar un entorno virtual (recomendado):

```bash
2. (Linux) Asegurarse de que existe Chrome/Chromium. Puedes usar el script incluido:

```bash
3. (Linux) El repositorio intenta instalar un `chromedriver` no-snap que coincida con tu Chrome cuando invocas `run_selector.py` o los scripts `click_enlaces*.sh`. Si prefieres instalarlo manualmente, descarga la versión que coincida con `google-chrome --version` y coloca `chromedriver` en `/usr/local/bin`:

```bash
Nota sobre Snap: en algunas distribuciones `chromedriver` puede venir como paquete `snap` (p. ej. `/snap/bin/chromium.chromedriver`). Ese `chromedriver` está confinado y no puede lanzar un Chrome/Chromium instalado fuera de snap. Por eso la herramienta intenta instalar un `chromedriver` en `/usr/local/bin` que no use snap.

Uso
Desde la línea de comandos (CLI):

```bash
Interfaz gráfica (GUI):

```bash
Otras alternativas: puedes usar `run_selector.py` para elegir CLI/GUI y (en Linux) lanzar la comprobación/instalación automática de `chromedriver`.

