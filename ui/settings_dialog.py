"""
ui/settings_dialog.py
Panel de configuración general de la aplicación.
"""

from __future__ import annotations
import tkinter as tk
from typing import TYPE_CHECKING

import customtkinter as ctk

from ui.theme import ColorPalette, FONT
from utils.config_manager import ConfigManager

if TYPE_CHECKING:
    from ui.app import FileOptimizerApp


class SettingsPanel(ctk.CTkScrollableFrame):
    """
    Panel de configuración completo embebido en la tab de configuración.
    """

    def __init__(
        self,
        master: ctk.CTkFrame,
        palette: ColorPalette,
        config: ConfigManager,
        app: "FileOptimizerApp",
    ) -> None:
        super().__init__(
            master,
            fg_color="transparent",
            scrollbar_button_color=palette.border,
            scrollbar_button_hover_color=palette.accent_primary,
        )
        self.palette = palette
        self.config = config
        self.app = app
        self._build()

    def _build(self) -> None:
        """Construye todas las secciones de configuración."""
        self._section("🎨  Apariencia", [
            ("Tema de la interfaz", "theme"),
        ])

        self._separator()
        self._build_theme_section()

        self._separator()
        self._section("📂  Archivos", None)
        self._build_files_section()

        self._separator()
        self._section("📋  Logs", None)
        self._build_logs_section()

        self._separator()
        self._section("ℹ️  Acerca de", None)
        self._build_about_section()

    # ------------------------------------------------------------------
    # Secciones
    # ------------------------------------------------------------------

    def _build_theme_section(self) -> None:
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=6)

        ctk.CTkLabel(
            row,
            text="Tema de la interfaz",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_base),
            text_color=self.palette.text_primary,
        ).pack(side="left")

        self._theme_var = tk.StringVar(
            value="Oscuro" if self.config.get("theme") == "dark" else "Claro"
        )
        ctk.CTkSegmentedButton(
            row,
            values=["Oscuro", "Claro"],
            variable=self._theme_var,
            fg_color=self.palette.bg_card,
            selected_color=self.palette.accent_primary,
            selected_hover_color=self.palette.accent_hover,
            unselected_color=self.palette.bg_card,
            unselected_hover_color=self.palette.bg_hover,
            text_color=self.palette.text_primary,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
            command=self._on_theme_change,
        ).pack(side="right")

    def _build_files_section(self) -> None:
        # Carpeta de salida por defecto
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=6)

        ctk.CTkLabel(
            row,
            text="Carpeta de salida personalizada",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_base),
            text_color=self.palette.text_primary,
        ).pack(side="left")

        self._folder_entry = ctk.CTkEntry(
            row,
            placeholder_text="Misma carpeta del archivo (por defecto)",
            fg_color=self.palette.bg_card,
            border_color=self.palette.border,
            text_color=self.palette.text_primary,
            placeholder_text_color=self.palette.text_muted,
            width=280,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
        )
        saved_folder = self.config.get("last_output_folder", "")
        if saved_folder:
            self._folder_entry.insert(0, saved_folder)
        self._folder_entry.pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            row,
            text="...",
            width=30,
            fg_color=self.palette.bg_card,
            hover_color=self.palette.bg_hover,
            border_width=1,
            border_color=self.palette.border,
            text_color=self.palette.text_primary,
            command=self._browse_folder,
        ).pack(side="right", padx=4)

    def _build_logs_section(self) -> None:
        from pathlib import Path

        log_path = Path(__file__).parent.parent / "logs" / "fileoptimizer.log"

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=6)

        ctk.CTkLabel(
            row,
            text="Archivo de logs",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_base),
            text_color=self.palette.text_primary,
        ).pack(side="left")

        ctk.CTkLabel(
            row,
            text=str(log_path),
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_xs),
            text_color=self.palette.text_muted,
        ).pack(side="right")

        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(2, 6))

        ctk.CTkButton(
            row2,
            text="Abrir carpeta de logs",
            height=30,
            fg_color="transparent",
            hover_color=self.palette.bg_hover,
            border_width=1,
            border_color=self.palette.border,
            text_color=self.palette.text_secondary,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
            command=self._open_logs_folder,
        ).pack(side="left")

    def _build_about_section(self) -> None:
        about_frame = ctk.CTkFrame(
            self,
            fg_color=self.palette.bg_card,
            corner_radius=10,
            border_width=1,
            border_color=self.palette.border,
        )
        about_frame.pack(fill="x", padx=16, pady=8)

        ctk.CTkLabel(
            about_frame,
            text="⚡ FileOptimizer Pro",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_lg, weight="bold"),
            text_color=self.palette.accent_primary,
        ).pack(pady=(16, 4))

        ctk.CTkLabel(
            about_frame,
            text="Versión 1.0.0",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
            text_color=self.palette.text_secondary,
        ).pack()

        ctk.CTkLabel(
            about_frame,
            text=(
                "Herramienta profesional de compresión de archivos.\n"
                "100% local • Sin conexión a Internet • Datos privados garantizados.\n"
                "Apto para uso en instituciones gubernamentales y corporativas."
            ),
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
            text_color=self.palette.text_muted,
            justify="center",
        ).pack(pady=(8, 16))

        ctk.CTkButton(
            about_frame,
            text="Restaurar configuración por defecto",
            height=32,
            fg_color="transparent",
            hover_color=self.palette.warning_bg,
            border_width=1,
            border_color=self.palette.warning,
            text_color=self.palette.warning,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
            command=self._reset_config,
        ).pack(pady=(0, 16))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _section(self, title: str, _: object) -> None:
        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_md, weight="bold"),
            text_color=self.palette.text_primary,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(16, 4))

    def _separator(self) -> None:
        ctk.CTkFrame(self, height=1, fg_color=self.palette.border).pack(
            fill="x", padx=8, pady=4
        )

    def _on_theme_change(self, value: str) -> None:
        new_theme = "dark" if value == "Oscuro" else "light"
        if new_theme != self.config.get("theme"):
            self.config.set("theme", new_theme)
            self.app.toggle_theme()

    def _browse_folder(self) -> None:
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if folder:
            self._folder_entry.delete(0, "end")
            self._folder_entry.insert(0, folder)
            self.config.set("last_output_folder", folder)

    def _open_logs_folder(self) -> None:
        import subprocess
        from pathlib import Path
        logs_dir = Path(__file__).parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        subprocess.Popen(["explorer", str(logs_dir)])

    def _reset_config(self) -> None:
        from tkinter import messagebox
        if messagebox.askyesno(
            "Confirmar",
            "¿Restaurar toda la configuración a los valores por defecto?",
        ):
            self.config.reset_to_defaults()
