# Uso de ClicToriano

Resumen rápido:
- ClicToriano automatiza clics en enlaces de una página web. Está pensado para navegar en enlaces internos (mismo dominio) y gestionar enlaces externos según una política configurable.

Archivo de configuración persistente:
- `~/.clictoriano/config.json` guarda las preferencias `external_policy` y `scroll_policy`.

Opciones importantes (CLI / GUI):
- `--external-policy`: `new_tab` | `same_window` | `ignore` — cómo tratar enlaces hacia otros dominios.
- `--scroll-policy`: `none` | `small` | `medium` | `full` | `random` — desplazamiento antes de clicar. `random` elige una política por clic.
- `--link-wait`: segundos a esperar activamente para que aparezcan enlaces dinámicos antes de continuar.
- `--headless`: ejecutar Chrome en modo headless (sin UI).

Política de scroll (qué hacen):
- `none`: no se desplaza.
- `small`: centra el enlace en pantalla con un pequeño ajuste.
- `medium`: centra y desplaza un poco más arriba.
- `full`: realiza un desplazamiento escalonado hasta la posición del enlace.
- `random`: antes de cada clic se selecciona aleatoriamente una de las anteriores; el log mostrará la política elegida con el prefijo "🔽 Scroll elegido:".

Registro / Auditoría:
- El programa escribe líneas de log por consola que la GUI recoge. Ejemplo de auditoría de scroll:
  [scroll] 2025-11-26 20:06:48 policy=medium href=https://... text='...'

Notas para Linux:
- Asegúrate de tener Google Chrome o Chromium instalado. En muchos sistemas la ruta es `/usr/bin/google-chrome` o similar.
- Si usas `snap` (Ubuntu), la sandbox puede cambiar la ruta del binario. Comprueba con `which google-chrome` o `google-chrome --version`.
- El instalador de `chromedriver` intenta colocarlo en `/usr/local/bin`. Si no tienes permisos puede pedir sudo.

Notas para Windows (resumen y pasos):
- El lanzador puede descargar `chromedriver.exe` y colocarlo en la ruta de usuario (ej. `%LOCALAPPDATA%\\chromedriver`) para evitar elevación.
- Para que quede disponible para todas las sesiones, añade la carpeta al `PATH` del usuario (PowerShell o Panel de Control).

Pasos detallados para Windows:

1) Comprobar la versión de Google Chrome
- Abre Chrome y ve a `chrome://settings/help` (Ayuda → Acerca de Google Chrome). Anota la versión completa, p. ej. `120.0.6098.94`.
- Alternativa en PowerShell si `chrome` está en `PATH`:
  ```powershell
  chrome --version
  ```
  o consulta el registro de Windows:
  ```powershell
  reg query "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon" /v version
  ```

2) Descargar chromedriver que coincida con la versión mayor de Chrome
- Visita: https://chromedriver.chromium.org/downloads y descarga la versión de chromedriver cuya versión "major" (parte antes del primer punto) coincida con la versión de Chrome.
- Ejemplo: si Chrome es `120.0.x`, descarga chromedriver `120.x`.

3) Instalar `chromedriver.exe` en la carpeta de usuario (sin elevación)
- Para evitar pedir permisos de administrador, coloca `chromedriver.exe` en una carpeta de tu perfil de usuario, p. ej. `%LOCALAPPDATA%\\chromedriver`.
- Ejemplo de pasos manuales:
  - Crea la carpeta: `C:\Users\<usuario>\AppData\Local\chromedriver`
  - Copia `chromedriver.exe` dentro de esa carpeta.

4) Añadir la carpeta al `PATH` del usuario (PowerShell)
- Ejecuta este snippet en PowerShell (como usuario; no requiere elevación). Sustituye si deseas una ruta distinta.
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

5) Verificar que Selenium puede encontrar `chromedriver`
- Abre una nueva PowerShell/terminal y ejecuta:
  ```powershell
  chromedriver --version
  ```
  o en Linux/macOS:
  ```bash
  chromedriver --version
  ```
- Si se muestra la versión, Selenium podrá usarlo si el ejecutable está en `PATH`.

Consejos y notas sobre Windows
- Si prefieres no modificar el PATH de usuario, `run_selector.py` y el lanzador intentan colocar `chromedriver.exe` en la carpeta de usuario y añadir esa carpeta al PATH del proceso actual automáticamente.
- Para actualizaciones futuras, descarga la versión de chromedriver que empareje la versión mayor de Chrome.
- Si el navegador no arranca por incompatibilidad entre Chrome y chromedriver, actualiza uno de los dos para que coincidan en la versión major.

Problemas comunes y soluciones:
- Error "no chrome binary": instala Google Chrome o ajusta `PATH`/rutas.
- Problemas de versión entre Chrome y chromedriver: descarga la versión de chromedriver que coincida con la versión mayor de Chrome.

Ejemplos de uso (CLI):
```bash
# Ejecuta en modo visible, espera hasta 5s por enlaces dinámicos, política de scroll full
python3 click_enlaces.py --url "https://ejemplo.com" --link-wait 5 --scroll-policy full

# Modo headless y abrir externos en nueva pestaña
python3 click_enlaces.py --url "https://ejemplo.com" --headless --external-policy new_tab
```

Cómo abrir la GUI:
- Ejecuta `python3 click_enlaces_gui.py` o usa `run_selector.py` para seleccionar el modo adecuado según tu sistema.

Notas finales:
- Si quieres que te ayude a añadir instrucciones para añadir la carpeta de `chromedriver` al `PATH` de usuario en Windows, dime y genero un snippet de PowerShell.
