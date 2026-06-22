"""
ui/progress_panel.py
Panel de progreso global e individual.
"""

from __future__ import annotations
import tkinter as tk

import customtkinter as ctk

from ui.theme import ColorPalette, FONT


class ProgressPanel(ctk.CTkFrame):
    """
    Panel que muestra el progreso global del procesamiento.

    Muestra:
    - Barra de progreso global.
    - Conteo (X de N archivos).
    - Estado textual del archivo actual.
    """

    def __init__(self, master: ctk.CTkFrame, palette: ColorPalette) -> None:
        super().__init__(
            master,
            fg_color=palette.bg_card,
            corner_radius=8,
            border_width=1,
            border_color=palette.border,
            height=72,
        )
        self.palette = palette
        self.pack_propagate(False)
        self._total = 0
        self._completed = 0
        self._build()
        self._hide()

    def _build(self) -> None:
        """Construye los elementos del panel."""
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=8)

        # Fila superior: texto estado + contador
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x")

        self._status_label = ctk.CTkLabel(
            top_row,
            text="Procesando...",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
            text_color=self.palette.text_primary,
            anchor="w",
        )
        self._status_label.pack(side="left", fill="x", expand=True)

        self._count_label = ctk.CTkLabel(
            top_row,
            text="0 / 0",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm, weight="bold"),
            text_color=self.palette.accent_primary,
        )
        self._count_label.pack(side="right")

        # Barra de progreso
        self._progress_bar = ctk.CTkProgressBar(
            inner,
            height=8,
            corner_radius=4,
            progress_color=self.palette.accent_primary,
            fg_color=self.palette.border,
        )
        self._progress_bar.set(0)
        self._progress_bar.pack(fill="x", pady=(4, 0))

    def start(self, total: int) -> None:
        """Inicia el panel con el total de archivos a procesar."""
        self._total = total
        self._completed = 0
        self._progress_bar.set(0)
        self._count_label.configure(text=f"0 / {total}")
        self._status_label.configure(
            text="Iniciando compresión...",
            text_color=self.palette.text_primary,
        )
        self._show()

    def update_progress(self, file_name: str, completed: int) -> None:
        """Actualiza el progreso al completar un archivo."""
        self._completed = completed
        if self._total > 0:
            ratio = completed / self._total
            self._progress_bar.set(ratio)
            self._count_label.configure(text=f"{completed} / {self._total}")
        self._status_label.configure(
            text=f"Procesando: {file_name}",
            text_color=self.palette.text_primary,
        )

    def finish(self, total: int, success: int) -> None:
        """Muestra el mensaje final."""
        self._progress_bar.set(1.0)
        failed = total - success
        if failed == 0:
            msg = f"✓  {success} archivo(s) comprimidos exitosamente."
            color = self.palette.success
        else:
            msg = f"✓  {success} exitosos  ✗  {failed} con errores"
            color = self.palette.warning

        self._status_label.configure(text=msg, text_color=color)
        self._count_label.configure(text=f"{success} / {total}")

        # Ocultar automáticamente después de 5 segundos
        self.after(5000, self._hide)

    def _show(self) -> None:
        self.pack(fill="x", padx=12, pady=(0, 6))

    def _hide(self) -> None:
        self.pack_forget()
