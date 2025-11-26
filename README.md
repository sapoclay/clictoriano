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

Variables de entorno y `--chrome-path`
- `--chrome-path <ruta>`: fuerza el binario de Chrome/Chromium a usar (ej.: `/opt/google/chrome/chrome` o `C:\Program Files\Google\Chrome\Application\chrome.exe`).
- También se aceptan estas variables de entorno si prefieres exportarlas:
    - `CLICTORIS_CHROME_PATH`
Problemas comunes y soluciones

Preferencia GUI: comportamiento con enlaces externos

En la interfaz gráfica, en el menú `Preferencias -> Configuración` puedes elegir cómo tratar los enlaces que apuntan a dominios distintos del indicado en la URL inicial:

- **Abrir en nueva pestaña/ventana** (por defecto): abre el enlace externo en una pestaña nueva y vuelve al foco de la ventana principal.
- **Abrir en la misma ventana**: carga el enlace externo en la misma pestaña donde estás navegando.
- **Ignorar enlaces externos**: no se abrirán ni seguirán enlaces externos; el programa los marcará como visitados y continuará con enlaces internos.

La selección se aplica inmediatamente al iniciar el proceso desde la GUI.

Persistencia de preferencias

Las preferencias de la GUI (actualmente sólo la política de enlaces externos) se guardan automáticamente en `~/.clictoriano/config.json` y se recargan al iniciar la aplicación. Puedes editar ese fichero manualmente si lo deseas. Formato:

```json
{
    "external_policy": "new_tab"  
}
```
Valores válidos: `new_tab`, `same_window`, `ignore`.

- Error: `session not created ... no chrome binary at /usr/bin/google-chrome`
    - Causa: `chromedriver` no logra localizar o lanzar el binario de Chrome (común cuando `chromedriver` proviene de `snap`).
- Error: ventanas duplicadas al iniciar la GUI
    - La aplicación intenta evitar una pestaña `about:blank/data:` arrancando Chrome con `--app=<url>`. Si tu entorno abre dos ventanas, la aplicación cierra duplicados automáticamente; si sigues viendo dos ventanas, revisa si tu `click_enlaces_gui.py` está ejecutando la acción dos veces (botón pulsado doble) o si hay procesos previos de `chromedriver`/`chrome` en ejecución.

- Error: permiso al instalar `chromedriver` en `/usr/local/bin`
Diagnóstico rápido

Si algo va mal, ejecuta estos comandos y pega la salida para ayuda:

```bash
Desarrollo

- Código principal: `click_enlaces.py`.
- Tests/manual: lanzar `click_enlaces.py` con `--max-clicks 1` para validar arranque.

Contacto
Licencia

Proyecto personal (no se incluye licencia específica en este repositorio).

# ClicToriano - Programa de Clic Automático en Enlaces

Programa en Python que visita una URL y hace clic automáticamente en los enlaces que encuentra en la página, con un intervalo de tiempo configurable.

## 📋 Características

- ✅ Hace clic automático en enlaces de una página web
- ✅ **Solo navega dentro del mismo dominio** (no sigue enlaces externos)
- ⏱️ Intervalo de tiempo configurable entre clics
- 🔀 Selección aleatoria de enlaces no visitados
- 🎯 Límite opcional de clics máximos
- 👁️ Modo headless disponible
- 📊 Registro de enlaces visitados
- 🛡️ Manejo de errores robusto

## 🛠️ Instalación

### Linux (Ubuntu/Debian)

1.  **Clonar o descargar** este repositorio.
2.  **Dar permisos de ejecución** a los scripts:
    ```bash
    chmod +x click_enlaces.sh click_enlaces_gui.sh install_chrome.sh
    ```
3.  **Instalar dependencias del sistema** (si es necesario):
    ```bash
    ./install_chrome.sh
    ```

### Windows

1.  **Descargar** este repositorio.
2.  Tener instalado **Python 3** (asegúrate de marcar "Add Python to PATH" durante la instalación).
3.  Tener instalado **Google Chrome**.
4.  No es necesario instalar nada más manualmente; los scripts `.bat` crearán el entorno virtual e instalarán las librerías automáticamente la primera vez.

### Chromedriver en Windows (nota rápida)

Si Selenium/GChrome requiere `chromedriver` en Windows, una forma segura sin elevación es colocar `chromedriver.exe` en una carpeta del perfil de usuario y añadir esa carpeta al `PATH` de usuario. Aquí tienes un snippet de PowerShell (ejecutar como usuario):

```powershell
$cd = Join-Path $env:LOCALAPPDATA 'chromedriver'
if (-not (Test-Path $cd)) { New-Item -ItemType Directory -Path $cd -Force }
$old = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($old -notlike "*${cd}*") {
    [Environment]::SetEnvironmentVariable('Path', "$old;$cd", 'User')
    Write-Output "Ruta agregada al PATH de usuario: $cd"
} else {
    Write-Output "La ruta ya está en el PATH de usuario: $cd"
}
Write-Output "Reinicia la terminal o la sesión para que los cambios surtan efecto."
```

Después coloca `chromedriver.exe` en `%LOCALAPPDATA%\chromedriver` y abre una nueva terminal para comprobar con `chromedriver --version`.

## 🚀 Uso

### Interfaz Gráfica (Recomendado)

*   **Linux**: Ejecuta `./click_enlaces_gui.sh`
*   **Windows**: Haz doble clic en `click_enlaces_gui.bat`

### Línea de Comandos

*   **Linux**:
    ```bash
    ./click_enlaces.sh https://es.wikipedia.org/wiki/Python
    ```
*   **Windows**:
    Abre una terminal (CMD o PowerShell) en la carpeta y ejecuta:
    ```cmd
    click_enlaces.bat https://es.wikipedia.org/wiki/Python
    ```

**2. Con intervalo personalizado de 10 segundos:**
```bash
python3 click_enlaces.py https://example.com -i 10
```

**3. Modo headless (sin ventana del navegador):**
```bash
python3 click_enlaces.py https://example.com --headless
```

**4. Limitar a 20 clics máximo:**
```bash
python3 click_enlaces.py https://example.com --max-clicks 20
```

**5. Combinación de opciones:**
```bash
python3 click_enlaces.py https://example.com -i 3 --headless --max-clicks 50
```

## 🎛️ Opciones

| Opción | Descripción | Default |
|--------|-------------|---------|
| `url` | URL de la página web (requerido) | - |
| `-i, --intervalo` | Segundos entre clics | 5 |
| `--headless` | Ejecutar sin interfaz gráfica | False |
| `--max-clicks` | Número máximo de clics | Infinito |

## 🔧 Funcionamiento

1. **Inicia el navegador** Chrome/Chromium con Selenium
2. **Carga la URL** proporcionada
3. **Extrae el dominio base** de la URL (ej: `https://ejemplo.com`)
4. **Busca todos los enlaces** en la página actual
5. **Filtra los enlaces** para quedarse solo con los del mismo dominio
6. **Selecciona aleatoriamente** un enlace no visitado del mismo dominio
7. **Hace clic** en el enlace (carga la nueva página)
8. **Espera** el intervalo de tiempo configurado
9. **Repite** desde el paso 4 hasta alcanzar el límite de clics o visitar todos los enlaces internos

> **Nota importante:** El programa **SOLO** hace clic en enlaces que pertenecen al mismo dominio que la URL inicial. Por ejemplo, si inicias con `https://wikipedia.org`, solo visitará páginas de `https://wikipedia.org` e ignorará enlaces a otros sitios.

## ⚠️ Notas importantes

- El programa solo hace clic en enlaces que comiencen con `http://` o `https://`
- Los enlaces ya visitados no se vuelven a visitar
- Presiona `Ctrl+C` para detener el programa en cualquier momento
- El programa mostrará estadísticas al finalizar

## 📊 Ejemplo de salida

```
✓ Navegador iniciado correctamente

🌐 Cargando URL: https://example.com

⏱️  Intervalo entre clics: 5 segundos

============================================================
Presiona Ctrl+C para detener el programa
============================================================

[1] 🖱️  Haciendo clic en:
    Texto: Más información
    URL: https://example.com/info
    ✓ Página cargada correctamente
    ⏳ Esperando 5 segundos...

[2] 🖱️  Haciendo clic en:
    Texto: Contacto
    URL: https://example.com/contact
    ✓ Página cargada correctamente
    ⏳ Esperando 5 segundos...
```

## 🐛 Solución de problemas

### Problema: "ChromeDriver no encontrado" o "Chrome instance exited"

#### Para Ubuntu (Chromium instalado via Snap):

El problema más común en Ubuntu es que Chromium se instala como un paquete Snap, lo cual puede causar problemas de compatibilidad con Selenium. Aquí hay dos soluciones:

**Solución 1: Instalar Google Chrome (recomendado)**

```bash
# Ejecutar el script de instalación incluido
./install_chrome.sh
```

O manualmente:
```bash
# Descargar e instalar Google Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f -y
rm google-chrome-stable_current_amd64.deb
```

**Solución 2: Usar Playwright (alternativa moderna a Selenium)**

Si Chrome/Chromium sigue causando problemas, considera usar `click_enlaces_playwright.py` (si está disponible) o instala Playwright:

```bash
./venv/bin/pip install playwright
./venv/bin/playwright install chromium
```

### Error: Módulo selenium no encontrado

```bash
pip install selenium
```

### El navegador no se inicia en modo headless

Asegúrate de tener instalado `chromium-browser`:
```bash
sudo apt install chromium-browser
```

### Forzar ruta del binario de Chrome/Chromium

Si la aplicación no encuentra automáticamente el binario de Chrome/Chromium, puedes forzar la ruta de dos maneras:

- Usando la variable de entorno (cualquiera de estas, se pondrá en orden de preferencia):
    - `CLICTORIS_CHROME_PATH` (variable heredada del proyecto)
    - `CHROME_BIN` (nombre habitual y común)
    - `GOOGLE_CHROME_PATH` / `GOOGLE_CHROME_SHIM`

    Ejemplo:

    ```bash
    export CHROME_BIN=/opt/google/chrome/google-chrome
    python3 click_enlaces.py https://example.com
    ```

- O usando el nuevo argumento de línea de comandos `--chrome-path`:

    ```bash
    python3 click_enlaces.py https://example.com --chrome-path /opt/google/chrome/google-chrome
    ```

Si aún falla, revisa permisos de ejecución del binario (`ls -l /ruta/a/google-chrome`) y que `chromedriver` tiene la misma versión que tu navegador (`chromedriver --version` vs `google-chrome --version`).

## 📝 Licencia

Este programa es de código abierto y puede ser utilizado libremente.

## 👨‍💻 Autor

Creado para automatizar la navegación web y pruebas de enlaces.
