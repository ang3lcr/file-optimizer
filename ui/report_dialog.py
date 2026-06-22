"""
ui/report_dialog.py
Diálogo modal para exportar reportes en PDF, XLSX o CSV.
"""

from __future__ import annotations
import tkinter as tk
from pathlib import Path
from typing import Sequence

import customtkinter as ctk

from ui.theme import ColorPalette, FONT
from models.history_entry import HistoryEntry
from utils.report_generator import ReportGenerator
from utils.logger import get_logger

logger = get_logger("ui.report")


class ReportDialog(ctk.CTkToplevel):
    """
    Ventana modal para exportar el historial a PDF, XLSX o CSV.
    """

    def __init__(
        self,
        master: ctk.CTk,
        palette: ColorPalette,
        entries: Sequence[HistoryEntry],
    ) -> None:
        super().__init__(master)
        self.palette = palette
        self.entries = entries
        self._generator = ReportGenerator()

        self.title("Exportar Reporte")
        self.geometry("420x300")
        self.resizable(False, False)
        self.configure(fg_color=palette.bg_primary)

        self._center()
        self._build()

    def _center(self) -> None:
        self.update_idletasks()
        master = self.master
        x = master.winfo_x() + (master.winfo_width() - 420) // 2
        y = master.winfo_y() + (master.winfo_height() - 300) // 2
        self.geometry(f"420x300+{x}+{y}")

    def _build(self) -> None:
        # Título
        ctk.CTkLabel(
            self,
            text="Exportar Reporte de Compresión",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_md, weight="bold"),
            text_color=self.palette.text_primary,
        ).pack(pady=(20, 4))

        ctk.CTkLabel(
            self,
            text=f"{len(self.entries)} registro(s) en el historial",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
            text_color=self.palette.text_muted,
        ).pack(pady=(0, 16))

        # Selector de formato
        ctk.CTkLabel(
            self,
            text="Formato de exportación:",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
            text_color=self.palette.text_secondary,
        ).pack(anchor="w", padx=24)

        self._format_var = tk.StringVar(value="PDF")
        formats = ctk.CTkSegmentedButton(
            self,
            values=["PDF", "XLSX", "CSV"],
            variable=self._format_var,
            fg_color=self.palette.bg_card,
            selected_color=self.palette.accent_primary,
            selected_hover_color=self.palette.accent_hover,
            unselected_color=self.palette.bg_card,
            unselected_hover_color=self.palette.bg_hover,
            text_color=self.palette.text_primary,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
        )
        formats.pack(padx=24, pady=(4, 16))

        # Estado
        self._status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
            text_color=self.palette.text_muted,
        )
        self._status_label.pack()

        # Botones
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=16, side="bottom")

        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            height=36,
            fg_color="transparent",
            hover_color=self.palette.bg_hover,
            border_width=1,
            border_color=self.palette.border,
            text_color=self.palette.text_secondary,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
            command=self.destroy,
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame,
            text="💾  Exportar",
            height=36,
            fg_color=self.palette.accent_primary,
            hover_color=self.palette.accent_hover,
            text_color=self.palette.text_on_accent,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm, weight="bold"),
            command=self._do_export,
        ).pack(side="right")

    def _do_export(self) -> None:
        """Ejecuta la exportación."""
        from tkinter import filedialog
        fmt = self._format_var.get()

        ext_map = {"PDF": ".pdf", "XLSX": ".xlsx", "CSV": ".csv"}
        ext = ext_map.get(fmt, ".pdf")

        filepath = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[(f"Archivo {fmt}", f"*{ext}")],
            initialfile=f"reporte_fileoptimizer{ext}",
            title=f"Guardar reporte {fmt}",
        )
        if not filepath:
            return

        path = Path(filepath)
        self._status_label.configure(
            text="Generando reporte...",
            text_color=self.palette.text_secondary,
        )
        self.update()

        if fmt == "PDF":
            success = self._generator.export_pdf(self.entries, path)
        elif fmt == "XLSX":
            success = self._generator.export_xlsx(self.entries, path)
        else:
            success = self._generator.export_csv(self.entries, path)

        if success:
            self._status_label.configure(
                text=f"✓ Exportado: {path.name}",
                text_color=self.palette.success,
            )
            # Abrir carpeta del reporte
            import subprocess
            subprocess.Popen(["explorer", "/select,", str(path)])
            self.after(2000, self.destroy)
        else:
            self._status_label.configure(
                text="✗ Error al exportar. Revisa los logs.",
                text_color=self.palette.error,
            )
