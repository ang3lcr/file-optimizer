"""
ui/app.py
Clase principal de la aplicación CustomTkinter.
"""

from __future__ import annotations
import sys
import tkinter as tk
from pathlib import Path
from typing import Optional

import customtkinter as ctk

from ui.theme import get_palette, FONT
from utils.config_manager import ConfigManager
from utils.logger import get_logger

logger = get_logger("ui.app")


class FileOptimizerApp(ctk.CTk):
    """
    Ventana principal de FileOptimizer Pro.

    Gestiona:
    - Inicialización de CustomTkinter con tema guardado.
    - Layout root: sidebar + área principal.
    - Cierre limpio guardando configuración.
    """

    APP_TITLE = "FileOptimizer Pro"
    APP_VERSION = "1.0.0"
    MIN_WIDTH = 1150
    MIN_HEIGHT = 680

    def __init__(self, config: ConfigManager) -> None:
        self.config = config
        theme = config.get("theme", "light")

        # Configurar tema antes de crear ventanas
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("blue")

        super().__init__()

        self.palette = get_palette(theme)
        self._setup_window()
        self._build_ui()

        logger.info("Aplicación iniciada (tema=%s)", theme)

    def _setup_window(self) -> None:
        """Configura tamaño, título e ícono de la ventana."""
        self.title(self.APP_TITLE)
        self.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)

        # Geometría guardada o por defecto
        saved_geom = self.config.get("window_geometry", "")
        if saved_geom:
            try:
                self.geometry(saved_geom)
            except Exception:
                self._center_window(1280, 780)
        else:
            self._center_window(1280, 780)

        if self.config.get("window_maximized", False):
            self.state("zoomed")

        # Ícono
        icon_path = Path(__file__).parent.parent / "assets" / "logo.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        self.configure(fg_color=self.palette.bg_primary)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center_window(self, w: int, h: int) -> None:
        """Centra la ventana en la pantalla."""
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - w) // 2
        y = (screen_h - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self) -> None:
        """Construye el layout principal."""
        from ui.main_window import MainWindow
        self.main_window = MainWindow(self, self.config, self.palette)
        self.main_window.pack(fill="both", expand=True)

    def _on_close(self) -> None:
        """Guarda el estado de la ventana antes de cerrar."""
        try:
            is_maximized = self.state() == "zoomed"
            self.config.set("window_maximized", is_maximized)
            if not is_maximized:
                self.config.set("window_geometry", self.geometry())
            self.config.save()
        except Exception as exc:
            logger.warning("Error al guardar geometría: %s", exc)
        finally:
            logger.info("Aplicación cerrada.")
            self.destroy()

    def toggle_theme(self) -> None:
        """Alterna entre tema Claro (light) y Oscuro (dark)."""
        current = self.config.get("theme", "light")
        new_theme = "dark" if current == "light" else "light"
        
        # Guardar nueva configuración
        self.config.set("theme", new_theme)
        self.palette = get_palette(new_theme)
        
        # Sincronizar apariencia de CustomTkinter
        ctk.set_appearance_mode(new_theme)
        self.configure(fg_color=self.palette.bg_primary)
        
        # Reconstruir la interfaz para aplicar los nuevos colores
        if hasattr(self, "main_window"):
            self.main_window.destroy()
        self._build_ui()
        logger.info("Tema cambiado a: %s (interfaz recreada)", new_theme)
