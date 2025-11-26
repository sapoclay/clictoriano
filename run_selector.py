#!/usr/bin/env python3
"""Utilidad para seleccionar y ejecutar el script adecuado de ClicToriano
según el sistema operativo.

- En Linux puedes elegir entre el script CLI y el script GUI 
- En Windows puedes elegir entre el archivo batch CLI y el archivo batch GUI 

El script detecta el SO mediante `platform.system()` y muestra un menú numerado sencillo del todo.
El script seleccionado se ejecuta con subprocess.run.
"""

import os
import platform
import subprocess
import sys
import argparse
import shutil
try:
    from webdrivers import ensure_webdriver
except Exception:
    ensure_webdriver = None


def obtener_scripts():
    """Devuelve un diccionario con las opciones disponibles según el SO."""
    sistema = platform.system()
    if sistema == "Windows":
        return {
            "1": ("CLI (Batch)", "click_enlaces.bat"),
            "2": ("GUI (Batch)", "click_enlaces_gui.bat"),
        }
    else:  # Se asume Linux/Unix‑like
        return {
            "1": ("CLI (Shell)", "click_enlaces.sh"),
            "2": ("GUI (Shell)", "click_enlaces_gui.sh"),
        }


def _confirm_exit_prompt():
    """Pregunta al usuario si desea salir tras un Ctrl+C en modo interactivo.

    Devuelve True si el usuario confirma salir, False para continuar.
    """
    try:
        resp = input("¿Desea salir? [Y/n]: ").strip().lower()
    except Exception:
        # Si la entrada falla, asumimos que quiere salir
        return True
    return resp in ("", "y", "s", "si", "yes")



def get_chrome_version():
    """Intentar detectar la versión de Chrome/Chromium instalada según el SO.

    Devuelve la versión como cadena (p.ej. '142.0.7444.175') o None.
    """
    candidates = []
    sistema = platform.system()
    if sistema == 'Windows':
        candidates = [
            r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\\Google\\Chrome\\Application\\chrome.exe"),
        ]
    elif sistema == 'Darwin':
        candidates = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    else:
        # Linux / other
        candidates = [
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
        ]
        # also try from PATH
        which = shutil.which('google-chrome') or shutil.which('chromium') or shutil.which('chromium-browser')
        if which:
            candidates.insert(0, which)

    for cmd in candidates:
        if not cmd:
            continue
        try:
            out = subprocess.check_output([cmd, '--version'], universal_newlines=True, stderr=subprocess.DEVNULL)
            # Ejemplo: 'Google Chrome 142.0.7444.175\n' o 'Chromium 142.0.7444.175'
            ver = out.strip().split()[-1]
            return ver
        except Exception:
            continue
    return None

def get_chromedriver_version(path):
    try:
        out = subprocess.check_output([path, "--version"], universal_newlines=True)
        # Ejemplo: 'ChromeDriver 142.0.7444.175 (....)'
        parts = out.strip().split()
        if len(parts) >= 2:
            return parts[1]
        return None
    except Exception:
        return None

def ensure_chromedriver():
    """Asegura que exista un ChromeDriver compatible.

    - En Linux coloca el binario en `/usr/local/bin/chromedriver` (requiere sudo si no hay permisos).
    - En Windows descarga `chromedriver.exe` y lo coloca en una carpeta de usuario sin elevación, y añade esa carpeta a `PATH` para este proceso.
    """
    import shutil
    import tempfile
    import zipfile
    import urllib.request

    sistema = platform.system()
    chrome_version = get_chrome_version()
    if not chrome_version:
        print("No se pudo detectar la versión de Google Chrome. Saltando verificación de ChromeDriver.")
        return

    if sistema == 'Windows':
        # Carpeta de usuario donde colocar chromedriver.exe sin necesitar elevación
        local_appdata = os.getenv('LOCALAPPDATA') or os.path.expanduser('~\\AppData\\Local')
        dest_dir = os.path.join(local_appdata, 'chromedriver')
        os.makedirs(dest_dir, exist_ok=True)
        chromedriver_path = os.path.join(dest_dir, 'chromedriver.exe')
        cd_version = get_chromedriver_version(chromedriver_path) if os.path.exists(chromedriver_path) else None
        if cd_version == chrome_version:
            # Asegurar que el directorio está en PATH para este proceso
            os.environ['PATH'] = dest_dir + os.pathsep + os.environ.get('PATH', '')
            return

        print(f"Descargando ChromeDriver {chrome_version} para Windows (sin elevación)...")
        url = f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_version}/win64/chromedriver-win64.zip"
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, 'chromedriver.zip')
            try:
                urllib.request.urlretrieve(url, zip_path)
            except Exception as e:
                print(f"Error descargando ChromeDriver: {e}")
                return
            try:
                with zipfile.ZipFile(zip_path) as z:
                    z.extractall(tmpdir)
            except Exception as e:
                print(f"Error extrayendo ChromeDriver: {e}")
                return
            # Dentro de la ZIP suele haber una carpeta chromedriver-win64\chromedriver.exe
            candidate = None
            for root, dirs, files in os.walk(tmpdir):
                if 'chromedriver.exe' in files:
                    candidate = os.path.join(root, 'chromedriver.exe')
                    break
            if not candidate:
                print("No se encontró chromedriver.exe en el zip descargado")
                return
            try:
                shutil.move(candidate, chromedriver_path)
            except Exception:
                try:
                    # Intentar copiar si move falla
                    shutil.copy(candidate, chromedriver_path)
                except Exception as e:
                    print(f"Error al mover/copy chromedriver.exe: {e}")
                    return
        # Añadir al PATH de este proceso
        os.environ['PATH'] = dest_dir + os.pathsep + os.environ.get('PATH', '')
        print(f"✓ ChromeDriver {chrome_version} instalado en {chromedriver_path} (usuario)")
        return

    # Linux / macOS fallback
    chromedriver_path = '/usr/local/bin/chromedriver'
    cd_version = get_chromedriver_version(chromedriver_path) if os.path.exists(chromedriver_path) else None
    if cd_version == chrome_version:
        return

    print(f"Descargando ChromeDriver {chrome_version} para Linux/macOS...")
    url = f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_version}/linux64/chromedriver-linux64.zip"
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, 'chromedriver.zip')
        try:
            urllib.request.urlretrieve(url, zip_path)
            with zipfile.ZipFile(zip_path) as z:
                z.extractall(tmpdir)
        except Exception as e:
            print(f"Error descargando o extrayendo ChromeDriver: {e}")
            return
        src = os.path.join(tmpdir, 'chromedriver-linux64', 'chromedriver')
        if not os.path.exists(src):
            # intentar buscar binario en el TMP
            found = None
            for root, dirs, files in os.walk(tmpdir):
                if 'chromedriver' in files:
                    found = os.path.join(root, 'chromedriver')
                    break
            if found:
                src = found
        try:
            try:
                shutil.move(src, chromedriver_path)
                os.chmod(chromedriver_path, 0o755)
            except PermissionError:
                print("Permiso denegado para mover ChromeDriver. Intentando con sudo...")
                subprocess.run(["sudo", "cp", src, chromedriver_path], check=True)
                subprocess.run(["sudo", "chmod", "+x", chromedriver_path], check=True)
        except Exception as e:
            print(f"Error instalando ChromeDriver: {e}")
            return
    print(f"✓ ChromeDriver {chrome_version} instalado en {chromedriver_path}")


def warn_windows_chromedriver_missing():
    """Si estamos en Windows y no se encuentra chromedriver, imprimir instrucciones rápidas."""
    sistema = platform.system()
    if sistema != 'Windows':
        return
    # Comprobar en PATH
    in_path = shutil.which('chromedriver') is not None
    # Comprobar carpeta de usuario donde el lanzador suele instalarlo
    local_appdata = os.getenv('LOCALAPPDATA') or os.path.expanduser('~\\AppData\\Local')
    user_cd = os.path.join(local_appdata, 'chromedriver', 'chromedriver.exe')
    if in_path or os.path.exists(user_cd):
        return

    # Mensaje conciso y útil para usuarios menos técnicos
    print('\n== Atención: ChromeDriver no detectado en Windows ==')
    print('Selenium necesita `chromedriver.exe` para controlar Google Chrome. Sigue estos pasos rápidos:')
    print(' 1) Averigua la versión de Chrome: abre chrome://settings/help y anota la versión (p.ej. 120.x)')
    print(' 2) Descarga la versión de ChromeDriver que coincida con la versión "major" (parte antes del primer punto):')
    print('    https://chromedriver.chromium.org/downloads')
    print(' 3) Coloca el archivo `chromedriver.exe` en:')
    print(f"    %LOCALAPPDATA%\\chromedriver  (ej. {user_cd})")
    print(' 4) Ejecuta este snippet en PowerShell (como usuario) para añadir la carpeta al PATH de usuario:')
    print('\n--- PowerShell (pegar y ejecutar) ---')
    print(r"$cd = Join-Path $env:LOCALAPPDATA 'chromedriver'")
    print(r"if (-not (Test-Path $cd)) { New-Item -ItemType Directory -Path $cd -Force }")
    print(r"$old = [Environment]::GetEnvironmentVariable('Path', 'User')")
    print('''if ($old -notlike "*${cd}*") {
    [Environment]::SetEnvironmentVariable('Path', "$old;$cd", 'User');
    Write-Output "Ruta agregada al PATH de usuario: $cd"
} else {
    Write-Output "La ruta ya está en el PATH de usuario: $cd"
}''')
    print(r"Write-Output 'Reinicia la terminal o la sesión para que los cambios surtan efecto.'")
    print('--- Fin snippet ---\n')
    print('También puedes ver instrucciones más detalladas en `docs/USO.md`.')

def main():
    parser = argparse.ArgumentParser(
        description="Selector de ejecución para ClicToriano (elige CLI o GUI).",
        epilog="Si no se pasan opciones, se muestra un menú interactivo."
    )
    parser.add_argument('--cli', action='store_true', help='Ejecutar el script CLI (no interactivo)')
    parser.add_argument('--gui', action='store_true', help='Ejecutar el script GUI (no interactivo)')
    parser.add_argument('--url', help='URL a pasar al script CLI (cuando corresponda)')
    parser.add_argument('--link-wait', type=int, help='Tiempo (s) para pasar como --link-wait al script CLI')
    parser.add_argument('--install-chromedriver', action='store_true', help='Intentar descargar e instalar ChromeDriver (compatibilidad)')
    parser.add_argument('--install-webdriver', action='store_true', help='Intentar descargar e instalar el webdriver adecuado (chrome|firefox)')
    parser.add_argument('--browser', choices=['chrome', 'chromium', 'firefox'], help='Navegador a usar para el script (chrome|chromium|firefox)')
    args = parser.parse_args()

    scripts = obtener_scripts()

    # Si el usuario pidió intentar instalar webdrivers, manejarlo y salir
    if args.install_chromedriver or args.install_webdriver:
        target_browser = args.browser or 'chrome'
        print(f'Intentando descargar/instalar webdriver para: {target_browser}...')
        if ensure_webdriver:
            try:
                path = ensure_webdriver(target_browser)
                if path and os.path.exists(path):
                    print(f'Webdriver detectado/instalado en: {path}')
                    # Si estamos en Windows y la instalación quedó en LOCALAPPDATA, mostrar snippet de PowerShell
                    if platform.system() == 'Windows':
                        local = os.getenv('LOCALAPPDATA') or os.path.expanduser('~\\AppData\\Local')
                        if str(path).lower().startswith(str(local).lower()):
                            snippet = (
                                "$cd = Join-Path $env:LOCALAPPDATA 'webdrivers'\n"
                                "if (-not (Test-Path $cd)) { New-Item -ItemType Directory -Path $cd -Force }\n"
                                "$old = [Environment]::GetEnvironmentVariable('Path', 'User')\n"
                                "if ($old -notlike \"*$cd*\") {\n"
                                "    [Environment]::SetEnvironmentVariable('Path', \"$old;$cd\", 'User')\n"
                                "    Write-Output \"Ruta agregada al PATH de usuario: $cd\"\n"
                                "} else {\n"
                                "    Write-Output \"La ruta ya está en el PATH de usuario: $cd\"\n"
                                "}\n"
                                "Write-Output 'Reinicia la terminal o la sesión para que los cambios surtan efecto.'\n"
                            )
                            print('\nEjecuta en PowerShell (como usuario) para añadir la carpeta al PATH de usuario:\n')
                            print(snippet)
                    sys.exit(0)
                else:
                    print('No se pudo instalar el webdriver automáticamente. Consulta docs/USO.md para pasos manuales.')
                    sys.exit(1)
            except Exception as e:
                print(f'Error instalando webdriver: {e}')
                sys.exit(1)
        else:
            # Fallback a la implementación local (ensure_chromedriver) si existe
            if args.install_chromedriver:
                if platform.system() != 'Windows':
                    print('La opción --install-chromedriver está pensada para Windows. No se realizará ninguna acción en este SO.')
                    sys.exit(0)
                print('Intentando descargar/instalar ChromeDriver para Windows (fallback)...')
                ensure_chromedriver()
                if shutil.which('chromedriver') or os.path.exists(os.path.join(os.getenv('LOCALAPPDATA') or os.path.expanduser('~\\AppData\\Local'), 'chromedriver', 'chromedriver.exe')):
                    print('ChromeDriver detectado correctamente tras la instalación (fallback).')
                    sys.exit(0)
                else:
                    print('No se pudo instalar ChromeDriver automáticamente (fallback).')
                    sys.exit(1)
            else:
                print('No hay instalador disponible en este entorno (module webdrivers no cargado).')
                sys.exit(1)

    # Modo no interactivo: elegir por flags
    if args.cli or args.gui:
        if platform.system() == 'Windows':
            if args.cli:
                nombre_script = 'click_enlaces.bat'
            else:
                nombre_script = 'click_enlaces_gui.bat'
        else:
            if args.cli:
                nombre_script = 'click_enlaces.sh'
            else:
                nombre_script = 'click_enlaces_gui.sh'
        eleccion = None
    else:
        # Interactivo (por compatibilidad con versiones anteriores)
        print("Selecciona el script a ejecutar:")
        for clave, (desc, _) in scripts.items():
            print(f"  {clave}. {desc}")

        # Pedir elección con manejo de Ctrl+C que permite confirmar salida
        while True:
            try:
                eleccion = input("Introduce el número (por defecto 1): ").strip() or "1"
                break
            except KeyboardInterrupt:
                print()
                if _confirm_exit_prompt():
                    print("Operación cancelada por el usuario. Saliendo...")
                    sys.exit(0)
                else:
                    # Continuar el bucle y volver a pedir la entrada
                    continue
        if eleccion not in scripts:
            print("Opción no válida, terminando.")
            sys.exit(1)

        _, nombre_script = scripts[eleccion]
    ruta_script = os.path.join(os.path.dirname(__file__), nombre_script)

    if not os.path.isfile(ruta_script):
        print(f"Script no encontrado: {ruta_script}")
        sys.exit(1)

    # En Linux, antes de ejecutar el CLI, aseguramos el webdriver correspondiente
    if platform.system() != "Windows" and nombre_script == "click_enlaces.sh":
        # Usar ensure_webdriver si está disponible, sino fallback a ensure_chromedriver
        if ensure_webdriver:
            try:
                ensure_webdriver(args.browser or 'chrome')
            except Exception as e:
                print(f"Advertencia: no fue posible ejecutar ensure_webdriver: {e}")
        else:
            ensure_chromedriver()
        os.chmod(ruta_script, 0o755)
    # En Windows, si chromedriver no está presente, mostrar instrucciones rápidas
    if platform.system() == 'Windows':
        warn_windows_chromedriver_missing()

    print(f"Ejecutando {nombre_script} ...")
    try:
        # Si se va a ejecutar el script CLI (shell/batch), pedir o usar la URL proporcionada
        if nombre_script in ("click_enlaces.sh", "click_enlaces.bat"):
            if args.url:
                url = args.url
            else:
                # Si venimos del modo interactivo, el usuario ya eligió eleccion y pedimos la URL
                while True:
                    try:
                        url = input("Introduce la URL a procesar (por ejemplo https://example.com): ").strip()
                        break
                    except KeyboardInterrupt:
                        print()
                        if _confirm_exit_prompt():
                            print("Operación cancelada por el usuario. Saliendo...")
                            sys.exit(0)
                        else:
                            continue
            if not url:
                print("No se proporcionó URL. Cancelando.")
                sys.exit(1)
            # Pasar la URL como argumento al script (y opcionalmente --link-wait)
            cmd = [ruta_script, url]
            if args.link_wait is not None:
                cmd += ['--link-wait', str(args.link_wait)]
            if args.browser:
                cmd += ['--browser', args.browser]
            subprocess.run(cmd, check=True)
        else:
            subprocess.run([ruta_script], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar el script: {e}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Mensaje amigable cuando el usuario pulsa Ctrl+C
        print("\nOperación cancelada por el usuario (Ctrl+C). Saliendo...")
        try:
            sys.exit(0)
        except SystemExit:
            pass