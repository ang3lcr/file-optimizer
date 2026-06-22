"""
ui/sidebar.py
Panel lateral de opciones de compresión.
"""

from __future__ import annotations
import tkinter as tk
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

import customtkinter as ctk

from ui.theme import ColorPalette, FONT
from models.compression_profile import QualityLevel, CompressionMode
from compressors.base import CompressionOptions
from utils.config_manager import ConfigManager
from utils.logger import get_logger

if TYPE_CHECKING:
    from ui.main_window import MainWindow

logger = get_logger("ui.sidebar")


class Sidebar(ctk.CTkFrame):
    """
    Panel lateral con controles de configuración de compresión.

    Controles:
    - Selector de nivel de calidad.
    - Modo de compresión (auto/manual).
    - Toggle: eliminar metadatos.
    - Toggle: eliminar revisiones.
    - Toggle: convertir a WebP.
    - Selector de carpeta de salida.
    - Botón principal "Comprimir".
    - Botón "Limpiar lista".
    """

    WIDTH = 270

    def __init__(
        self,
        master: ctk.CTkFrame,
        config: ConfigManager,
        palette: ColorPalette,
        main_window: "MainWindow",
    ) -> None:
        super().__init__(
            master,
            width=self.WIDTH,
            fg_color=self.palette_bg(palette),
            corner_radius=0,
            border_width=1,
            border_color=palette.border,
        )
        self.pack_propagate(False)
        self.palette = palette
        self.config = config
        self.main_window = main_window

        self._cancel_fn: Optional[Callable] = None
        self._is_processing = False

        self._build()

    def palette_bg(self, palette: ColorPalette) -> str:
        return palette.bg_secondary

    def _build(self) -> None:
        """Construye todos los controles del sidebar."""
        # Scroll interior
        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.palette.border,
            scrollbar_button_hover_color=self.palette.accent_primary,
        )
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # Título sección
        self._section_title(scroll, "⚙  Opciones de Compresión")

        # Calidad
        self._build_quality_section(scroll)
        self._separator(scroll)

        # Modo de compresión
        self._build_mode_section(scroll)
        self._separator(scroll)

        # Toggles
        self._build_toggles(scroll)
        self._separator(scroll)

        # Carpeta de salida
        self._build_output_folder(scroll)
        self._separator(scroll)

        # Estadística rápida
        self._build_stats(scroll)

        # Botones acción (fuera del scroll, siempre visibles)
        self._build_action_buttons()

    # ------------------------------------------------------------------
    # Secciones
    # ------------------------------------------------------------------

    def _build_quality_section(self, parent: ctk.CTkScrollableFrame) -> None:
        self._section_label(parent, "Nivel de calidad")

        self._quality_var = tk.StringVar(value=self.config.get("quality_level", "balanced"))
        quality_options = [q.label for q in QualityLevel if q != QualityLevel.CUSTOM]
        self._quality_values = [q.value for q in QualityLevel if q != QualityLevel.CUSTOM]

        self._quality_menu = ctk.CTkOptionMenu(
            parent,
            values=quality_options,
            variable=self._quality_var,
            fg_color=self.palette.bg_card,
            button_color=self.palette.accent_primary,
            button_hover_color=self.palette.accent_hover,
            text_color=self.palette.text_primary,
            dropdown_fg_color=self.palette.bg_card,
            dropdown_text_color=self.palette.text_primary,
            dropdown_hover_color=self.palette.bg_hover,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
            command=self._on_quality_changed,
        )
        self._quality_menu.pack(fill="x", padx=12, pady=(4, 2))

        # Slider de calidad personalizada (oculto por defecto)
        self._custom_quality_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._custom_quality_label = ctk.CTkLabel(
            self._custom_quality_frame,
            text="Calidad personalizada: 75%",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_xs),
            text_color=self.palette.text_secondary,
        )
        self._custom_quality_label.pack(fill="x", padx=12)
        self._custom_quality_slider = ctk.CTkSlider(
            self._custom_quality_frame,
            from_=10,
            to=100,
            number_of_steps=18,
            progress_color=self.palette.accent_primary,
            button_color=self.palette.accent_primary,
            button_hover_color=self.palette.accent_hover,
            command=self._on_custom_quality_changed,
        )
        self._custom_quality_slider.set(self.config.get("custom_image_quality", 75))
        self._custom_quality_slider.pack(fill="x", padx=12, pady=(0, 4))

        # Descripción del nivel
        self._quality_desc = ctk.CTkLabel(
            parent,
            text=self._get_quality_desc(),
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_xs),
            text_color=self.palette.text_muted,
            wraplength=220,
            justify="left",
        )
        self._quality_desc.pack(fill="x", padx=12, pady=(0, 4))

    def _build_mode_section(self, parent: ctk.CTkScrollableFrame) -> None:
        self._section_label(parent, "Modo de compresión")

        self._mode_var = tk.StringVar(value="Automático")
        mode_options = [m.label for m in CompressionMode]

        ctk.CTkOptionMenu(
            parent,
            values=mode_options,
            variable=self._mode_var,
            fg_color=self.palette.bg_card,
            button_color=self.palette.accent_primary,
            button_hover_color=self.palette.accent_hover,
            text_color=self.palette.text_primary,
            dropdown_fg_color=self.palette.bg_card,
            dropdown_text_color=self.palette.text_primary,
            dropdown_hover_color=self.palette.bg_hover,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
        ).pack(fill="x", padx=12, pady=(4, 4))

    def _build_toggles(self, parent: ctk.CTkScrollableFrame) -> None:
        self._section_label(parent, "Opciones avanzadas")

        self._meta_var = tk.BooleanVar(value=self.config.get("remove_metadata", True))
        self._rev_var = tk.BooleanVar(value=self.config.get("remove_revisions", False))
        self._webp_var = tk.BooleanVar(value=self.config.get("convert_images_to_webp", False))

        self._toggle_row(parent, "Eliminar metadatos", self._meta_var, self._on_toggle_meta)
        self._toggle_row(parent, "Eliminar revisiones (Office)", self._rev_var, self._on_toggle_rev)
        self._toggle_row(parent, "Convertir imágenes a WebP", self._webp_var, self._on_toggle_webp)

    def _build_output_folder(self, parent: ctk.CTkScrollableFrame) -> None:
        self._section_label(parent, "Carpeta de salida")

        saved_folder = self.config.get("last_output_folder", "")
        self._output_mode = "same_folder"

        ctk.CTkRadioButton(
            parent,
            text="Misma carpeta del archivo",
            value="same_folder",
            variable=tk.StringVar(value="same_folder"),
            fg_color=self.palette.accent_primary,
            border_color=self.palette.border,
            text_color=self.palette.text_primary,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
        ).pack(anchor="w", padx=12, pady=(4, 2))

        folder_row = ctk.CTkFrame(parent, fg_color="transparent")
        folder_row.pack(fill="x", padx=12, pady=(2, 4))

        self._folder_entry = ctk.CTkEntry(
            folder_row,
            placeholder_text="Carpeta personalizada...",
            fg_color=self.palette.bg_card,
            border_color=self.palette.border,
            text_color=self.palette.text_primary,
            placeholder_text_color=self.palette.text_muted,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_xs),
        )
        if saved_folder:
            self._folder_entry.insert(0, saved_folder)
        self._folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            folder_row,
            text="...",
            width=30,
            fg_color=self.palette.bg_card,
            hover_color=self.palette.bg_hover,
            border_color=self.palette.border,
            border_width=1,
            text_color=self.palette.text_primary,
            command=self._browse_output_folder,
        ).pack(side="right")

    def _build_stats(self, parent: ctk.CTkScrollableFrame) -> None:
        """Mini panel de estadísticas de la sesión actual."""
        self._section_label(parent, "Sesión actual")

        stats_frame = ctk.CTkFrame(
            parent,
            fg_color=self.palette.bg_card,
            corner_radius=8,
            border_width=1,
            border_color=self.palette.border,
        )
        stats_frame.pack(fill="x", padx=12, pady=(4, 8))

        self._stat_files = self._stat_item(stats_frame, "Archivos", "0")
        self._stat_saved = self._stat_item(stats_frame, "Espacio ahorrado", "0 B")
        self._stat_avg = self._stat_item(stats_frame, "Reducción promedio", "0%")

    def _build_action_buttons(self) -> None:
        """Botones de acción siempre visibles en la parte inferior."""
        btn_frame = ctk.CTkFrame(
            self,
            fg_color=self.palette.bg_secondary,
            corner_radius=0,
            border_width=1,
            border_color=self.palette.border,
        )
        btn_frame.pack(fill="x", side="bottom", padx=0, pady=0)

        self._compress_btn = ctk.CTkButton(
            btn_frame,
            text="▶  Comprimir Todo",
            height=42,
            fg_color=self.palette.accent_primary,
            hover_color=self.palette.accent_hover,
            text_color=self.palette.text_on_accent,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_base, weight="bold"),
            corner_radius=8,
            command=self._on_compress_clicked,
        )
        self._compress_btn.pack(fill="x", padx=12, pady=(10, 4))

        self._clear_btn = ctk.CTkButton(
            btn_frame,
            text="🗑  Limpiar lista",
            height=34,
            fg_color="transparent",
            hover_color=self.palette.bg_hover,
            border_width=1,
            border_color=self.palette.border,
            text_color=self.palette.text_secondary,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
            corner_radius=8,
            command=self._on_clear_clicked,
        )
        self._clear_btn.pack(fill="x", padx=12, pady=(0, 10))

    # ------------------------------------------------------------------
    # Helpers UI
    # ------------------------------------------------------------------

    def _section_title(self, parent: ctk.CTkScrollableFrame, text: str) -> None:
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm, weight="bold"),
            text_color=self.palette.text_primary,
            anchor="w",
        ).pack(fill="x", padx=12, pady=(16, 4))

    def _section_label(self, parent: ctk.CTkScrollableFrame, text: str) -> None:
        ctk.CTkLabel(
            parent,
            text=text.upper(),
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_xs, weight="bold"),
            text_color=self.palette.text_muted,
            anchor="w",
        ).pack(fill="x", padx=12, pady=(10, 2))

    def _separator(self, parent: ctk.CTkScrollableFrame) -> None:
        ctk.CTkFrame(
            parent,
            height=1,
            fg_color=self.palette.border,
        ).pack(fill="x", padx=8, pady=4)

    def _toggle_row(
        self,
        parent: ctk.CTkScrollableFrame,
        text: str,
        var: tk.BooleanVar,
        command: Callable,
    ) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=2)

        ctk.CTkLabel(
            row,
            text=text,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
            text_color=self.palette.text_primary,
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkSwitch(
            row,
            text="",
            variable=var,
            width=40,
            height=20,
            progress_color=self.palette.accent_primary,
            button_color=self.palette.text_on_accent,
            button_hover_color=self.palette.accent_light,
            command=command,
        ).pack(side="right")

    def _stat_item(self, parent: ctk.CTkFrame, label: str, value: str) -> ctk.CTkLabel:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=3)
        ctk.CTkLabel(
            row,
            text=label,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_xs),
            text_color=self.palette.text_muted,
        ).pack(side="left")
        lbl = ctk.CTkLabel(
            row,
            text=value,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_xs, weight="bold"),
            text_color=self.palette.accent_primary,
        )
        lbl.pack(side="right")
        return lbl

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_quality_changed(self, label: str) -> None:
        selected = next(
            (q for q in QualityLevel if q.label == label), QualityLevel.BALANCED
        )
        self.config.set("quality_level", selected.value)
        self._quality_desc.configure(text=self._get_quality_desc())
        if selected == QualityLevel.CUSTOM:
            self._custom_quality_frame.pack(fill="x")
        else:
            self._custom_quality_frame.pack_forget()

    def _on_custom_quality_changed(self, value: float) -> None:
        q = int(value)
        self._custom_quality_label.configure(text=f"Calidad personalizada: {q}%")
        self.config.set("custom_image_quality", q)

    def _on_toggle_meta(self) -> None:
        self.config.set("remove_metadata", self._meta_var.get())

    def _on_toggle_rev(self) -> None:
        self.config.set("remove_revisions", self._rev_var.get())

    def _on_toggle_webp(self) -> None:
        self.config.set("convert_images_to_webp", self._webp_var.get())

    def _browse_output_folder(self) -> None:
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if folder:
            self._folder_entry.delete(0, "end")
            self._folder_entry.insert(0, folder)
            self.config.set("last_output_folder", folder)

    def _on_compress_clicked(self) -> None:
        if self._is_processing and self._cancel_fn:
            self._cancel_fn()
        else:
            self.main_window.start_compression()

    def _on_clear_clicked(self) -> None:
        self.main_window.results_table.clear_all()
        self.update_stats(0, 0, 0)

    def _get_quality_desc(self) -> str:
        level_str = self.config.get("quality_level", "balanced")
        descs = {
            "maximum": "Mínima pérdida de calidad. Ideal para documentos finales.",
            "high": "Excelente calidad. Buena reducción para imágenes.",
            "balanced": "Balance óptimo entre tamaño y calidad. Recomendado.",
            "high_compression": "Mayor compresión, ligera pérdida de calidad.",
            "extreme": "Máxima compresión. Usar solo cuando el tamaño es crítico.",
            "custom": "Define manualmente el nivel de calidad con el slider.",
        }
        return descs.get(level_str, "")

    # ------------------------------------------------------------------
    # Métodos públicos
    # ------------------------------------------------------------------

    def add_files(self, paths: list[Path]) -> None:
        """Llamado cuando se agregan archivos desde la drop zone."""
        pass  # Actualización de stats manejada por ResultsTable

    def get_options(self) -> CompressionOptions:
        """Retorna las opciones actuales configuradas por el usuario."""
        quality_str = self.config.get("quality_level", "balanced")
        quality = next(
            (q for q in QualityLevel if q.value == quality_str),
            QualityLevel.BALANCED,
        )

        folder_text = self._folder_entry.get().strip()
        output_folder = Path(folder_text) if folder_text else None

        return CompressionOptions(
            quality_level=quality,
            custom_quality=self.config.get("custom_image_quality", 75),
            remove_metadata=self._meta_var.get(),
            remove_revisions=self._rev_var.get(),
            convert_to_webp=self._webp_var.get(),
        )

    def set_processing(self, processing: bool, cancel_fn: Optional[Callable] = None) -> None:
        """Actualiza el estado del botón según si hay compresión en curso."""
        self._is_processing = processing
        self._cancel_fn = cancel_fn
        if processing:
            self._compress_btn.configure(
                text="⏹  Cancelar",
                fg_color=self.palette.error,
                hover_color=self.palette.error,
            )
        else:
            self._compress_btn.configure(
                text="▶  Comprimir Todo",
                fg_color=self.palette.accent_primary,
                hover_color=self.palette.accent_hover,
            )

    def update_stats(self, files: int, saved_bytes: int, avg_reduction: float) -> None:
        """Actualiza el mini panel de estadísticas."""
        from utils.file_utils import format_size
        self._stat_files.configure(text=str(files))
        self._stat_saved.configure(text=format_size(saved_bytes))
        self._stat_avg.configure(text=f"{avg_reduction:.1f}%")
