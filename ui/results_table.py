"""
ui/results_table.py
Tabla de resultados de compresión con actualización en tiempo real.
"""

from __future__ import annotations
import tkinter as tk
from pathlib import Path
from typing import Optional

import customtkinter as ctk

from ui.theme import ColorPalette, FONT
from models.file_item import FileItem, FileStatus
from models.compression_result import CompressionResult
from utils.file_utils import detect_file_type, format_size
from utils.logger import get_logger

logger = get_logger("ui.results_table")

# Columnas de la tabla
_COLUMNS = ["Archivo", "Tipo", "Original", "Final", "Reducción", "Estado", "Acción"]
_COL_WIDTHS = [260, 60, 90, 90, 90, 110, 70]


class ResultsTable(ctk.CTkFrame):
    """
    Tabla scrolleable de resultados de compresión.

    Muestra en tiempo real el estado de cada archivo:
    - Pendiente, Procesando, Completado, Error, Cancelado.
    """

    def __init__(self, master: ctk.CTkFrame, palette: ColorPalette) -> None:
        super().__init__(
            master,
            fg_color=palette.bg_secondary,
            corner_radius=8,
            border_width=1,
            border_color=palette.border,
        )
        self.palette = palette

        self._items: dict[str, FileItem] = {}      # id → FileItem
        self._rows: dict[str, dict] = {}            # id → dict de widgets de fila
        self._results: dict[str, CompressionResult] = {}  # id → resultado

        self._build()

    def _build(self) -> None:
        """Construye el encabezado y el área scrolleable."""
        # Encabezado
        header = ctk.CTkFrame(
            self,
            fg_color=self.palette.bg_card,
            corner_radius=0,
            height=36,
        )
        header.pack(fill="x", padx=1, pady=(1, 0))
        header.pack_propagate(False)

        for col, (name, width) in enumerate(zip(_COLUMNS, _COL_WIDTHS)):
            ctk.CTkLabel(
                header,
                text=name,
                font=ctk.CTkFont(family=FONT.family, size=FONT.size_xs, weight="bold"),
                text_color=self.palette.text_muted,
                width=width,
                anchor="w" if col == 0 else "center",
            ).pack(side="left", padx=(12 if col == 0 else 4, 4))

        # Área de datos scrolleable
        self._scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.palette.border,
            scrollbar_button_hover_color=self.palette.accent_primary,
        )
        self._scroll.pack(fill="both", expand=True, padx=1, pady=(0, 1))

        # Placeholder cuando está vacío
        self._empty_label = ctk.CTkLabel(
            self._scroll,
            text="No hay archivos en la lista.\nArrastra archivos o usa el selector.",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_base),
            text_color=self.palette.text_muted,
        )
        self._empty_label.pack(expand=True, pady=40)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def add_files(self, paths: list[Path]) -> None:
        """Agrega archivos a la tabla con estado PENDING."""
        new_added = False
        for path in paths:
            # Evitar duplicados
            if any(item.path == path for item in self._items.values()):
                continue
            item = FileItem(path=path)
            self._items[item.id] = item
            self._add_row(item)
            new_added = True

        if new_added:
            self._empty_label.pack_forget()

    def get_pending_files(self) -> list[FileItem]:
        """Retorna archivos con estado PENDING o ERROR (reintentar)."""
        return [
            item for item in self._items.values()
            if item.status in (FileStatus.PENDING, FileStatus.ERROR)
        ]

    def get_filename(self, file_id: str) -> str:
        item = self._items.get(file_id)
        return item.name if item else ""

    def get_filetype(self, file_id: str) -> str:
        item = self._items.get(file_id)
        return item.extension if item else ""

    def clear_all(self) -> None:
        """Elimina todos los archivos de la tabla."""
        for row_widgets in self._rows.values():
            row_widgets["frame"].destroy()
        self._items.clear()
        self._rows.clear()
        self._results.clear()
        self._empty_label.pack(expand=True, pady=40)

    # ------------------------------------------------------------------
    # Callbacks de estado (llamados desde el worker)
    # ------------------------------------------------------------------

    def on_file_start(self, file_id: str) -> None:
        """Marca un archivo como 'Procesando...'"""
        self._update_item_status(file_id, FileStatus.PROCESSING)

    def on_file_progress(self, file_id: str, progress: float) -> None:
        """Actualiza la barra de progreso de un archivo."""
        if file_id in self._rows and "progress" in self._rows[file_id]:
            try:
                self._rows[file_id]["progress"].set(progress)
            except Exception:
                pass

    def on_file_done(self, file_id: str, result: CompressionResult) -> None:
        """Actualiza la fila con el resultado final."""
        self._results[file_id] = result
        if file_id in self._items:
            self._items[file_id].status = (
                FileStatus.COMPLETED if result.success else FileStatus.ERROR
            )

        self._update_row_result(file_id, result)
        self._update_sidebar_stats()

    # ------------------------------------------------------------------
    # Construcción de filas
    # ------------------------------------------------------------------

    def _add_row(self, item: FileItem) -> None:
        """Crea y agrega una fila para un FileItem."""
        row_frame = ctk.CTkFrame(
            self._scroll,
            fg_color="transparent",
            height=44,
        )
        row_frame.pack(fill="x", padx=4, pady=1)
        row_frame.pack_propagate(False)

        # Línea divisoria entre filas
        ctk.CTkFrame(
            row_frame,
            height=1,
            fg_color=self.palette.border,
        ).place(x=0, rely=0, relwidth=1)

        widgets: dict = {"frame": row_frame}

        # Nombre del archivo (con ícono según tipo)
        icon = _file_icon(item.extension)
        name_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=_COL_WIDTHS[0])
        name_frame.pack(side="left", fill="y", padx=(12, 4))
        name_frame.pack_propagate(False)

        ctk.CTkLabel(
            name_frame,
            text=f"{icon} {item.name}",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
            text_color=self.palette.text_primary,
            anchor="w",
        ).pack(fill="both", expand=True)

        # Tipo
        widgets["type"] = self._cell(row_frame, item.extension.upper(), 1)

        # Tamaño original
        widgets["original"] = self._cell(row_frame, format_size(item.original_size), 2)

        # Final (placeholder)
        widgets["final"] = self._cell(row_frame, "—", 3)

        # Reducción
        widgets["reduction"] = self._cell(row_frame, "—", 4)

        # Estado
        status_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=_COL_WIDTHS[5])
        status_frame.pack(side="left", padx=4)
        status_frame.pack_propagate(False)

        status_label = ctk.CTkLabel(
            status_frame,
            text=item.status.label,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_xs),
            text_color=item.status.color,
            width=_COL_WIDTHS[5],
        )
        status_label.pack(fill="both", expand=True)
        widgets["status"] = status_label

        # Mini progress bar (oculta inicialmente)
        progress_bar = ctk.CTkProgressBar(
            status_frame,
            height=3,
            progress_color=self.palette.accent_primary,
            fg_color=self.palette.border,
        )
        progress_bar.set(0)
        widgets["progress"] = progress_bar

        # Botón de acción (eliminar)
        action_btn = ctk.CTkButton(
            row_frame,
            text="✕",
            width=28,
            height=28,
            fg_color="transparent",
            hover_color=self.palette.bg_hover,
            text_color=self.palette.text_muted,
            font=ctk.CTkFont(size=11),
            corner_radius=4,
            command=lambda fid=item.id: self._remove_row(fid),
        )
        action_btn.pack(side="left", padx=4)
        widgets["action_btn"] = action_btn

        self._rows[item.id] = widgets

    def _cell(self, parent: ctk.CTkFrame, text: str, col_idx: int) -> ctk.CTkLabel:
        """Crea una celda de texto centrada."""
        lbl = ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
            text_color=self.palette.text_secondary,
            width=_COL_WIDTHS[col_idx],
            anchor="center",
        )
        lbl.pack(side="left", padx=4)
        return lbl

    # ------------------------------------------------------------------
    # Actualización de filas
    # ------------------------------------------------------------------

    def _update_item_status(self, file_id: str, status: FileStatus) -> None:
        if file_id in self._items:
            self._items[file_id].status = status
        if file_id in self._rows:
            row = self._rows[file_id]
            row["status"].configure(
                text=status.label,
                text_color=status.color,
            )
            if status == FileStatus.PROCESSING:
                row["progress"].pack(fill="x", padx=4)
                row["status"].pack_forget()
                row["progress"].pack(fill="x")
            else:
                row["progress"].pack_forget()
                row["status"].pack(fill="both", expand=True)

    def _update_row_result(self, file_id: str, result: CompressionResult) -> None:
        """Actualiza la fila con los datos del resultado."""
        if file_id not in self._rows:
            return
        row = self._rows[file_id]

        # Ocultar progress bar
        row["progress"].pack_forget()
        row["status"].pack(fill="both", expand=True)

        if result.success:
            status = FileStatus.COMPLETED
            row["final"].configure(text=result.final_size_str)
            reduction_text = f"{result.reduction_percent:.1f}%"
            color = self.palette.success if result.reduction_percent > 5 else self.palette.warning
            row["reduction"].configure(text=reduction_text, text_color=color)
        else:
            status = FileStatus.ERROR
            row["final"].configure(text="Error")
            row["reduction"].configure(text="—")

        row["status"].configure(
            text=status.label,
            text_color=status.color,
        )

    def _remove_row(self, file_id: str) -> None:
        """Elimina una fila de la tabla."""
        if file_id in self._rows:
            self._rows[file_id]["frame"].destroy()
            del self._rows[file_id]
        self._items.pop(file_id, None)
        self._results.pop(file_id, None)

        if not self._items:
            self._empty_label.pack(expand=True, pady=40)

    def _update_sidebar_stats(self) -> None:
        """Actualiza las estadísticas en el sidebar."""
        try:
            total_saved = sum(
                r.bytes_saved for r in self._results.values() if r.success
            )
            total_completed = sum(1 for r in self._results.values() if r.success)
            avg_reduction = (
                sum(r.reduction_percent for r in self._results.values() if r.success)
                / total_completed
                if total_completed > 0
                else 0.0
            )

            # Navegar hasta el sidebar
            app = self.winfo_toplevel()
            if hasattr(app, "main_window") and hasattr(app.main_window, "sidebar"):
                app.main_window.sidebar.update_stats(
                    total_completed, total_saved, avg_reduction
                )
        except Exception:
            pass


def _file_icon(ext: str) -> str:
    """Retorna un emoji según el tipo de archivo."""
    icons = {
        "pdf": "📄",
        "jpg": "🖼", "jpeg": "🖼", "png": "🖼", "webp": "🖼",
        "bmp": "🖼", "gif": "🖼", "tiff": "🖼", "tif": "🖼",
        "docx": "📝", "doc": "📝", "rtf": "📝", "odt": "📝",
        "xlsx": "📊", "xls": "📊", "ods": "📊", "csv": "📊",
        "pptx": "📋",
        "json": "🔧", "xml": "🔧", "html": "🌐", "htm": "🌐",
        "txt": "📃",
    }
    return icons.get(ext.lower(), "📁")
