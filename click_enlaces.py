#!/usr/bin/env python3
"""
Programa para hacer clic automático en enlaces de una página web
"""

import argparse
import time
import random
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, NoSuchElementException, StaleElementReferenceException, NoSuchWindowException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
import sys
import platform
import os
import threading
import json
from pathlib import Path

class ClicToris:
    def __init__(self, url, intervalo_min=5, intervalo_max=10, modo_headless=False, max_clicks=None, chrome_path=None, external_links_policy='new_tab', link_wait=10, browser='chrome'):
        """
        Inicializa el programa de clic automático
        
        Args:
            url (str): URL de la página a visitar
            intervalo_min (int): Tiempo mínimo en segundos entre clics
            intervalo_max (int): Tiempo máximo en segundos entre clics
            modo_headless (bool): Si True, ejecuta el navegador sin interfaz gráfica
            max_clicks (int): Número máximo de clics (None = infinito)
        """
        self.url = url
        self.intervalo_min = intervalo_min
        self.intervalo_max = intervalo_max
        self.modo_headless = modo_headless
        self.max_clicks = max_clicks
        self.driver = None
        self.enlaces_visitados = set()
        self.ventana_principal = None  # Para mantener referencia a la ventana principal
        # Lock para evitar iniciar múltiples drivers desde hilos simultáneos
        self._driver_lock = threading.Lock()
        # Extraer el dominio base de la URL inicial
        parsed_url = urlparse(url)
        self.dominio_base = f"{parsed_url.scheme}://{parsed_url.netloc}"
        # Ruta explícita opcional al binario de Chrome (puede venir por CLI o variable de entorno)
        self.chrome_path = chrome_path
        # Browser: 'chrome' | 'chromium' | 'firefox'
        self.browser = (browser or 'chrome').lower()
        # Política para manejar enlaces externos: 'new_tab' | 'same_window' | 'ignore'
        self.external_policy = external_links_policy
        # Política para hacer scroll antes de clicar: 'none'|'small'|'medium'|'full'|'random'
        self.scroll_policy = 'none'
        # Tiempo máximo (s) para esperar enlaces dinámicos tras cargar la página
        self.link_wait = link_wait

    def _apply_scroll(self, elemento, policy=None):
        """Aplica scroll según la política configurada antes de interactuar con un elemento.

        `elemento` puede ser un WebElement; si no está disponible, la función falla silenciosamente.
        """
        try:
            if not elemento:
                return
            policy = policy or getattr(self, 'scroll_policy', 'none')
            if policy == 'none':
                return
            # Registrar en logs que vamos a aplicar scroll (timestamp + policy)
            try:
                href = None
                texto = None
                try:
                    href = elemento.get_attribute('href')
                except Exception:
                    href = None
                try:
                    texto = (elemento.text or '')[:80]
                except Exception:
                    texto = ''
                ts = time.strftime('%Y-%m-%d %H:%M:%S')
                print(f"[scroll] {ts} policy={policy} href={href or '[no-href]'} text='{texto}'")
            except Exception:
                pass
            if policy == 'small':
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elemento)
                except Exception:
                    pass
            elif policy == 'medium':
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'}); window.scrollBy(0, -100);", elemento)
                except Exception:
                    pass
            elif policy == 'full':
                try:
                    # Scroll escalonado desde arriba hasta la posición del elemento
                    self.driver.execute_script(
                        "var el=arguments[0]; var top=el.getBoundingClientRect().top+window.pageYOffset; var step=Math.max(100, window.innerHeight/5); for(var y=0;y<top;y+=step){window.scrollTo(0,y);} window.scrollTo(0,top);",
                        elemento)
                except Exception:
                    pass
        except Exception:
            pass
        
    def iniciar_navegador(self):
        """Inicializa el navegador según la opción `browser` (chrome/chromium/firefox)"""
        import os
        import subprocess
        
        try:
            # Evitar que dos hilos lancen el driver simultáneamente
            with self._driver_lock:
                # Si ya tenemos un driver activo y responde, reutilizarlo (evita iniciar dos instancias)
                if getattr(self, 'driver', None):
                    try:
                        _ = self.driver.current_window_handle
                        print("✓ Navegador ya iniciado, reutilizando instancia existente")
                        return True
                    except Exception:
                        # Instancia previa invalidada: intentar cerrar y continuar
                        try:
                            self.driver.quit()
                        except Exception:
                            pass
                        self.driver = None
            # Si el usuario pidió Firefox, usar FirefoxOptions y el driver correspondiente
            if self.browser == 'firefox':
                from selenium.webdriver.firefox.options import Options as FirefoxOptions
                from selenium.webdriver.firefox.service import Service as FirefoxService
                firefox_options = FirefoxOptions()
                if self.modo_headless:
                    firefox_options.headless = True
                # Intentar localizar binario de Firefox si se indicó chrome_path o variables de entorno
                ff_env_candidates = [
                    self.chrome_path,
                    os.getenv('FIREFOX_BIN'),
                    os.getenv('FIREFOX_PATH'),
                ]
                ff_bin = next((p for p in ff_env_candidates if p), None)
                if ff_bin and os.path.isfile(ff_bin):
                    try:
                        firefox_options.binary_location = ff_bin
                        print(f"⚙️  Usando ruta de Firefox especificada: {ff_bin}")
                    except Exception:
                        pass
                try:
                    # Dejar que Selenium Manager maneje geckodriver si es necesario
                    self.driver = webdriver.Firefox(options=firefox_options)
                    print(f"✓ Firefox iniciado correctamente")
                    return True
                except Exception as e:
                    print(f"⚠️  Error iniciando Firefox: {e}")
                    raise e

            chrome_options = Options()
            if self.modo_headless:
                chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            # Si no estamos en modo headless, iniciar Chrome directamente en la URL
            # objetivo para evitar que aparezca primero una pestaña about:blank.
            if not self.modo_headless and getattr(self, 'url', None):
                try:
                    # Usar --app=<url> hace que Chrome abra directamente la URL
                    # en una ventana de aplicación, evitando about:blank inicial.
                    chrome_options.add_argument(f"--app={self.url}")
                    # marcar que arrancó con la URL para posibles ajustes posteriores
                    self._started_with_url = True
                except Exception:
                    self._started_with_url = False
            else:
                self._started_with_url = False
            # Configuración de rutas según el sistema operativo
            sistema = platform.system()

            # Función interna para validar que el binario funciona
            def _validar_binario(ruta):
                try:
                    subprocess.run([ruta, '--version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                    return True
                except Exception:
                    return False

            # Intentar usar ruta proporcionada por CLI o variables de entorno
            # Soporta varias variables de entorno comunes por compatibilidad
            revisadas = []
            env_candidates = [
                self.chrome_path,
                os.getenv('CLICTORIS_CHROME_PATH'),
                os.getenv('CHROME_BIN'),
                os.getenv('GOOGLE_CHROME_PATH'),
                os.getenv('GOOGLE_CHROME_SHIM')
            ]
            env_path = next((p for p in env_candidates if p), None)
            binary_location = None
            if env_path:
                if os.path.isfile(env_path) and os.access(env_path, os.X_OK) and _validar_binario(env_path):
                    binary_location = env_path
                    print(f"⚙️  Usando ruta de Chrome especificada por variable/argumento: {binary_location}")
                else:
                    print(f"⚠️  La ruta especificada en variable/argumento no es válida o no es ejecutable: {env_path}")
            else:
                # Lista de rutas comunes según el SO
                if sistema == "Windows":
                    # Si el usuario pidió 'chromium', priorizar rutas de Chromium
                    if self.browser == 'chromium':
                        posibles = [
                            r"C:\\Program Files\\Chromium\\Application\\chrome.exe",
                            r"C:\\Program Files (x86)\\Chromium\\Application\\chrome.exe",
                            r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                        ]
                    else:
                        posibles = [
                            r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                            r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                            os.path.expanduser(r"~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe")
                        ]
                else:
                    # En Unix-like, si el usuario pidió 'chromium' priorizar binarios de chromium
                    if self.browser == 'chromium':
                        posibles = [
                            '/usr/bin/chromium',
                            '/usr/bin/chromium-browser',
                            '/snap/bin/chromium',
                            '/usr/bin/google-chrome',
                        ]
                    else:
                        posibles = [
                            '/usr/bin/google-chrome',
                            '/opt/google/chrome/google-chrome',
                            '/usr/bin/chromium',
                            '/usr/bin/chromium-browser',
                            '/snap/bin/chromium',
                            '/usr/bin/google-chrome-stable',
                            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'  # macOS
                        ]
                # Probar y registrar el resultado de cada ruta candidata (útil para diagnóstico)
                revisadas = []
                for p in posibles:
                    ok = os.path.isfile(p) and os.access(p, os.X_OK) and _validar_binario(p)
                    revisadas.append((p, ok))
                    if ok:
                        binary_location = p
                        break

            if binary_location:
                chrome_options.binary_location = binary_location
                print(f"✓ Navegador encontrado en: {binary_location}")
            else:
                print("⚠️  No se encontró un binario de Chrome/Chromium en las rutas comunes.")
                # Mostrar lista diagnosticada de rutas comprobadas si existe
                try:
                    print("    Rutas comprobadas:")
                    for p, ok in revisadas:
                        print(f"      - {p}: {'OK' if ok else 'no encontrado / no ejecutable / sin version'}")
                except Exception:
                    pass
                print("    Intentando iniciar el navegador, confiando en Selenium Manager para encontrarlo.")

            # Intentar iniciar el driver
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                print(f"✓ Navegador iniciado correctamente")
                # Si arrancó ya con la URL no es necesario minimizar/restaurar
                try:
                    if getattr(self, '_started_with_url', False):
                        pass
                except Exception:
                    self._started_with_url = False
                return True
            except Exception as e:
                print(f"⚠️  Intento estándar fallido: {e}")
                # Fallback para Linux si ChromeDriver está en /usr/bin
                if sistema != "Windows" and os.path.exists('/usr/bin/chromedriver'):
                    print("    Intentando con ChromeDriver en /usr/bin/chromedriver...")
                    try:
                        service = Service('/usr/bin/chromedriver')
                        self.driver = webdriver.Chrome(service=service, options=chrome_options)
                        print(f"✓ Navegador iniciado correctamente con ChromeDriver en /usr/bin")
                        return True
                    except Exception as e_fallback:
                        print(f"    ✗ Fallback con ChromeDriver fallido: {e_fallback}")
                        raise e # Re-raise original exception if fallback fails
                else:
                    raise e
        except WebDriverException as e:
            print(f"✗ Error al iniciar el navegador: {e}")
            print(f"\nPosibles soluciones:")
            print(f"  1. Instalar Google Chrome: ./install_chrome.sh")
            print(f"  2. Verificar ChromeDriver: sudo apt install chromium-chromedriver")
            print(f"  3. Revisar las versiones coincidan:")
            print(f"     google-chrome --version")
            print(f"     chromedriver --version")
            return False
    
    def obtener_enlaces(self):
        """Obtiene todos los enlaces de la página actual (internos y externos)"""
        try:
            # Buscar todos los elementos <a> con atributo href
            elementos = self.driver.find_elements(By.TAG_NAME, "a")
            enlaces = []

            for elemento in elementos:
                try:
                    href = elemento.get_attribute("href")
                except Exception:
                    continue
                if href and href.startswith("http"):
                    # Verificar si el enlace es interno o externo
                    es_interno = href.startswith(self.dominio_base)
                    enlaces.append({
                        'url': href,
                        'texto': (elemento.text or '[Sin texto]')[:200],
                        'elemento': elemento,
                        'es_interno': es_interno
                    })

            return enlaces
        except (StaleElementReferenceException, WebDriverException, NoSuchWindowException) as e:
            # Errores que indican que la sesión/ventana cambió o se desconectó
            print(f"Error al obtener enlaces: {e.__class__.__name__}: {str(e)}")
            # Marcar que el driver se perdió para que el bucle principal termine
            self._driver_lost = True
            return []
        except Exception as e:
            print(f"Error al obtener enlaces: {e}")
            return []
    
    def ejecutar(self):
        """Ejecuta el programa principal"""
        if not self.iniciar_navegador():
            return
        
        try:
            # Cargar la página inicial
            print(f"\n🌐 Cargando URL: {self.url}")
            print(f"🔒 Dominio base: {self.dominio_base}")
            print(f"   • Enlaces internos: navegar en la misma pestaña")
            policy = getattr(self, 'external_policy', 'new_tab')
            policy_map = {
                'new_tab': 'abrir en nueva pestaña',
                'same_window': 'abrir en la misma ventana',
                'ignore': 'ignorar enlaces externos'
            }
            print(f"   • Enlaces externos: {policy_map.get(policy, 'abrir en nueva pestaña')}")
            # Navegar a la URL si el navegador NO arrancó ya con la URL
            # (cuando usamos --app=<url> evitamos about:blank inicial).
            if not getattr(self, '_started_with_url', False):
                self.driver.get(self.url)
            try:
                if getattr(self, '_started_offscreen', False):
                    try:
                        # Mover la ventana a posición visible y maximizar
                        try:
                            self.driver.set_window_position(50, 50)
                        except Exception:
                            pass
                        try:
                            self.driver.maximize_window()
                        except Exception:
                            pass
                    except Exception:
                        pass
            except Exception:
                pass
            time.sleep(2)  # Esperar a que cargue la página

            # Esperar activamente hasta que aparezca al menos un enlace <a> con href que empiece por http
            try:
                try:
                    WebDriverWait(self.driver, getattr(self, 'link_wait', 10), poll_frequency=0.5).until(
                        lambda d: any(((e.get_attribute('href') or '').startswith('http')) for e in d.find_elements(By.TAG_NAME, 'a'))
                    )
                except TimeoutException:
                    # Si no aparece en el tiempo dado, continuar de todos modos
                    pass
            except Exception:
                pass
            # Guardar la ventana principal
            # Si la página inicial es un `data:` o `about:blank`, reemplazarla
            try:
                url_actual = ''
                try:
                    url_actual = self.driver.current_url
                except Exception:
                    url_actual = ''

                if url_actual.startswith('data:') or url_actual in ('about:blank', ''):
                    # Intentar abrir la URL objetivo en una nueva pestaña y cerrar la ventana en blanco
                    try:
                        self.driver.execute_script(f"window.open('{self.url}', '_blank');")
                        time.sleep(0.6)
                        handles = self.driver.window_handles
                        target_handle = None
                        for h in handles:
                            try:
                                self.driver.switch_to.window(h)
                                cu = self.driver.current_url
                                if cu.startswith('http') and (urlparse(cu).netloc == urlparse(self.url).netloc or self.url in cu):
                                    target_handle = h
                                    break
                            except Exception:
                                continue

                        # Si no encontramos una pestaña coincidente, usar la última
                        if not target_handle and handles:
                            target_handle = handles[-1]

                        # Cerrar las demás ventanas (incluida la que tenía data:)
                        for h in handles:
                            if h != target_handle:
                                try:
                                    self.driver.switch_to.window(h)
                                    self.driver.close()
                                except Exception:
                                    pass

                        # Enfocar la pestaña objetivo
                        if target_handle:
                            self.driver.switch_to.window(target_handle)
                    except Exception:
                        # Fallback: navegar directamente
                        try:
                            self.driver.get(self.url)
                        except Exception:
                            pass

            except Exception:
                pass

            # Guardar la ventana principal
            try:
                self.ventana_principal = self.driver.current_window_handle
            except Exception:
                self.ventana_principal = None
            # Cerrar ventanas duplicadas que carguen la misma URL objetivo
            try:
                if self.ventana_principal:
                    handles = self.driver.window_handles
                    seen = {}
                    keep_handle = None
                    target_netloc = urlparse(self.url).netloc
                    for h in handles:
                        try:
                            self.driver.switch_to.window(h)
                            cu = ''
                            try:
                                cu = self.driver.current_url
                            except Exception:
                                cu = ''
                            # Normalizar URLs que empiezan por http
                            if cu and cu.startswith('http'):
                                netloc = urlparse(cu).netloc
                                key = netloc + '|' + cu
                                if key not in seen:
                                    seen[key] = h
                                    # Preferir ventana cuyo netloc coincida con la URL objetivo
                                    if netloc == target_netloc and not keep_handle:
                                        keep_handle = h
                                else:
                                    # Cerrar duplicado
                                    try:
                                        self.driver.close()
                                    except Exception:
                                        pass
                            else:
                                # Si la ventana no tiene URL válida, cerrarla
                                try:
                                    self.driver.close()
                                except Exception:
                                    pass
                        except Exception:
                            continue

                    # Si no elegimos una ventana para mantener, tomar la primera disponible
                    remaining = self.driver.window_handles
                    if not keep_handle and remaining:
                        keep_handle = remaining[0]

                    # Enfocar la ventana que mantuvimos
                    if keep_handle:
                        try:
                            self.driver.switch_to.window(keep_handle)
                            self.ventana_principal = keep_handle
                        except Exception:
                            pass
            except Exception:
                pass
            
            contador_clics = 0
            
            contador_clics = 0
            
            print(f"\n⏱️  Intervalo aleatorio entre clics: {self.intervalo_min} - {self.intervalo_max} segundos")
            if self.max_clicks:
                print(f"🔢 Máximo de clics: {self.max_clicks}")
            print("\n" + "="*60)
            print("Presiona Ctrl+C para detener el programa")
            print("="*60 + "\n")
            
            while True:
                # Comprueba si el driver se ha perdido (por errores previos)
                if getattr(self, '_driver_lost', False):
                    print("⚠️  La sesión del navegador se perdió. Saliendo...")
                    break
                # Verificar que queden ventanas abiertas
                try:
                    handles_check = self.driver.window_handles
                    if not handles_check:
                        print("⚠️  No quedan ventanas del navegador abiertas. Saliendo...")
                        break
                except (WebDriverException, NoSuchWindowException):
                    print("⚠️  No se puede acceder a las ventanas del navegador (conexión perdida). Saliendo...")
                    break

                # Verificar si se alcanzó el máximo de clics
                if self.max_clicks and contador_clics >= self.max_clicks:
                    print(f"\n✓ Se alcanzó el máximo de {self.max_clicks} clics")
                    break
                
                # Obtener enlaces de la página actual
                enlaces = self.obtener_enlaces()
                
                if not enlaces:
                    print("⚠️  No se encontraron enlaces en la página")
                    break
                
                # Filtrar enlaces no visitados
                enlaces_no_visitados = [e for e in enlaces if e['url'] not in self.enlaces_visitados]
                
                if not enlaces_no_visitados:
                    print("\n✓ Todos los enlaces han sido visitados")
                    print(f"Total de enlaces visitados: {len(self.enlaces_visitados)}")
                    break
                
                # Seleccionar un enlace aleatorio
                enlace = random.choice(enlaces_no_visitados)
                contador_clics += 1
                
                print(f"\n[{contador_clics}] 🖱️  Haciendo clic en:")
                print(f"    Texto: {enlace['texto'][:60]}")
                print(f"    URL: {enlace['url'][:80]}")
                
                # Marcar como visitado
                self.enlaces_visitados.add(enlace['url'])
                
                # Determinar si es interno o externo
                es_interno = enlace.get('es_interno', True)
                
                if es_interno:
                    print(f"    📍 Tipo: Enlace INTERNO (mismo dominio)")
                else:
                    print(f"    🌍 Tipo: Enlace EXTERNO (otro dominio)")
                
                # Hacer clic
                try:
                    if es_interno:
                        # Enlaces internos: navegar normalmente
                        try:
                            # Intentar desplazar hasta el elemento antes de navegar
                            try:
                                policy_to_apply = self.scroll_policy
                                if policy_to_apply == 'random':
                                    policy_to_apply = random.choice(['none', 'small', 'medium', 'full'])
                                # Informar qué política se eligió (aparece en la GUI/log)
                                try:
                                    print(f"    🔽 Scroll elegido: {policy_to_apply}")
                                except Exception:
                                    pass
                                self._apply_scroll(enlace.get('elemento'), policy=policy_to_apply)
                            except Exception:
                                pass
                        except Exception:
                            pass
                        self.driver.get(enlace['url'])
                        print(f"    ✓ Página cargada correctamente")
                    else:
                        # Enlaces externos: comportamientos según la política de usuario
                        if self.external_policy == 'ignore':
                            print(f"    ⚠️ Enlace externo ignorado por configuración")
                        elif self.external_policy == 'same_window':
                            try:
                                # No aplicar scroll para dominios externos (solo se aplica en enlaces internos)
                                self.driver.get(enlace['url'])
                                print(f"    ✓ Página externa cargada en la misma ventana")
                            except Exception as e:
                                print(f"    ✗ Error al cargar en la misma ventana: {e}")
                                # Si hay problema con la sesión, marcar pérdida
                                if isinstance(e, WebDriverException):
                                    self._driver_lost = True
                                    break
                        else:
                            # default/new_tab: abrir en nueva pestaña
                            try:
                                # No aplicar scroll para dominios externos (solo se aplica en enlaces internos)
                                self.driver.execute_script(f"window.open('{enlace['url']}', '_blank');")
                                print(f"    ✓ Enlace abierto en nueva pestaña")
                                # Esperar un momento para que se abra la pestaña
                                time.sleep(1)
                                # Cerrar cualquier pestaña que no sea la principal
                                ventanas = self.driver.window_handles
                                for ventana in ventanas:
                                    if ventana != self.ventana_principal:
                                        try:
                                            self.driver.switch_to.window(ventana)
                                            self.driver.close()
                                        except Exception:
                                            pass
                                # Volver a la ventana principal
                                try:
                                    self.driver.switch_to.window(self.ventana_principal)
                                except Exception:
                                    pass
                                print(f"    ↩️  Foco devuelto a la página principal")
                            except Exception as e:
                                print(f"    ✗ Error al abrir en nueva pestaña: {e}")
                                if isinstance(e, WebDriverException):
                                    self._driver_lost = True
                                    break
                        
                except Exception as e:
                    print(f"    ✗ Error al cargar la página: {e}")
                
                # Esperar un intervalo aleatorio
                tiempo_espera = random.uniform(self.intervalo_min, self.intervalo_max)
                print(f"    ⏳ Esperando {tiempo_espera:.1f} segundos (aleatorio entre {self.intervalo_min}-{self.intervalo_max})...")
                time.sleep(tiempo_espera)
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Programa interrumpido por el usuario")
            print(f"Total de clics realizados: {contador_clics}")
            print(f"Total de enlaces visitados: {len(self.enlaces_visitados)}")
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
                finally:
                    self.driver = None
                print("\n✓ Navegador cerrado\n")


def main():
    parser = argparse.ArgumentParser(
        description='Programa para hacer clic automático en enlaces de una página web',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s https://example.com
  %(prog)s https://example.com --min 5 --max 15
  %(prog)s https://example.com --min 2 --max 5 --headless
  %(prog)s https://example.com --max-clicks 20
        """
    )

    parser.add_argument(
        'url',
        help='URL de la página web a visitar'
    )

    parser.add_argument(
        '--min',
        type=int,
        default=5,
        help='Tiempo mínimo en segundos entre clics (default: 5)'
    )

    parser.add_argument(
        '--max',
        type=int,
        default=10,
        help='Tiempo máximo en segundos entre clics (default: 10)'
    )

    # Mantener compatibilidad con -i (usará ese valor como min y max)
    parser.add_argument(
        '-i', '--intervalo',
        type=int,
        help='Intervalo fijo (sobreescribe min/max)'
    )

    parser.add_argument(
        '--headless',
        action='store_true',
        help='Ejecutar el navegador en modo headless (sin interfaz gráfica)'
    )

    parser.add_argument(
        '--max-clicks',
        type=int,
        default=None,
        help='Número máximo de clics a realizar (default: infinito)'
    )

    parser.add_argument(
        '--chrome-path',
        dest='chrome_path',
        help='Ruta al binario de Chrome/Chromium (por ejemplo /usr/bin/google-chrome). Puede usarse en lugar de variables de entorno.'
    )

    parser.add_argument(
        '--external-policy',
        dest='external_policy',
        choices=['new_tab', 'same_window', 'ignore'],
        help="Política para enlaces externos: 'new_tab' (por defecto), 'same_window' o 'ignore'"
    )

    parser.add_argument(
        '--scroll-policy',
        dest='scroll_policy',
        choices=['none', 'small', 'medium', 'full', 'random'],
        help="Política de scroll antes de clicar: 'none','small','medium','full' o 'random' (elige una al azar antes de cada clic)"
    )

    parser.add_argument(
        '--link-wait',
        dest='link_wait',
        type=int,
        help='Tiempo máximo (segundos) a esperar para que aparezcan enlaces dinámicos tras la carga (default: 10)'
    )

    parser.add_argument(
        '--browser',
        dest='browser',
        choices=['chrome', 'chromium', 'firefox'],
        default='chrome',
        help='Navegador a usar: chrome (por defecto), chromium o firefox'
    )

    args = parser.parse_args()

    # Validar la URL
    if not args.url.startswith('http'):
        print("Error: La URL debe comenzar con http:// o https://")
        sys.exit(1)

    # Gestionar intervalos
    intervalo_min = args.min
    intervalo_max = args.max

    if args.intervalo:
        intervalo_min = args.intervalo
        intervalo_max = args.intervalo

    if intervalo_min < 1:
        print("Error: El intervalo mínimo debe ser al menos 1 segundo")
        sys.exit(1)

    if intervalo_max < intervalo_min:
        print(f"Error: El máximo ({intervalo_max}) no puede ser menor que el mínimo ({intervalo_min})")
        sys.exit(1)

    # Leer configuración persistente si existe (solo para opciones no proporcionadas por CLI)
    config_path = Path.home() / '.clictoriano' / 'config.json'
    config = {}
    try:
        if config_path.exists():
            with config_path.open('r', encoding='utf-8') as f:
                config = json.load(f)
    except Exception:
        config = {}

    # Determinar política externa: prioridad CLI > config > default
    policy = args.external_policy or config.get('external_policy', 'new_tab')
    scroll_policy = args.scroll_policy or config.get('scroll_policy', 'none')
    link_wait = args.link_wait if args.link_wait is not None else config.get('link_wait', 10)

    # Crear y ejecutar el programa
    programa = ClicToris(
        url=args.url,
        intervalo_min=intervalo_min,
        intervalo_max=intervalo_max,
        modo_headless=args.headless,
        max_clicks=args.max_clicks,
        chrome_path=args.chrome_path,
        external_links_policy=policy,
        link_wait=link_wait,
        browser=args.browser,
    )
    # Aplicar política de scroll seleccionada
    try:
        programa.scroll_policy = scroll_policy
    except Exception:
        pass
    
    programa.ejecutar()


if __name__ == "__main__":
    main()
