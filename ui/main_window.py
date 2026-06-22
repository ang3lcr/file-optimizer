"""
ui/main_window.py
Layout principal de la aplicación.

Estructura:
┌─────────────────────────────────────────────────────┐
│  Header (logo + título + toggle tema)               │
├──────────────┬──────────────────────────────────────┤
│              │  Tab: Comprimir                      │
│   Sidebar    │    - DropZone                        │
│              │    - Tabla de resultados             │
│  (opciones)  │    - Panel de progreso               │
│              ├──────────────────────────────────────┤
│              │  Tab: Historial                      │
│              ├──────────────────────────────────────┤
│              │  Tab: Configuración                  │
└──────────────┴──────────────────────────────────────┘
"""

from __future__ import annotations
import tkinter as tk
from pathlib import Path
from typing import TYPE_CHECKING

import customtkinter as ctk

from ui.theme import ColorPalette, FONT
from utils.config_manager import ConfigManager

if TYPE_CHECKING:
    from ui.app import FileOptimizerApp


class MainWindow(ctk.CTkFrame):
    """Frame raíz que organiza todo el layout de la aplicación."""

    def __init__(
        self,
        master: "FileOptimizerApp",
        config: ConfigManager,
        palette: ColorPalette,
    ) -> None:
        super().__init__(master, fg_color="transparent", corner_radius=0)
        self.app = master
        self.config = config
        self.palette = palette

        self._build_header()
        self._build_body()

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _build_header(self) -> None:
        """Barra superior con logo, título y toggle de tema."""
        header = ctk.CTkFrame(
            self,
            height=56,
            corner_radius=0,
            fg_color=self.palette.bg_secondary,
            border_width=1,
            border_color=self.palette.border,
        )
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # Logo + título
        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.pack(side="left", padx=20)

        # Cargar logotipo logofinanzas.jpg si existe
        logo_path = Path(__file__).parent.parent / "./assets/logofinanzas.jpg"
        if logo_path.exists():
            try:
                from PIL import Image
                pil_img = Image.open(logo_path)
                # Relación de aspecto ~2.27 (339x149). Para altura 36px, ancho es ~82px
                logo_ctk = ctk.CTkImage(
                    light_image=pil_img,
                    dark_image=pil_img,
                    size=(82, 36)
                )
                logo_label = ctk.CTkLabel(logo_frame, image=logo_ctk, text="")
                logo_label.pack(side="left", padx=(0, 10))
            except Exception:
                # Fallback a emoji en caso de error
                ctk.CTkLabel(
                    logo_frame,
                    text="⚡",
                    font=ctk.CTkFont(size=22),
                    text_color=self.palette.accent_primary,
                ).pack(side="left", padx=(0, 8))
        else:
            ctk.CTkLabel(
                logo_frame,
                text="⚡",
                font=ctk.CTkFont(size=22),
                text_color=self.palette.accent_primary,
            ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            logo_frame,
            text="FileOptimizer Pro",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_lg, weight="bold"),
            text_color=self.palette.text_primary,
        ).pack(side="left")

        ctk.CTkLabel(
            logo_frame,
            text="v1.0",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_xs),
            text_color=self.palette.text_muted,
        ).pack(side="left", padx=(6, 0), pady=(6, 0))

        # Controles derecha
        right_frame = ctk.CTkFrame(header, fg_color="transparent")
        right_frame.pack(side="right", padx=16)

        # Toggle tema
        self._theme_label = ctk.CTkLabel(
            right_frame,
            text="🌙" if self.config.get("theme") == "dark" else "☀️",
            font=ctk.CTkFont(size=16),
            cursor="hand2",
        )
        self._theme_label.pack(side="right", padx=8)
        self._theme_label.bind("<Button-1>", self._toggle_theme)

    # ------------------------------------------------------------------
    # Body: Sidebar + Área principal con tabs
    # ------------------------------------------------------------------

    def _build_body(self) -> None:
        """Construye el área principal con sidebar y tabs."""
        body = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True)

        # Sidebar izquierdo
        from ui.sidebar import Sidebar
        self.sidebar = Sidebar(body, self.config, self.palette, self)
        self.sidebar.pack(side="left", fill="y")

        # Área de contenido
        content = ctk.CTkFrame(
            body,
            fg_color=self.palette.bg_primary,
            corner_radius=0,
        )
        content.pack(side="left", fill="both", expand=True)

        # Tabs
        self.tabview = ctk.CTkTabview(
            content,
            fg_color=self.palette.bg_primary,
            segmented_button_fg_color=self.palette.bg_secondary,
            segmented_button_selected_color=self.palette.accent_primary,
            segmented_button_selected_hover_color=self.palette.accent_hover,
            segmented_button_unselected_color=self.palette.bg_secondary,
            segmented_button_unselected_hover_color=self.palette.bg_hover,
            text_color=self.palette.text_primary,
            text_color_disabled=self.palette.text_muted,
            border_color=self.palette.border,
            border_width=1,
        )
        self.tabview.pack(fill="both", expand=True, padx=8, pady=(8, 8))

        self.tabview.add("  Comprimir  ")
        self.tabview.add("  Historial  ")
        self.tabview.add("  Configuración  ")

        self._build_compress_tab(self.tabview.tab("  Comprimir  "))
        self._build_history_tab(self.tabview.tab("  Historial  "))
        self._build_settings_tab(self.tabview.tab("  Configuración  "))

    # ------------------------------------------------------------------
    # Tab: Comprimir
    # ------------------------------------------------------------------

    def _build_compress_tab(self, parent: ctk.CTkFrame) -> None:
        from ui.drop_zone import DropZone
        from ui.results_table import ResultsTable
        from ui.progress_panel import ProgressPanel

        # Drop zone superior
        self.drop_zone = DropZone(parent, self.palette, on_files_dropped=self._on_files_dropped)
        self.drop_zone.pack(fill="x", padx=12, pady=(12, 6))

        # Panel de progreso
        self.progress_panel = ProgressPanel(parent, self.palette)
        self.progress_panel.pack(fill="x", padx=12, pady=(0, 6))

        # Tabla de resultados (resto del espacio)
        self.results_table = ResultsTable(parent, self.palette)
        self.results_table.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    # ------------------------------------------------------------------
    # Tab: Historial
    # ------------------------------------------------------------------

    def _build_history_tab(self, parent: ctk.CTkFrame) -> None:
        from ui.history_view import HistoryView
        self.history_view = HistoryView(parent, self.palette, self.config)
        self.history_view.pack(fill="both", expand=True, padx=12, pady=12)

    # ------------------------------------------------------------------
    # Tab: Configuración
    # ------------------------------------------------------------------

    def _build_settings_tab(self, parent: ctk.CTkFrame) -> None:
        from ui.settings_dialog import SettingsPanel
        self.settings_panel = SettingsPanel(parent, self.palette, self.config, self.app)
        self.settings_panel.pack(fill="both", expand=True, padx=12, pady=12)

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_files_dropped(self, paths: list[Path]) -> None:
        """Llamado cuando el usuario arrastra/selecciona archivos."""
        self.sidebar.add_files(paths)
        self.results_table.add_files(paths)

    def _toggle_theme(self, event: tk.Event | None = None) -> None:
        self.app.toggle_theme()

    def start_compression(self) -> None:
        """Inicia el proceso de compresión desde el sidebar."""
        from ui.compression_worker import CompressionWorker
        files = self.results_table.get_pending_files()
        if not files:
            return

        options = self.sidebar.get_options()
        worker = CompressionWorker(
            files=files,
            options=options,
            on_file_start=self.results_table.on_file_start,
            on_file_progress=self.results_table.on_file_progress,
            on_file_done=self._on_file_done,
            on_all_done=self._on_all_done,
            progress_panel=self.progress_panel,
        )
        self.sidebar.set_processing(True, worker.cancel)
        self.progress_panel.start(len(files))
        worker.start()

    def _on_file_done(self, file_id: str, result: object) -> None:
        """Llamado en el hilo principal cuando un archivo termina."""
        self.results_table.on_file_done(file_id, result)
        # Agregar al historial
        from utils.history_manager import HistoryManager
        from models.compression_result import CompressionResult
        from models.history_entry import HistoryEntry
        from datetime import datetime

        if isinstance(result, CompressionResult) and result.success:
            entry = HistoryEntry(
                filename=self.results_table.get_filename(file_id),
                file_type=self.results_table.get_filetype(file_id),
                original_size=result.original_size,
                final_size=result.final_size,
                reduction_percent=result.reduction_percent,
                elapsed_seconds=result.elapsed_seconds,
                output_path=str(result.output_path or ""),
                method_used=result.method_used,
                success=result.success,
            )
            HistoryManager().add_entry(entry)

    def _on_all_done(self, total: int, success: int) -> None:
        """Llamado cuando todos los archivos han sido procesados."""
        self.sidebar.set_processing(False)
        self.progress_panel.finish(total, success)
        # Refrescar historial
        if hasattr(self, "history_view"):
            self.history_view.refresh()
