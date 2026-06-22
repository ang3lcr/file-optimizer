"""
ui/history_view.py
Vista de historial de comprensiones realizadas.
"""

from __future__ import annotations
import tkinter as tk
from pathlib import Path
from typing import Optional

import customtkinter as ctk

from ui.theme import ColorPalette, FONT
from utils.config_manager import ConfigManager
from utils.history_manager import HistoryManager
from utils.logger import get_logger

logger = get_logger("ui.history")

_COLUMNS = ["Fecha", "Archivo", "Tipo", "Original", "Final", "Ahorro", "Reducción", "Tiempo"]
_COL_WIDTHS = [120, 240, 60, 90, 90, 90, 90, 70]


class HistoryView(ctk.CTkFrame):
    """
    Vista de historial con tabla, filtros y exportación de reportes.
    """

    def __init__(
        self,
        master: ctk.CTkFrame,
        palette: ColorPalette,
        config: ConfigManager,
    ) -> None:
        super().__init__(master, fg_color="transparent", corner_radius=0)
        self.palette = palette
        self.config = config
        self._manager = HistoryManager()
        self._build()
        self.refresh()

    def _build(self) -> None:
        """Construye la vista completa."""
        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            toolbar,
            text="Historial de compresiones",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_lg, weight="bold"),
            text_color=self.palette.text_primary,
        ).pack(side="left")

        # Botones
        btn_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_frame.pack(side="right")

        self._btn_export = ctk.CTkButton(
            btn_frame,
            text="📊 Exportar reporte",
            height=32,
            fg_color=self.palette.accent_primary,
            hover_color=self.palette.accent_hover,
            text_color=self.palette.text_on_accent,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
            corner_radius=6,
            command=self._export_report,
        )
        self._btn_export.pack(side="right", padx=(4, 0))

        ctk.CTkButton(
            btn_frame,
            text="🗑 Limpiar historial",
            height=32,
            fg_color="transparent",
            hover_color=self.palette.error_bg,
            border_width=1,
            border_color=self.palette.border,
            text_color=self.palette.text_secondary,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
            corner_radius=6,
            command=self._clear_history,
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            btn_frame,
            text="↻ Actualizar",
            height=32,
            fg_color="transparent",
            hover_color=self.palette.bg_hover,
            border_width=1,
            border_color=self.palette.border,
            text_color=self.palette.text_secondary,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
            corner_radius=6,
            command=self.refresh,
        ).pack(side="right", padx=4)

        # Stats summary
        self._stats_frame = ctk.CTkFrame(
            self,
            fg_color=self.palette.bg_card,
            corner_radius=8,
            border_width=1,
            border_color=self.palette.border,
            height=60,
        )
        self._stats_frame.pack(fill="x", pady=(0, 8))
        self._stats_frame.pack_propagate(False)
        self._build_stats_bar()

        # Tabla
        table_container = ctk.CTkFrame(
            self,
            fg_color=self.palette.bg_secondary,
            corner_radius=8,
            border_width=1,
            border_color=self.palette.border,
        )
        table_container.pack(fill="both", expand=True)

        # Encabezado tabla
        header = ctk.CTkFrame(
            table_container,
            fg_color=self.palette.bg_card,
            height=34,
            corner_radius=0,
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        for i, (col, w) in enumerate(zip(_COLUMNS, _COL_WIDTHS)):
            ctk.CTkLabel(
                header,
                text=col,
                font=ctk.CTkFont(family=FONT.family, size=FONT.size_xs, weight="bold"),
                text_color=self.palette.text_muted,
                width=w,
                anchor="w" if i == 1 else "center",
            ).pack(side="left", padx=(12 if i == 0 else 4, 4))

        # Scroll
        self._scroll = ctk.CTkScrollableFrame(
            table_container,
            fg_color="transparent",
            scrollbar_button_color=self.palette.border,
            scrollbar_button_hover_color=self.palette.accent_primary,
        )
        self._scroll.pack(fill="both", expand=True)
        # _empty_label se crea dinámicamente en refresh()

    def _build_stats_bar(self) -> None:
        """Panel de estadísticas globales."""
        inner = ctk.CTkFrame(self._stats_frame, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        self._stat_labels: dict[str, ctk.CTkLabel] = {}

        stats_defs = [
            ("total", "Total compresiones", "0"),
            ("saved", "Espacio total ahorrado", "0 B"),
            ("avg", "Reducción promedio", "0%"),
        ]

        for i, (key, label, default) in enumerate(stats_defs):
            if i > 0:
                ctk.CTkFrame(inner, width=1, fg_color=self.palette.border).pack(
                    side="left", fill="y", padx=20, pady=8
                )
            col = ctk.CTkFrame(inner, fg_color="transparent")
            col.pack(side="left", padx=16)

            val_lbl = ctk.CTkLabel(
                col,
                text=default,
                font=ctk.CTkFont(family=FONT.family, size=FONT.size_xl, weight="bold"),
                text_color=self.palette.accent_primary,
            )
            val_lbl.pack()
            ctk.CTkLabel(
                col,
                text=label,
                font=ctk.CTkFont(family=FONT.family, size=FONT.size_xs),
                text_color=self.palette.text_muted,
            ).pack()
            self._stat_labels[key] = val_lbl

    # ------------------------------------------------------------------
    # Métodos públicos
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Recarga el historial desde la base de datos."""
        # Limpiar filas anteriores
        for widget in self._scroll.winfo_children():
            widget.destroy()

        # Re-crear el empty_label (fue destruido en el clear)
        self._empty_label = ctk.CTkLabel(
            self._scroll,
            text="El historial está vacío.\nComienza a comprimir archivos para ver los registros aquí.",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_base),
            text_color=self.palette.text_muted,
        )

        entries = self._manager.get_all()
        stats = self._manager.get_stats()

        # Actualizar estadísticas
        from utils.file_utils import format_size
        self._stat_labels["total"].configure(text=str(stats.get("total", 0)))
        self._stat_labels["saved"].configure(text=format_size(stats.get("total_saved", 0)))
        self._stat_labels["avg"].configure(text=f"{stats.get('avg_reduction', 0):.1f}%")

        if not entries:
            self._empty_label.pack(expand=True, pady=40)
            return

        for i, entry in enumerate(entries):
            bg = self.palette.bg_card if i % 2 == 0 else "transparent"
            row = ctk.CTkFrame(self._scroll, fg_color=bg, height=36)
            row.pack(fill="x", padx=2, pady=0)
            row.pack_propagate(False)

            # Fecha
            self._hcell(row, entry.timestamp_str, 0)
            # Archivo
            name_lbl = ctk.CTkLabel(
                row,
                text=f"📄 {entry.filename}",
                font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
                text_color=self.palette.text_primary,
                width=_COL_WIDTHS[1],
                anchor="w",
            )
            name_lbl.pack(side="left", padx=(4, 4))
            # Tipo
            self._hcell(row, entry.file_type.upper(), 2)
            # Original
            self._hcell(row, entry.original_size_str, 3)
            # Final
            self._hcell(row, entry.final_size_str, 4)
            # Ahorro
            self._hcell(row, entry.bytes_saved_str, 5, color=self.palette.success)
            # Reducción
            self._hcell(row, f"{entry.reduction_percent:.1f}%", 6, color=self.palette.success)
            # Tiempo
            self._hcell(row, f"{entry.elapsed_seconds:.1f}s", 7)

    def _hcell(
        self,
        parent: ctk.CTkFrame,
        text: str,
        col: int,
        color: Optional[str] = None,
    ) -> None:
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_xs),
            text_color=color or self.palette.text_secondary,
            width=_COL_WIDTHS[col],
            anchor="center",
        ).pack(side="left", padx=4)

    def _clear_history(self) -> None:
        """Limpia el historial tras confirmación."""
        from tkinter import messagebox
        if messagebox.askyesno(
            "Confirmar",
            "¿Deseas eliminar todo el historial de comprensiones?\nEsta acción no se puede deshacer.",
        ):
            self._manager.clear()
            self.refresh()

    def _export_report(self) -> None:
        """Exporta el historial al formato seleccionado."""
        from ui.report_dialog import ReportDialog
        from ui.app import FileOptimizerApp

        root = self.winfo_toplevel()
        entries = self._manager.get_all()
        dialog = ReportDialog(root, self.palette, entries)
        dialog.grab_set()
