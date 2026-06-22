"""
ui/drop_zone.py
Área de arrastrar y soltar archivos.
Usa tkinterdnd2 si está disponible, con fallback a selección de archivo.
"""

from __future__ import annotations
import tkinter as tk
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk

from ui.theme import ColorPalette, FONT
from utils.file_utils import collect_files_from_paths, is_supported
from utils.logger import get_logger

logger = get_logger("ui.drop_zone")


class DropZone(ctk.CTkFrame):
    """
    Área de arrastre de archivos con animación de hover.

    Permite:
    - Arrastrar archivos y carpetas (usando tkinterdnd2 si disponible).
    - Clic para abrir selector de archivos estándar.
    - Clic secundario para abrir selector de carpeta.
    """

    def __init__(
        self,
        master: ctk.CTkFrame,
        palette: ColorPalette,
        on_files_dropped: Callable[[list[Path]], None],
    ) -> None:
        super().__init__(
            master,
            height=140,
            corner_radius=12,
            fg_color=palette.drop_bg,
            border_width=2,
            border_color=palette.drop_border,
        )
        self.palette = palette
        self.on_files_dropped = on_files_dropped
        self.pack_propagate(False)

        self._build_content()
        self._setup_drag_drop()
        self._bind_click()

    def _build_content(self) -> None:
        """Construye el contenido visual de la zona de drop."""
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.place(relx=0.5, rely=0.5, anchor="center")

        # Ícono animado
        self._icon_label = ctk.CTkLabel(
            container,
            text="📂",
            font=ctk.CTkFont(size=34),
        )
        self._icon_label.pack()

        # Texto principal
        ctk.CTkLabel(
            container,
            text="Arrastra archivos o carpetas aquí",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_md, weight="bold"),
            text_color=self.palette.text_primary,
        ).pack(pady=(4, 2))

        # Texto secundario
        ctk.CTkLabel(
            container,
            text="o haz clic para seleccionar • Clic derecho para seleccionar carpeta",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_sm),
            text_color=self.palette.text_secondary,
        ).pack()

        # Formatos soportados
        ctk.CTkLabel(
            container,
            text="PDF • JPG • PNG • DOCX • XLSX • PPTX • JSON • XML • HTML • TXT",
            font=ctk.CTkFont(family=FONT.family, size=FONT.size_xs),
            text_color=self.palette.text_muted,
        ).pack(pady=(4, 0))

    def _setup_drag_drop(self) -> None:
        """Configura drag & drop usando tkinterdnd2."""
        try:
            import tkinterdnd2 as dnd  # type: ignore[import]

            # tkinterdnd2 requiere que el root sea TkinterDnD.Tk
            # Si el root soporta DnD, registrar la zona
            root = self.winfo_toplevel()
            if hasattr(root, "drop_target_register"):
                self.drop_target_register = dnd.DND_FILES  # type: ignore[attr-defined]
                self.dnd_bind("<<Drop>>", self._on_dnd_drop)  # type: ignore[attr-defined]
                self.dnd_bind("<<DragEnter>>", self._on_drag_enter)  # type: ignore[attr-defined]
                self.dnd_bind("<<DragLeave>>", self._on_drag_leave)  # type: ignore[attr-defined]
                logger.debug("DnD registrado con tkinterdnd2.")
        except ImportError:
            logger.debug("tkinterdnd2 no disponible. Solo selección por clic.")
        except Exception as exc:
            logger.debug("Error configurando DnD: %s", exc)

    def _bind_click(self) -> None:
        """Registra eventos de clic para selección de archivos."""
        for widget in self.winfo_children() + [self]:
            widget.bind("<Button-1>", self._on_click_select_files, add=True)
            widget.bind("<Button-3>", self._on_click_select_folder, add=True)
            widget.bind("<Enter>", self._on_mouse_enter, add=True)
            widget.bind("<Leave>", self._on_mouse_leave, add=True)

        self.configure(cursor="hand2")

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _on_dnd_drop(self, event: tk.Event) -> None:
        """Maneja archivos soltados por drag & drop."""
        self._on_drag_leave(event)
        raw = event.data  # type: ignore[attr-defined]
        paths = _parse_dnd_paths(raw)
        self._process_paths(paths)

    def _on_drag_enter(self, event: tk.Event) -> None:
        """Highlight al entrar con un archivo."""
        self.configure(
            border_color=self.palette.accent_primary,
            fg_color=self.palette.accent_light,
        )
        self._icon_label.configure(text="📥")

    def _on_drag_leave(self, event: tk.Event) -> None:
        """Restaura estado normal al salir."""
        self.configure(
            border_color=self.palette.drop_border,
            fg_color=self.palette.drop_bg,
        )
        self._icon_label.configure(text="📂")

    def _on_mouse_enter(self, event: tk.Event) -> None:
        self.configure(border_color=self.palette.accent_primary)

    def _on_mouse_leave(self, event: tk.Event) -> None:
        self.configure(border_color=self.palette.drop_border)

    def _on_click_select_files(self, event: tk.Event) -> None:
        """Abre selector de múltiples archivos."""
        from tkinter import filedialog
        from utils.file_utils import SUPPORTED_EXTENSIONS

        # Construir filtros
        all_exts = " ".join(
            f"*.{ext}"
            for exts in SUPPORTED_EXTENSIONS.values()
            for ext in exts
        )
        filetypes = [
            ("Todos los formatos soportados", all_exts),
            ("PDF", "*.pdf"),
            ("Imágenes", "*.jpg *.jpeg *.png *.webp *.bmp *.gif *.tiff"),
            ("Office", "*.docx *.xlsx *.pptx *.xls *.ods"),
            ("Texto", "*.txt *.json *.xml *.html *.csv *.rtf *.odt"),
        ]

        files = filedialog.askopenfilenames(
            title="Seleccionar archivos a comprimir",
            filetypes=filetypes,
        )
        if files:
            self._process_paths([Path(f) for f in files])

    def _on_click_select_folder(self, event: tk.Event) -> None:
        """Abre selector de carpeta."""
        from tkinter import filedialog

        folder = filedialog.askdirectory(title="Seleccionar carpeta a comprimir")
        if folder:
            self._process_paths([Path(folder)])

    def _process_paths(self, paths: list[Path]) -> None:
        """Expande carpetas, filtra soportados y notifica."""
        files = collect_files_from_paths(paths)
        if files:
            logger.info("%d archivo(s) agregado(s).", len(files))
            self.on_files_dropped(files)
        else:
            logger.warning("No se encontraron archivos soportados en la selección.")


def _parse_dnd_paths(raw: str) -> list[Path]:
    """
    Parsea la cadena de rutas que devuelve tkinterdnd2.
    Las rutas pueden estar separadas por espacios o encerradas en llaves {}.
    """
    paths: list[Path] = []
    raw = raw.strip()

    # Extraer rutas entre llaves (rutas con espacios)
    import re
    braced = re.findall(r"\{([^}]+)\}", raw)
    for p in braced:
        raw = raw.replace(f"{{{p}}}", "")
        paths.append(Path(p.strip()))

    # El resto son rutas sin espacios
    for p in raw.split():
        p = p.strip()
        if p:
            paths.append(Path(p))

    return paths
