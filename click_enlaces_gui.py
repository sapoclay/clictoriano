#!/usr/bin/env python3
"""
Interfaz Gráfica Moderna para ClicToriano usando CustomTkinter
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import sys
import os
import webbrowser
from PIL import Image
from io import StringIO
from click_enlaces import ClicToris
import json
from pathlib import Path

# Configuración inicial de CustomTkinter
ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class ClicTorisGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana principal
        self.title("ClicToriano - Navegación Automática")
        self.geometry("900x750")
        self.resizable(True, True)
        
        # Crear menú superior
        self.crear_menu()
        
        # Variable para controlar el programa
        self.programa_activo = False
        self.thread_programa = None
        self.programa = None
        # Política por defecto para enlaces externos: 'new_tab' | 'same_window' | 'ignore'
        self.external_policy = 'new_tab'
        # Política por defecto para scroll antes de clicar: 'none'|'small'|'medium'|'full'
        self.scroll_policy = 'none'
        # Navegador por defecto: 'chrome' | 'chromium' | 'firefox'
        self.browser = 'chrome'
        # Intentar cargar preferencia persistente
        try:
            cfg_file = Path.home() / '.clictoriano' / 'config.json'
            if cfg_file.exists():
                with cfg_file.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                    p = data.get('external_policy')
                    if p in ('new_tab', 'same_window', 'ignore'):
                        self.external_policy = p
                    sp = data.get('scroll_policy')
                    if sp in ('none', 'small', 'medium', 'full', 'random'):
                        self.scroll_policy = sp
                    # Cargar preferencia de navegador si existe
                    b = data.get('browser')
                    if b in ('chrome', 'chromium', 'firefox'):
                        self.browser = b
        except Exception:
            pass
        
        # Grid layout 1x2
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Crear panel lateral de navegación/configuración
        self.crear_panel_lateral()
        
        # Crear área principal
        self.crear_area_principal()
        
        # Centrar ventana
        self.centrar_ventana()

    def crear_menu(self):
        """Crea la barra de menú superior"""
        menu_bar = tk.Menu(self)
        
        # Menú Archivo
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Salir", command=self.quit)
        menu_bar.add_cascade(label="Archivo", menu=file_menu)
        
        # Menú Preferencias
        pref_menu = tk.Menu(menu_bar, tearoff=0)
        pref_menu.add_command(label="Configuración", command=self.mostrar_configuracion)
        pref_menu.add_command(label="Documentación", command=self.mostrar_documentacion)
        pref_menu.add_command(label="About", command=self.mostrar_about)
        menu_bar.add_cascade(label="Preferencias", menu=pref_menu)
        
        self.config(menu=menu_bar)

    def mostrar_about(self):
        """Muestra la ventana About"""
        about_window = ctk.CTkToplevel(self)
        about_window.title("About ClicToriano")
        about_window.geometry("400x450")
        about_window.resizable(False, False)
        
        # Hacer que sea modal
        about_window.transient(self)
        about_window.grab_set()
        
        # Centrar sobre la ventana principal
        x = self.winfo_x() + (self.winfo_width() // 2) - 200
        y = self.winfo_y() + (self.winfo_height() // 2) - 225
        about_window.geometry(f"+{x}+{y}")
        
        # Cargar logo
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "img", "logo.png")
            if os.path.exists(logo_path):
                img = ctk.CTkImage(light_image=Image.open(logo_path),
                                 dark_image=Image.open(logo_path),
                                 size=(100, 100))
                logo_label = ctk.CTkLabel(about_window, image=img, text="")
                logo_label.pack(pady=(30, 10))
        except Exception as e:
            print(f"Error cargando logo: {e}")
            
        # Versión
        ctk.CTkLabel(about_window, text="v1.0", 
               font=ctk.CTkFont(size=12)).pack(pady=(10, 20))
        
        # Descripción
        desc = ("Herramienta de automatización para navegación web.\n"
               "Realiza clics automáticos en enlaces internos,\n"
               "respetando el dominio y gestionando pestañas\n"
               "para enlaces externos.")
        ctk.CTkLabel(about_window, text=desc, justify="center").pack(pady=10)
        
        # Botón GitHub
        github_btn = ctk.CTkButton(about_window, text="Ver en GitHub",
                     command=self.abrir_github,
                     fg_color="#24292e", hover_color="#1b1f23")
        github_btn.pack(pady=30)
        
        # Botón Cerrar
        ctk.CTkButton(about_window, text="Cerrar",
                    command=about_window.destroy,
                    fg_color="transparent", border_width=1,
                    text_color=("gray10", "#DCE4EE")).pack(pady=10)

    def mostrar_documentacion(self):
        """Muestra la documentación de las opciones del programa."""
        doc = ctk.CTkToplevel(self)
        doc.title("Documentación - ClicToriano")
        doc.geometry("700x520")
        doc.resizable(True, True)
        doc.transient(self)
        doc.grab_set()

        # Centrar
        x = self.winfo_x() + (self.winfo_width() // 2) - 350
        y = self.winfo_y() + (self.winfo_height() // 2) - 260
        doc.geometry(f"+{x}+{y}")

        # Intentar cargar la documentación desde el archivo docs/USO.md si está disponible
        texto = None
        try:
            base_dir = os.path.dirname(__file__)
            candidates = [
                os.path.join(base_dir, 'docs', 'USO.md'),
                os.path.join(base_dir, 'USO.md')
            ]
            for cand in candidates:
                if os.path.exists(cand):
                    try:
                        with open(cand, 'r', encoding='utf-8') as fh:
                            texto = fh.read()
                            break
                    except Exception:
                        texto = None
        except Exception:
            texto = None

        if not texto:
            texto = (
                "Documentación de ClicToriano\n\n"
                "Resumen: Esta herramienta automatiza clics en enlaces de una página web.\n\n"
                "Opciones principales:\n"
                " - URL Objetivo: La página inicial donde se buscan enlaces. Debe comenzar con http:// o https://.\n"
                " - Intervalo Mínimo / Máximo: Tiempo aleatorio entre clics en segundos.\n"
                " - Máximo de clics: Límite de clics antes de detenerse.\n"
                " - Modo Headless: Ejecuta Chrome sin interfaz gráfica (útil en servidores).\n\n"
                "Política para enlaces externos (Preferencias -> Configuración):\n"
                " - Abrir en nueva pestaña/ventana (new_tab): abre enlaces que apuntan a otro dominio en una nueva pestaña.\n"
                " - Abrir en la misma ventana (same_window): navega al enlace externo en la misma pestaña.\n"
                " - Ignorar enlaces externos (ignore): no seguirá enlaces que vayan a otros dominios.\n\n"
                "Política de Scroll antes de clicar (Preferencias -> Configuración):\n"
                " - Sin desplazamiento (none): no se hace scroll antes de clicar.\n"
                " - Desplazamiento pequeño (small): centra el enlace en pantalla.\n"
                " - Desplazamiento medio (medium): centra y ajusta un poco hacia arriba.\n"
                " - Desplazamiento completo (full): realiza un desplazamiento escalonado hasta la posición del enlace.\n"
                " - Aleatorio (random): antes de CADA clic se selecciona aleatoriamente entre none/small/medium/full; el log mostrará la política elegida.\n\n"
                "Espera de enlaces dinámicos (--link-wait):\n"
                " - Cuando una página añade enlaces dinámicamente tras la carga, esta opción indica cuánto tiempo (s) esperar activamente para que aparezcan enlaces antes de continuar.\n\n"
                "Configuración persistente: Las preferencias de 'external_policy' y 'scroll_policy' se guardan en ~/.clictoriano/config.json.\n\n"
                "Registro de actividad: El programa imprime líneas en formato legible en la consola (o en la caja de log GUI).\n"
                "Ejemplo de línea de auditoría de scroll: [scroll] 2025-11-26 20:06:48 policy=medium href=... text='...'.\n\n"
                "Consejos de uso:\n"
                " - Prueba con --link-wait pequeño (p.ej. 3-5s) si los enlaces se cargan rápido.\n"
                " - Usa headless en servidores o para ejecución silenciosa.\n"
                " - Si el navegador no arranca, consulta install_chrome.sh y la verificación de chromedriver.\n"
            )

        # Asegurar que la documentación muestre la versión v1.0 al principio
        if texto and not texto.strip().startswith('v1.0'):
            texto = 'v1.0\n\n' + texto

        txt = ctk.CTkTextbox(doc, width=660, height=420, font=("Consolas", 11))
        txt.pack(padx=12, pady=12, fill="both", expand=True)
        txt.insert("0.0", texto)
        txt.configure(state="disabled")

        btn = ctk.CTkButton(doc, text="Cerrar", command=doc.destroy)
        btn.pack(pady=(0,12))

    def update_scroll_status_label(self, text: str | None = None):
        """Actualiza la etiqueta de estado del scroll.

        - Si `text` se pasa, lo usa como texto (por ejemplo "Scroll elegido: medium").
        - El color de fondo indica si la política configurada es `random` (amarillo) o no (transparente).
        """
        try:
            # Determinar color según la política configurada (self.scroll_policy)
            if getattr(self, 'scroll_policy', None) == 'random':
                fg = '#F1C40F'  # amarillo suave
                txt_color = '#000000'
            else:
                fg = 'transparent'
                txt_color = 'gray'

            display_text = text if text is not None else f"Scroll: {getattr(self, 'scroll_policy', 'none')}"
            try:
                self.scroll_status_label.configure(text=display_text, fg_color=fg, text_color=txt_color)
            except Exception:
                # Algunos temas/versión de CTk pueden no aceptar fg_color en CTkLabel; intentar sólo texto
                try:
                    self.scroll_status_label.configure(text=display_text)
                except Exception:
                    pass
        except Exception:
            pass

    def mostrar_configuracion(self):
        """Muestra la ventana de configuración donde el usuario elige cómo tratar enlaces externos"""
        cfg = ctk.CTkToplevel(self)
        cfg.title("Configuración")
        # Ventana más grande para mostrar todas las opciones (incluido selector de navegador)
        cfg.geometry("520x320")
        cfg.resizable(True, True)
        cfg.transient(self)
        cfg.grab_set()

        # Centrar dialog
        x = self.winfo_x() + (self.winfo_width() // 2) - 260
        y = self.winfo_y() + (self.winfo_height() // 2) - 160
        cfg.geometry(f"+{x}+{y}")

        ctk.CTkLabel(cfg, text="Comportamiento para enlaces externos:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(16,8))

        # Mapa de opciones (texto -> valor interno)
        options = {
            "Abrir en nueva pestaña/ventana": 'new_tab',
            "Abrir en la misma ventana": 'same_window',
            "Ignorar enlaces externos": 'ignore'
        }

        # Valor actual
        current_label = None
        for k,v in options.items():
            if v == self.external_policy:
                current_label = k
                break
        if not current_label:
            current_label = list(options.keys())[0]

        opt = ctk.CTkOptionMenu(cfg, values=list(options.keys()))
        opt.pack(pady=(0,12))
        try:
            opt.set(current_label)
        except Exception:
            pass

        # --- Opciones de Scroll antes de clicar ---
        ctk.CTkLabel(cfg, text="Scroll vertical antes de clicar:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(6,6))
        scroll_options = {
            "Sin desplazamiento": 'none',
            "Desplazamiento pequeño": 'small',
            "Desplazamiento medio": 'medium',
            "Desplazamiento completo": 'full',
            "Aleatorio (random)": 'random'
        }
        # Determinar etiqueta actual
        current_scroll_label = None
        for k, v in scroll_options.items():
            if v == self.scroll_policy:
                current_scroll_label = k
                break
        if not current_scroll_label:
            current_scroll_label = list(scroll_options.keys())[0]

        scroll_opt = ctk.CTkOptionMenu(cfg, values=list(scroll_options.keys()))
        scroll_opt.pack(pady=(0,12))
        try:
            scroll_opt.set(current_scroll_label)
        except Exception:
            pass

        # --- Selector de Navegador ---
        ctk.CTkLabel(cfg, text="Navegador:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(6,6))
        browser_options = {
            "Chrome": 'chrome',
            "Chromium": 'chromium',
            "Firefox": 'firefox'
        }
        # Selección actual (etiqueta)
        current_browser_label = None
        for k, v in browser_options.items():
            if v == self.browser:
                current_browser_label = k
                break
        if not current_browser_label:
            current_browser_label = list(browser_options.keys())[0]

        browser_opt = ctk.CTkOptionMenu(cfg, values=list(browser_options.keys()))
        browser_opt.pack(pady=(0,12))
        try:
            browser_opt.set(current_browser_label)
        except Exception:
            pass

        def guardar():
            try:
                sel_label = opt.get()
            except Exception:
                sel_label = current_label
            self.external_policy = options.get(sel_label, 'new_tab')
            # Obtener selección de scroll
            try:
                sel_scroll_label = scroll_opt.get()
            except Exception:
                sel_scroll_label = current_scroll_label
            self.scroll_policy = scroll_options.get(sel_scroll_label, 'none')
            # Obtener selección de navegador
            try:
                sel_browser_label = browser_opt.get()
            except Exception:
                sel_browser_label = current_browser_label
            self.browser = browser_options.get(sel_browser_label, 'chrome')
            # Guardar preferencia en ~/.clictoriano/config.json (mantener otras claves si existen)
            try:
                cfg_dir = Path.home() / '.clictoriano'
                cfg_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
                cfg_file = cfg_dir / 'config.json'
                cfg_data = {}
                if cfg_file.exists():
                    try:
                        with cfg_file.open('r', encoding='utf-8') as f:
                            cfg_data = json.load(f) or {}
                    except Exception:
                        cfg_data = {}
                cfg_data['external_policy'] = self.external_policy
                cfg_data['scroll_policy'] = self.scroll_policy
                cfg_data['browser'] = self.browser
                with cfg_file.open('w', encoding='utf-8') as f:
                    json.dump(cfg_data, f)
            except Exception:
                pass
            cfg.destroy()
            # Actualizar etiqueta de estado de scroll tras guardar
            try:
                self.update_scroll_status_label()
            except Exception:
                pass

        btn_frame = ctk.CTkFrame(cfg, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=12)
        ctk.CTkButton(btn_frame, text="Guardar", command=guardar).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Cancelar", command=cfg.destroy).pack(side="left", padx=6)

    def abrir_github(self):
        """Abre el repositorio en el navegador"""
        webbrowser.open("https://github.com/sapoclay/clictoriano")

    def centrar_ventana(self):
        """Centra la ventana en la pantalla"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def crear_panel_lateral(self):
        """Crea el panel lateral con controles"""
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1)

        # Título y Logo
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="ClicToriano 🖱️", 
                                     font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.version_label = ctk.CTkLabel(self.sidebar_frame, text="v1.0", 
                                        font=ctk.CTkFont(size=12))
        self.version_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Configuración de URL
        self.url_label = ctk.CTkLabel(self.sidebar_frame, text="URL Objetivo:", anchor="w")
        self.url_label.grid(row=2, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.url_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="https://ejemplo.com")
        self.url_entry.grid(row=3, column=0, padx=20, pady=(5, 10), sticky="ew")
        self.url_entry.insert(0, "https://es.wikipedia.org/wiki/Python")

        # Intervalo Mínimo
        self.min_label = ctk.CTkLabel(self.sidebar_frame, text="Intervalo Mínimo (seg):", anchor="w")
        self.min_label.grid(row=4, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.min_slider = ctk.CTkSlider(self.sidebar_frame, from_=1, to=60, number_of_steps=59,
                                            command=self.actualizar_label_min)
        self.min_slider.grid(row=5, column=0, padx=20, pady=(5, 5), sticky="ew")
        self.min_slider.set(5)
        
        self.min_value_label = ctk.CTkLabel(self.sidebar_frame, text="5 seg")
        self.min_value_label.grid(row=6, column=0, padx=20, pady=(0, 5))

        # Intervalo Máximo
        self.max_label = ctk.CTkLabel(self.sidebar_frame, text="Intervalo Máximo (seg):", anchor="w")
        self.max_label.grid(row=7, column=0, padx=20, pady=(5, 0), sticky="w")
        
        self.max_slider = ctk.CTkSlider(self.sidebar_frame, from_=1, to=60, number_of_steps=59,
                                            command=self.actualizar_label_max)
        self.max_slider.grid(row=8, column=0, padx=20, pady=(5, 5), sticky="ew")
        self.max_slider.set(10)
        
        self.max_value_label = ctk.CTkLabel(self.sidebar_frame, text="10 seg")
        self.max_value_label.grid(row=9, column=0, padx=20, pady=(0, 10))

        # Máximo de clics
        self.clicks_label = ctk.CTkLabel(self.sidebar_frame, text="Máximo de clics:", anchor="w")
        self.clicks_label.grid(row=10, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.clicks_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="10")
        self.clicks_entry.grid(row=11, column=0, padx=20, pady=(5, 10), sticky="ew")
        self.clicks_entry.insert(0, "10")

        # Switches de configuración
        self.headless_switch = ctk.CTkSwitch(self.sidebar_frame, text="Modo Headless")
        self.headless_switch.grid(row=12, column=0, padx=20, pady=10, sticky="w")
        
        # Botones de control
        self.start_button = ctk.CTkButton(self.sidebar_frame, text="▶ INICIAR",
                                        fg_color="#2ECC71", hover_color="#27AE60",
                                        font=ctk.CTkFont(weight="bold"),
                                        command=self.iniciar_programa)
        self.start_button.grid(row=13, column=0, padx=20, pady=10, sticky="ew")
        
        self.stop_button = ctk.CTkButton(self.sidebar_frame, text="⏹ DETENER",
                                       fg_color="#E74C3C", hover_color="#C0392B",
                                       font=ctk.CTkFont(weight="bold"),
                                       state="disabled",
                                       command=self.detener_programa)
        self.stop_button.grid(row=14, column=0, padx=20, pady=(0, 20), sticky="ew")

        # Botón para comprobar/actualizar driver manualmente
        self.driver_btn = ctk.CTkButton(self.sidebar_frame, text="🔧 Comprobar/Actualizar driver",
                         fg_color="transparent", border_width=1,
                         text_color=("gray10", "#DCE4EE"),
                         height=30,
                         command=self._on_check_update_driver)
        self.driver_btn.grid(row=15, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Apariencia
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Tema:", anchor="w")
        self.appearance_mode_label.grid(row=16, column=0, padx=20, pady=(10, 0), sticky="w")
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, 
                                   values=["System", "Dark", "Light"],
                                   command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=17, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.appearance_mode_optionemenu.set("Dark")

    def crear_area_principal(self):
        """Crea el área principal con logs e información"""
        # Frame de información
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.info_frame.grid_columnconfigure(0, weight=1)
        self.info_frame.grid_rowconfigure(1, weight=1)

        # Panel de estado
        self.status_frame = ctk.CTkFrame(self.info_frame)
        self.status_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="⚪ Estado: Listo para iniciar", 
                                       font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.pack(pady=10, padx=10, anchor="w")
        # Etiqueta para mostrar la política de scroll actualmente activa / última elegida
        self.scroll_status_label = ctk.CTkLabel(self.status_frame, text="", 
                                               font=ctk.CTkFont(size=11))
        self.scroll_status_label.pack(pady=(0,6), padx=10, anchor="w")
        # Inicializar texto y color según la política actual
        try:
            self.update_scroll_status_label()
        except Exception:
            try:
                self.scroll_status_label.configure(text=f"Scroll: {self.scroll_policy}")
            except Exception:
                pass

        # Tarjetas de información
        self.cards_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        self.cards_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.cards_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Tarjeta Internos
        self.card_internal = ctk.CTkFrame(self.cards_frame)
        self.card_internal.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        ctk.CTkLabel(self.card_internal, text="📍 Enlaces Internos", 
                   font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        ctk.CTkLabel(self.card_internal, text="Navegan en la misma pestaña", 
                   text_color="gray").pack(pady=(0, 10))
        
        # Tarjeta Externos
        self.card_external = ctk.CTkFrame(self.cards_frame)
        self.card_external.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        ctk.CTkLabel(self.card_external, text="🌍 Enlaces Externos", 
                   font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        ctk.CTkLabel(self.card_external, text="Abren en nueva pestaña", 
                   text_color="gray").pack(pady=(0, 10))

        # Área de Log
        self.log_label = ctk.CTkLabel(self.info_frame, text="Registro de Actividad:", anchor="w")
        self.log_label.grid(row=2, column=0, sticky="w", pady=(10, 5))
        
        self.log_textbox = ctk.CTkTextbox(self.info_frame, width=500, font=("Consolas", 12))
        self.log_textbox.grid(row=3, column=0, sticky="nsew")
        
        # Botón limpiar log
        self.clear_log_btn = ctk.CTkButton(self.info_frame, text="Limpiar Log", 
                                         height=25, width=100,
                                         fg_color="transparent", border_width=1,
                                         text_color=("gray10", "#DCE4EE"),
                                         command=self.limpiar_log)
        self.clear_log_btn.grid(row=4, column=0, sticky="e", pady=10)

        self.agregar_log("Bienvenido a ClicToriano v1.0\n")
        self.agregar_log("Configure el rango de tiempo y presione INICIAR.\n")
        self.agregar_log("-" * 60 + "\n")

    def actualizar_label_min(self, value):
        self.min_value_label.configure(text=f"{int(value)} seg")
        # Asegurar que min <= max
        if int(value) > int(self.max_slider.get()):
            self.max_slider.set(value)
            self.max_value_label.configure(text=f"{int(value)} seg")

    def actualizar_label_max(self, value):
        self.max_value_label.configure(text=f"{int(value)} seg")
        # Asegurar que max >= min
        if int(value) < int(self.min_slider.get()):
            self.min_slider.set(value)
            self.min_value_label.configure(text=f"{int(value)} seg")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def agregar_log(self, mensaje):
        self.log_textbox.insert("end", mensaje)
        self.log_textbox.see("end")

    def limpiar_log(self):
        self.log_textbox.delete("0.0", "end")

    def validar_campos(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Debe ingresar una URL")
            return False
        
        if not url.startswith("http"):
            messagebox.showerror("Error", "La URL debe comenzar con http:// o https://")
            return False
        
        try:
            max_clicks = int(self.clicks_entry.get())
            if max_clicks < 1:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "El máximo de clics debe ser un número mayor a 0")
            return False
            
        if int(self.min_slider.get()) > int(self.max_slider.get()):
             messagebox.showerror("Error", "El intervalo mínimo no puede ser mayor que el máximo")
             return False
        
        return True

    def iniciar_programa(self):
        if not self.validar_campos():
            return
        
        # Antes de iniciar, comprobar compatibilidad de webdriver si se eligió Firefox
        try:
            if getattr(self, 'browser', 'chrome') == 'firefox':
                ok = self._check_firefox_driver_compat()
                if not ok:
                    # Usuario decidió no continuar o la actualización falló
                    return
        except Exception:
            # Si hay cualquier error en la comprobación, continuar y dejar que el proceso normal maneje el fallo
            pass

        # UI Updates
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.url_entry.configure(state="disabled")
        self.min_slider.configure(state="disabled")
        self.max_slider.configure(state="disabled")
        self.clicks_entry.configure(state="disabled")
        self.headless_switch.configure(state="disabled")
        
        self.status_label.configure(text="🟢 Estado: Ejecutando...", text_color="#2ECC71")
        self.agregar_log(f"\n{'='*20} INICIANDO {'='*20}\n")
        
        self.programa_activo = True
        
        # Thread
        self.thread_programa = threading.Thread(target=self.ejecutar_programa, daemon=True)
        self.thread_programa.start()

    def ejecutar_programa(self):
        try:
            url = self.url_entry.get().strip()
            intervalo_min = int(self.min_slider.get())
            intervalo_max = int(self.max_slider.get())
            max_clicks = int(self.clicks_entry.get())
            headless = bool(self.headless_switch.get())
            
            self.programa = ClicToris(
                url=url,
                intervalo_min=intervalo_min,
                intervalo_max=intervalo_max,
                modo_headless=headless,
                max_clicks=max_clicks,
                external_links_policy=self.external_policy,
                browser=self.browser
            )
            # Aplicar política de scroll seleccionada desde la GUI
            try:
                self.programa.scroll_policy = self.scroll_policy
            except Exception:
                pass
            
            # Redirigir stdout
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            original_print = print
            
            def custom_print(*args, **kwargs):
                mensaje = ' '.join(str(arg) for arg in args) + '\n'
                # Usar after para thread safety en GUI
                # Si el mensaje indica la política de scroll elegida, actualizar la etiqueta de estado
                def handle_message(m=mensaje):
                    self.agregar_log(m)
                    try:
                        if '🔽 Scroll elegido:' in m:
                            # Extraer la política elegida
                            parts = m.split('🔽 Scroll elegido:')
                            if len(parts) > 1:
                                chosen = parts[1].strip().split()[0]
                                # Mostrar la política elegida, pero mantener el color según la configuración (random o no)
                                self.update_scroll_status_label(text=f"Scroll elegido: {chosen}")
                                return
                        # También mostrar la política configurada al iniciar
                        if m.startswith('\n') and 'INICIANDO' in m:
                            try:
                                self.update_scroll_status_label()
                            except Exception:
                                pass
                    except Exception:
                        pass

                self.after(0, handle_message)
            
            import builtins
            builtins.print = custom_print
            
            try:
                if self.programa.iniciar_navegador():
                    self.programa.ejecutar()
            finally:
                sys.stdout = old_stdout
                builtins.print = original_print
            
        except Exception as e:
            self.after(0, lambda: self.agregar_log(f"\n❌ Error: {str(e)}\n"))
        finally:
            self.after(0, self.finalizar_programa)

    def _get_executable_version(self, cmd: list) -> str | None:
        """Ejecuta `cmd` (lista) y extrae la versión primaria de la salida.

        Devuelve la primera pareja de dígitos separadas por puntos encontrada, p.ej. '0.34.0' o '145.0.2'.
        """
        import subprocess, re
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=6)
            m = re.search(r"(\d+\.\d+(?:\.\d+)*)", out)
            if m:
                return m.group(1)
        except Exception:
            return None
        return None

    def _check_firefox_driver_compat(self) -> bool:
        """Comprueba versiones de `firefox` y `geckodriver`. Si detecta posible incompatibilidad,
        muestra un diálogo que permite actualizar el driver ahora.

        Devuelve True para continuar con el inicio, False para abortar.
        """
        import shutil, subprocess
        # Detectar firefox
        firefox_ver = self._get_executable_version(['firefox', '--version'])
        # Detectar geckodriver en PATH
        gecko_path = shutil.which('geckodriver')
        gecko_ver = None
        if gecko_path:
            gecko_ver = self._get_executable_version([gecko_path, '--version'])

        # Si no hay geckodriver, ofrecer instalarlo
        if not gecko_path:
            resp = messagebox.askyesno("Geckodriver no encontrado", (
                "No se ha detectado 'geckodriver' en PATH.\n"
                "¿Deseas intentar descargar/instalar geckodriver ahora?"
            ))
            if not resp:
                return True
            # Intentar instalar
            try:
                from webdrivers import ensure_webdriver
                self.agregar_log("Iniciando instalación de geckodriver...\n")
                ensure_webdriver('firefox', force_install=True)
                self.agregar_log("Instalación finalizada. Intenta iniciar de nuevo.")
                return True
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo instalar geckodriver: {e}")
                return False

        # Si ambos detectados, comparar versiones de forma conservadora: si son diferentes, proponer actualización
        if firefox_ver and gecko_ver and firefox_ver not in gecko_ver:
            # Mostrar diálogo con información y opción de actualizar ahora
            msg = (
                f"Se detectaron versiones potencialmente incompatibles:\n\n"
                f"Firefox: {firefox_ver}\n"
                f"Geckodriver en PATH ({gecko_path}): {gecko_ver}\n\n"
                "¿Deseas intentar actualizar/instalar ahora el geckodriver recomendado?"
            )
            resp = messagebox.askyesno("Incompatibilidad detectada de geckodriver", msg)
            if not resp:
                return True
            try:
                from webdrivers import ensure_webdriver
                self.agregar_log("Intentando actualizar geckodriver...\n")
                ensure_webdriver('firefox', force_install=True)
                self.agregar_log("Actualización finalizada. Continúa el inicio.")
                return True
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar geckodriver: {e}")
                return False

        return True

    def _show_progress_modal(self, title: str, message: str):
        """Muestra una ventana modal con una progressbar indeterminada.

        Devuelve la tupla (modal_window, progressbar)
        """
        modal = ctk.CTkToplevel(self)
        modal.title(title)
        modal.geometry("420x120")
        modal.transient(self)
        modal.grab_set()
        modal.resizable(False, False)
        # Centrar modal
        x = self.winfo_x() + (self.winfo_width() // 2) - 210
        y = self.winfo_y() + (self.winfo_height() // 2) - 60
        modal.geometry(f"+{x}+{y}")

        lbl = ctk.CTkLabel(modal, text=message)
        lbl.pack(pady=(18, 6), padx=12)
        pb = ctk.CTkProgressBar(modal, mode='indeterminate')
        pb.pack(fill='x', padx=20, pady=(6, 12))
        try:
            pb.start(10)
        except Exception:
            pass
        return modal, pb

    def _on_check_update_driver(self):
        """Manejador del botón 'Comprobar/Actualizar driver' en la GUI."""
        # Ejecutar en hilo para no bloquear la GUI
        def worker():
            try:
                from webdrivers import ensure_webdriver
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Módulo webdrivers no disponible: {e}"))
                self.after(0, lambda: self.agregar_log("Error: módulo webdrivers no disponible\n"))
                self.after(0, close_modal)
                return

            self.after(0, lambda: self.agregar_log("Comprobando/instalando webdriver...\n"))
            # status callback para mostrar el archivo/versión objetivo en el modal
            def status_cb(event: str, data: dict | None = None):
                try:
                    if event == 'download_start' and isinstance(data, dict):
                        info = data
                        ver = info.get('version') or info.get('archive') or info.get('url')
                        txt = f"Descargando: {ver}"
                        self.after(0, lambda: lbl.configure(text=txt))
                except Exception:
                    pass

            try:
                path_instalado = ensure_webdriver(self.browser, force_install=False, progress_callback=progress_cb, status_callback=status_cb)
                # Si llegó aquí, instalación/comprobación fue exitosa (o ya estaba en PATH)
                self.after(0, lambda: self.agregar_log(f"webdriver disponible: {path_instalado}\n"))
                # Mostrar resultado en el modal con botón para copiar ruta
                def show_result():
                    try:
                        # Limpiar widgets de progreso
                        try:
                            pb_det.pack_forget()
                        except Exception:
                            pass
                        try:
                            pb_ind.pack_forget()
                            pb_ind.stop()
                        except Exception:
                            pass
                        pct_label.configure(text="Completado")
                        # Label con ruta y botón copiar
                        path_lbl = ctk.CTkLabel(modal, text=f"Instalado en: {path_instalado}")
                        path_lbl.pack(pady=(6,6))
                        def copiar():
                            try:
                                self.clipboard_clear()
                                self.clipboard_append(path_instalado)
                                self.after(0, lambda: self.agregar_log(f"Ruta copiada al portapapeles: {path_instalado}\n"))
                            except Exception:
                                pass

                        btn_copy = ctk.CTkButton(modal, text="Copiar ruta al portapapeles", command=copiar)
                        btn_copy.pack(pady=(0,6))
                        # Botón cerrar
                        btn_close = ctk.CTkButton(modal, text="Cerrar", command=close_modal)
                        btn_close.pack(pady=(0,8))
                    except Exception as e:
                        try:
                            messagebox.showinfo("Info", f"Instalado en: {path_instalado}")
                        except Exception:
                            pass

                self.after(0, show_result)
            except Exception as e:
                # Intentar fallback con force_install
                try:
                    self.after(0, lambda: self.agregar_log(f"Intentando forzar instalación: {e}\n"))
                    path_instalado = ensure_webdriver(self.browser, force_install=True, progress_callback=progress_cb, status_callback=status_cb)
                    self.after(0, lambda: self.agregar_log(f"Instalación forzada completada: {path_instalado}\n"))
                    def show_result2():
                        try:
                            try:
                                pb_det.pack_forget()
                            except Exception:
                                pass
                            try:
                                pb_ind.pack_forget()
                                pb_ind.stop()
                            except Exception:
                                pass
                            pct_label.configure(text="Completado")
                            path_lbl = ctk.CTkLabel(modal, text=f"Instalado en: {path_instalado}")
                            path_lbl.pack(pady=(6,6))
                            def copiar2():
                                try:
                                    self.clipboard_clear()
                                    self.clipboard_append(path_instalado)
                                    self.after(0, lambda: self.agregar_log(f"Ruta copiada al portapapeles: {path_instalado}\n"))
                                except Exception:
                                    pass
                            btn_copy = ctk.CTkButton(modal, text="Copiar ruta al portapapeles", command=copiar2)
                            btn_copy.pack(pady=(0,6))
                            btn_close = ctk.CTkButton(modal, text="Cerrar", command=close_modal)
                            btn_close.pack(pady=(0,8))
                        except Exception:
                            pass

                    self.after(0, show_result2)
                except Exception as e2:
                    self.after(0, lambda: messagebox.showerror("Error", f"No se pudo instalar el webdriver: {e2}"))
                    self.after(0, lambda: self.agregar_log(f"Error instalando webdriver: {e2}\n"))
                    self.after(0, close_modal)

        # Crear modal con barra determinista y etiqueta de porcentaje
        modal = ctk.CTkToplevel(self)
        modal.title("Instalando webdriver")
        # Aumentar altura para que se vean los botones al finalizar
        modal.geometry("520x220")
        modal.transient(self)
        # Intentar grab_set de forma segura: actualizar la ventana y reintentar si falla
        try:
            modal.update_idletasks()
            modal.grab_set()
        except Exception:
            # Programar un intento breve después para cuando la ventana sea viewable
            try:
                self.after(50, lambda: (modal.update_idletasks(), modal.grab_set()))
            except Exception:
                pass
        # NO usar grab_set_global ni deshabilitar la ventana principal — pueden bloquear el sistema en algunos entornos.
        modal.resizable(False, False)
        x = self.winfo_x() + (self.winfo_width() // 2) - 260
        y = self.winfo_y() + (self.winfo_height() // 2) - 110
        modal.geometry(f"+{x}+{y}")

        lbl = ctk.CTkLabel(modal, text="Descargando/instalando driver, por favor espera...")
        lbl.pack(pady=(12, 6), padx=12)
        # Barra determinista (visible por defecto)
        pb_det = ctk.CTkProgressBar(modal)
        pb_det.pack(fill='x', padx=20, pady=(6, 6))
        # Barra indeterminada (oculta inicialmente)
        pb_ind = ctk.CTkProgressBar(modal, mode='indeterminate')
        # no la empaquetamos aún
        # Etiqueta de porcentaje
        pct_label = ctk.CTkLabel(modal, text="0%")
        pct_label.pack(pady=(0, 12))

        def close_modal():
            try:
                # Parar barra indeterminada si estaba corriendo
                try:
                    pb_ind.stop()
                except Exception:
                    pass
            except Exception:
                pass
            try:
                modal.grab_release()
            except Exception:
                pass
            try:
                modal.destroy()
            except Exception:
                pass

        # Callback de progreso llamado desde el hilo de descarga
        def progress_cb(downloaded: int, total: int | None):
            # Si el servidor proporcionó total, usamos la barra determinista
            if total and total > 0:
                frac = min(max(downloaded / total, 0.0), 1.0)
                pct = int(frac * 100)
                # Asegurar que la barra determinista esté visible
                def upd_det():
                    try:
                        # si pb_ind está visible, ocultarlo
                        try:
                            pb_ind.pack_forget()
                        except Exception:
                            pass
                        # mostrar pb_det si no está visible
                        try:
                            pb_det.pack(fill='x', padx=20, pady=(6, 6))
                        except Exception:
                            pass
                        pb_det.set(frac)
                        pct_label.configure(text=f"{pct}%")
                    except Exception:
                        pass

                self.after(0, upd_det)
            else:
                # Sin Content-Length: mostrar barra indeterminada
                def upd_ind():
                    try:
                        # ocultar determinista
                        try:
                            pb_det.pack_forget()
                        except Exception:
                            pass
                        # mostrar indeterminada y arrancarla
                        try:
                            pb_ind.pack(fill='x', padx=20, pady=(6, 6))
                            pb_ind.start(20)
                        except Exception:
                            pass
                        pct_label.configure(text="...")
                    except Exception:
                        pass

                self.after(0, upd_ind)

        # Iniciar thread del worker; el worker usará la closure `progress_cb`.
        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def detener_programa(self):
        self.programa_activo = False
        self.agregar_log("\n⚠️ Deteniendo programa...\n")
        
        if self.programa and self.programa.driver:
            try:
                self.programa.driver.quit()
            except:
                pass
        
        self.finalizar_programa()

    def finalizar_programa(self):
        self.programa_activo = False
        self.status_label.configure(text="⚪ Estado: Detenido", text_color=("gray10", "#DCE4EE"))
        
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.url_entry.configure(state="normal")
        self.min_slider.configure(state="normal")
        self.max_slider.configure(state="normal")
        self.clicks_entry.configure(state="normal")
        self.headless_switch.configure(state="normal")
        
        self.agregar_log(f"\n{'='*20} FINALIZADO {'='*20}\n")

if __name__ == "__main__":
    app = ClicTorisGUI()
    app.mainloop()
