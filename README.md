# ClicToriano

![logo](https://github.com/user-attachments/assets/92a7848c-14a3-4805-8426-25d6886b8f14)

ClicToriano es una herramienta en Python que carga una página web en Chrome/Chromium y realiza clics automáticos en enlaces (puede abrir enlaces externos en nuevas pestañas), para un uso en particular. Incluye modo CLI y una interfaz gráfica ligera.
Consulta la documentación en español en `docs/USO.md` para instrucciones detalladas sobre instalación y uso, incluyendo pasos específicos para Windows.

## Contenido del repositorio

- `click_enlaces.py`: lógica principal (Selenium + Chrome)
- `click_enlaces_gui.py`: GUI (CustomTkinter) para lanzar el proceso desde escritorio
- `run_selector.py`: selector de ejecución y ayudante para asegurar/instalar ChromeDriver
- `click_enlaces.sh`, `click_enlaces_gui.sh`: scripts para lanzar en Linux
- `install_chrome.sh`: script auxiliar para instalar Google Chrome en Linux (según distro)
- `requirements.txt`: dependencias Python

## Requisitos

- Python 3.8+ (probado con Python 3.12)
- `pip` y opcionalmente `virtualenv`/`venv`
- Google Chrome o Chromium instalado
- ChromeDriver que coincida con la versión de Chrome (el repositorio incluye lógica para descargar/instalarlo automáticamente en Linux)

## Instalación rápida (recomendado en Linux)

1. Crear y activar un entorno virtual (recomendado):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. (Linux) Asegurarse de que existe Chrome/Chromium. Puedes usar el script incluido `install_chrome.sh` según tu distribución.

3. (Linux) El repositorio intenta instalar un `chromedriver` no-snap que coincida con tu Chrome cuando invocas `run_selector.py` o los scripts `click_enlaces*.sh`. Si prefieres instalarlo manualmente, descarga la versión que coincida con `google-chrome --version` y coloca `chromedriver` en `/usr/local/bin`:

```bash
# Ejemplo (ajusta la versión según tu Chrome):
wget https://chromedriver.storage.googleapis.com/<<VERSION>>/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```

Nota sobre Snap: en algunas distribuciones `chromedriver` puede venir como paquete `snap` (p. ej. `/snap/bin/chromium.chromedriver`). Ese `chromedriver` está confinado y no puede lanzar un Chrome/Chromium instalado fuera de snap. Por eso la herramienta intenta instalar un `chromedriver` en `/usr/local/bin` o `~/.local/bin` que no use snap.

## Uso

<img width="752" height="111" alt="run_selector" src="https://github.com/user-attachments/assets/42283d2b-a0d1-4bed-99d7-31389ed1c78f" />

### Desde la línea de comandos (CLI)

```bash
./click_enlaces.sh https://example.com --link-wait 5 --browser chrome
```

### Interfaz gráfica (GUI)

```bash
./click_enlaces_gui.sh
```

Otras alternativas: puedes usar `run_selector.py` para elegir CLI/GUI y (opcionalmente) instalar el webdriver automáticamente.

## Instalar Webdriver con `run_selector.py`

-------------------------------------

Se añadió el módulo `webdrivers.py` y la opción CLI `--install-webdriver` en `run_selector.py` para facilitar la instalación automática de los drivers:

- `--install-webdriver`: intenta descargar e instalar el webdriver apropiado según `--browser` (por ejemplo `chrome` o `firefox`).
- `--install-chromedriver`: opción de compatibilidad que mantiene el comportamiento previo.

Ejemplos:

```bash
# Instalar chromedriver (específico):
python3 run_selector.py --install-chromedriver

# Instalar el webdriver adecuado para Chrome (recomendado):
python3 run_selector.py --install-webdriver --browser chrome

# Instalar el webdriver adecuado para Firefox (geckodriver):
python3 run_selector.py --install-webdriver --browser firefox
```

Notas importantes:

- En Windows la instalación coloca los binarios en `%LOCALAPPDATA%/webdrivers` o `%LOCALAPPDATA%/chromedriver` según la estrategia; puede ser necesario añadir esa carpeta al PATH de usuario (se incluye un snippet en `docs/USO.md`).
- En Linux si `/usr/local/bin` no es escribible, el instalador usa `~/.local/bin`. Asegúrate de que esa carpeta está en tu PATH (el script `click_enlaces_gui.sh` lo añade automáticamente).
- Si prefieres no usar el instalador automático, descarga manualmente desde:
  - [ChromeDriver](https://chromedriver.chromium.org/downloads)
  - [GeckoDriver](https://github.com/mozilla/geckodriver/releases)
- Si encuentras errores de "Process unexpectedly closed with status 127" en Firefox, verifica que `~/.local/bin` esté en PATH o instala manualmente geckodriver en `/usr/local/bin`.

## Soporte y límites

Este instalador cubre las plataformas Linux y Windows y funciona sin dependencias externas adicionales. En entornos corporativos o con políticas restrictivas la descarga automática puede fallar; en ese caso sigue el proceso manual o pide al administrador instalar el driver en una ubicación conocida.

## Autor y Licencia

- **Autor:** entreunosyceros
- **Licencia:** MIT License (ver el archivo `LICENSE` en el repositorio)
