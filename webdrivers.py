#!/usr/bin/env python3
"""
Módulo para gestionar la instalación de webdrivers (ChromeDriver y GeckoDriver).

Función principal:
- ensure_webdriver(browser: str, install_dir: Optional[str]=None) -> str

El instalador intenta (en este orden):
1. Detectar si el webdriver ya existe en PATH (shutil.which).
2. Intentar usar la versión adecuada descargando desde los repositorios oficiales
   (Chromedriver: chromedriver.storage.googleapis.com, Geckodriver: GitHub releases).
3. Instalar en un directorio de usuario en Windows (sin elevación) o en
   `/usr/local/bin` cuando sea posible. Si `/usr/local/bin` no es escribible,
   usa `~/.local/bin`.

Este módulo no requiere dependencias extra (usa urllib, zipfile, tarfile).
"""

from __future__ import annotations

import os
import sys
import stat
import json
import shutil
import platform
import tempfile
import urllib.request
import urllib.error
import zipfile
import tarfile
import subprocess
from pathlib import Path
from typing import Optional, Callable

__all__ = ["ensure_webdriver"]


def _is_executable(path: Path) -> bool:
    return path.exists() and os.access(str(path), os.X_OK)


def _which(name: str) -> Optional[str]:
    return shutil.which(name)


def _download_url(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "clictoriano-webdriver-installer/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        with open(dest, "wb") as fh:
            fh.write(resp.read())


def _download_url_with_progress(url: str, dest: Path, progress_callback: Optional[Callable[[int, Optional[int]], None]] = None) -> None:
    """Descarga `url` a `dest`, llamando a `progress_callback(bytes_downloaded, total_bytes)` si se proporciona.
    total_bytes puede ser None si el servidor no proporciona Content-Length.
    """
    req = urllib.request.Request(url, headers={"User-Agent": "clictoriano-webdriver-installer/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        total = None
        try:
            cl = resp.getheader('Content-Length')
            if cl:
                total = int(cl)
        except Exception:
            total = None

        chunk_size = 32 * 1024
        downloaded = 0
        with open(dest, 'wb') as fh:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                fh.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    try:
                        progress_callback(downloaded, total)
                    except Exception:
                        # No queremos que un error en el callback interrumpa la descarga
                        pass


def _extract_archive(archive: Path, dest_dir: Path) -> Path:
    """Extrae zip o tar.gz y devuelve la ruta del binario extraído (el primero que parezca un driver)."""
    extracted = None
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive, "r") as z:
            z.extractall(path=dest_dir)
            for name in z.namelist():
                base = Path(name).name
                if base.lower().startswith(("chromedriver", "geckodriver")):
                    extracted = dest_dir / base
                    break
    else:
        # tar.gz or .tar.bz2
        with tarfile.open(archive, "r:*") as t:
            t.extractall(path=dest_dir)
            for member in t.getmembers():
                base = Path(member.name).name
                if base.lower().startswith(("chromedriver", "geckodriver")):
                    extracted = dest_dir / base
                    break

    if not extracted:
        # fallback: pick any executable file in dest_dir
        for p in dest_dir.rglob("*"):
            if p.is_file() and os.access(str(p), os.X_OK):
                extracted = p
                break

    if not extracted:
        raise RuntimeError(f"No se encontró binario después de extraer {archive}")

    return extracted


def _make_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _get_chrome_binary_candidates() -> list[str]:
    candidates = []
    system = platform.system()
    if system == 'Windows':
        candidates += [
            os.path.join(os.environ.get('PROGRAMFILES', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
        ]
        # Chromium
        candidates += [
            os.path.join(os.environ.get('PROGRAMFILES', ''), 'Chromium', 'Application', 'chrome.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Chromium', 'Application', 'chrome.exe'),
        ]
    else:
        candidates += [
            '/usr/bin/google-chrome',
            '/usr/bin/chrome',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
            '/snap/bin/chromium',
        ]
    return candidates


def _get_firefox_binary_candidates() -> list[str]:
    candidates = []
    system = platform.system()
    if system == 'Windows':
        candidates += [
            os.path.join(os.environ.get('PROGRAMFILES', ''), 'Mozilla Firefox', 'firefox.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Mozilla Firefox', 'firefox.exe'),
        ]
    else:
        candidates += ['/usr/bin/firefox', '/snap/bin/firefox']
    return candidates


def _get_version_from_binary(path: str) -> Optional[str]:
    try:
        proc = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=10)
        out = proc.stdout.strip() or proc.stderr.strip()
        if out:
            # ejemplos: "Google Chrome 117.0.5938.132" o "Firefox 121.0"
            parts = out.strip().split()
            for part in parts[::-1]:
                if any(c.isdigit() for c in part):
                    return part
        return None
    except Exception:
        return None


def ensure_webdriver(browser: str = 'chrome', install_dir: Optional[str] = None, quiet: bool = False, force_install: bool = False,
                     progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
                     status_callback: Optional[Callable[[str, Optional[object]], None]] = None) -> str:
    """
    Asegura que el webdriver para `browser` esté instalado y devuelve la ruta al ejecutable.

    browser: 'chrome'|'chromium'|'firefox'
    install_dir: directorio destino opcional. Si None, elegirá un directorio adecuado.
    """
    browser = (browser or 'chrome').lower()

    # 1) Verificar si ya existe en PATH (a menos que se fuerce la instalación)
    name = 'chromedriver' if browser in ('chrome', 'chromium') else 'geckodriver'
    existing = _which(name)
    if existing and not force_install:
        if not quiet:
            print(f"webdriver ya en PATH: {existing}")
        return existing

    system = platform.system()

    # Determinar directorio de instalación preferido
    if install_dir:
        out_dir = Path(install_dir).expanduser()
    else:
        if system == 'Windows':
            out_dir = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / 'webdrivers'
        else:
            # Preferir /usr/local/bin si es escribible
            maybe = Path('/usr/local/bin')
            if maybe.exists() and os.access(str(maybe), os.W_OK):
                out_dir = maybe
            else:
                out_dir = Path.home() / '.local' / 'bin'

    out_dir.mkdir(parents=True, exist_ok=True)

    tmp = Path(tempfile.mkdtemp(prefix='clicdrv_'))
    try:
        if browser in ('chrome', 'chromium'):
            # Intentar detectar Chrome/Chromium para hallar la versión
            chrome_path = None
            for cand in _get_chrome_binary_candidates():
                if cand and Path(cand).exists():
                    chrome_path = cand
                    break

            version = None
            if chrome_path:
                version = _get_version_from_binary(chrome_path)
            if version:
                major = version.split('.')[0]
                # Obtener versión exacta de chromedriver para el major
                url_latest = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major}"
            else:
                # fallback a última versión
                url_latest = "https://chromedriver.storage.googleapis.com/LATEST_RELEASE"

            try:
                req = urllib.request.Request(url_latest, headers={"User-Agent": "clictoriano-installer/1.0"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    chromedriver_version = r.read().decode().strip()
            except Exception as e:
                raise RuntimeError(f"No se pudo obtener versión de chromedriver: {e}")

            # determinar sufijo de plataforma
            machine = platform.machine().lower()
            if system == 'Windows':
                plat = 'win32'
                archive_name = f"chromedriver_{plat}.zip"
            elif system == 'Linux':
                plat = 'linux64'
                archive_name = f"chromedriver_{plat}.zip"
            elif system == 'Darwin':
                if machine in ('arm64', 'aarch64'):
                    plat = 'mac_arm64'
                    # Algunos empaquetados usan mac64_m1, intentar ambos
                    archive_name = f"chromedriver_mac_arm64.zip"
                else:
                    plat = 'mac64'
                    archive_name = f"chromedriver_{plat}.zip"
            else:
                raise RuntimeError(f"OS no soportado para chromedriver: {system}")

            download_url = f"https://chromedriver.storage.googleapis.com/{chromedriver_version}/{archive_name}"
            archive_path = tmp / archive_name
            if not quiet:
                print(f"Descargando chromedriver {chromedriver_version} desde {download_url}")
            try:
                if status_callback:
                    try:
                        status_callback('download_start', {'url': download_url, 'archive': archive_name, 'version': chromedriver_version})
                    except Exception:
                        pass
                if progress_callback:
                    _download_url_with_progress(download_url, archive_path, progress_callback)
                else:
                    _download_url(download_url, archive_path)
            except urllib.error.HTTPError as e:
                # algunos nombres de archivo para mac pueden variar, intentar alternativa
                if system == 'Darwin':
                    alt = tmp / 'chromedriver_mac64.zip'
                    try:
                        _download_url(f"https://chromedriver.storage.googleapis.com/{chromedriver_version}/chromedriver_mac64.zip", alt)
                        archive_path = alt
                    except Exception:
                        raise
                else:
                    raise

            extracted = _extract_archive(archive_path, tmp)
            target = out_dir / ('chromedriver.exe' if system == 'Windows' else 'chromedriver')
            shutil.move(str(extracted), str(target))
            _make_executable(target)

            if not quiet:
                print(f"chromedriver instalado en: {target}")
            # Si estamos en Windows, mostrar snippet de PowerShell para añadir al PATH de usuario
            if system == 'Windows' and not quiet:
                p = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / 'webdrivers'
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
                print('\nPara usar el webdriver desde nuevas terminales en Windows, ejecuta este snippet en PowerShell (como usuario):\n')
                print(snippet)
            return str(target)

        elif browser == 'firefox':
            # Obtener última release de geckodriver desde GitHub
            api_url = 'https://api.github.com/repos/mozilla/geckodriver/releases/latest'
            req = urllib.request.Request(api_url, headers={"User-Agent": "clictoriano-installer/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)

            assets = data.get('assets', [])
            chosen_asset = None
            # Construir lista de tokens según la arquitectura para seleccionar el asset más apropiado
            machine = platform.machine().lower()
            arch_tokens = []
            if machine in ('x86_64', 'amd64'):
                arch_tokens = ['x86_64', 'amd64', 'linux64', 'linux64.tar.gz']
            elif machine in ('aarch64', 'arm64'):
                arch_tokens = ['aarch64', 'arm64', 'arm64.tar.gz']
            elif machine.startswith('arm') or 'arm' in machine:
                arch_tokens = ['armv7', 'armv7l', 'arm']
            elif machine in ('i386', 'i686'):
                arch_tokens = ['i386', 'i686']
            else:
                arch_tokens = [machine]

            # Prefer assets que incluyan el SO y uno de los arch_tokens
            def score_asset(name: str) -> int:
                s = 0
                nl = name.lower()
                if system == 'Windows' and ('win' in nl or nl.endswith('.zip')):
                    s += 4
                if system == 'Linux' and ('linux' in nl or nl.endswith('.tar.gz')):
                    s += 4
                if system == 'Darwin' and ('mac' in nl or 'macos' in nl or nl.endswith('.zip') or nl.endswith('.tar.gz')):
                    s += 4
                for t in arch_tokens:
                    if t in nl:
                        s += 8
                return s

            scored = []
            for asset in assets:
                name = asset.get('name', '')
                scored.append((score_asset(name), asset))
            scored.sort(key=lambda x: x[0], reverse=True)

            # Tomar el asset con mayor puntuación si tiene puntuación positiva
            if scored and scored[0][0] > 0:
                chosen_asset = scored[0][1]
            else:
                # último recurso: buscar cualquier asset que parezca tar.gz/zip y que incluya el OS name
                for asset in assets:
                    name = asset.get('name', '').lower()
                    if (system == 'Windows' and name.endswith('.zip')) or (system == 'Linux' and name.endswith('.tar.gz')) or (system == 'Darwin' and (name.endswith('.tar.gz') or name.endswith('.zip'))):
                        chosen_asset = asset
                        break

            if not chosen_asset:
                raise RuntimeError('No se encontró asset apropiado para geckodriver en la última release (assets disponibles: %s)' % ','.join([a.get('name','') for a in assets]))

            download_url = chosen_asset.get('browser_download_url')
            archive_name = Path(chosen_asset.get('name')).name
            archive_path = tmp / archive_name
            if status_callback:
                try:
                    status_callback('download_start', {'url': download_url, 'archive': archive_name})
                except Exception:
                    pass
            if progress_callback:
                _download_url_with_progress(download_url, archive_path, progress_callback)
            else:
                _download_url(download_url, archive_path)
            extracted = _extract_archive(archive_path, tmp)
            target = out_dir / ('geckodriver.exe' if system == 'Windows' else 'geckodriver')
            shutil.move(str(extracted), str(target))
            _make_executable(target)

            # Probar el binario resultante para detectar problemas de formato (p.ej. Exec format error)
            try:
                proc = subprocess.run([str(target), '--version'], capture_output=True, text=True, timeout=8)
                if proc.returncode != 0 and not proc.stdout and not proc.stderr:
                    # No salió información, posible formato erróneo
                    raise OSError('binary did not produce version output')
            except OSError as oe:
                # Exec format error o similar: intentar detectar otro asset posible
                # Borrar el binario inválido
                try:
                    target.unlink()
                except Exception:
                    pass
                # Buscar siguiente asset candidato distinto del elegido
                tried = {chosen_asset.get('name')}
                found_working = False
                for score, asset in scored[1:]:
                    aname = asset.get('name')
                    if aname in tried:
                        continue
                    tried.add(aname)
                    alt_url = asset.get('browser_download_url')
                    alt_archive = tmp / Path(aname).name
                    try:
                        if progress_callback:
                            _download_url_with_progress(alt_url, alt_archive, progress_callback)
                        else:
                            _download_url(alt_url, alt_archive)
                        alt_extracted = _extract_archive(alt_archive, tmp)
                        shutil.move(str(alt_extracted), str(target))
                        _make_executable(target)
                        # Probar de nuevo
                        proc = subprocess.run([str(target), '--version'], capture_output=True, text=True, timeout=8)
                        if proc.returncode == 0 or proc.stdout or proc.stderr:
                            found_working = True
                            if not quiet:
                                print(f"geckodriver instalado en: {target} (asset: {aname})")
                            break
                    except Exception:
                        try:
                            if target.exists():
                                target.unlink()
                        except Exception:
                            pass
                        continue

                if not found_working:
                    raise RuntimeError(f'El binario geckodriver descargado no es ejecutable para esta máquina ({machine}). Intenta descargar manualmente una versión compatible.')

            else:
                if not quiet:
                    print(f"geckodriver instalado en: {target}")
            if system == 'Windows' and not quiet:
                p = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / 'webdrivers'
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
                print('\nPara usar el webdriver desde nuevas terminales en Windows, ejecuta este snippet en PowerShell (como usuario):\n')
                print(snippet)
            return str(target)

        else:
            raise ValueError('Browser no soportado: ' + str(browser))

    finally:
        try:
            shutil.rmtree(tmp)
        except Exception:
            pass


if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser(description='Instalador unificado de webdrivers (ChromeDriver/GeckoDriver)')
    p.add_argument('--browser', choices=['chrome', 'chromium', 'firefox'], default='chrome')
    p.add_argument('--install-dir', help='Directorio de instalación (opcional)')
    p.add_argument('--quiet', action='store_true')
    args = p.parse_args()
    try:
        path = ensure_webdriver(args.browser, install_dir=args.install_dir, quiet=args.quiet)
        print(path)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
