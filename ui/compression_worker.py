"""
ui/compression_worker.py
Gestiona el procesamiento asíncrono de archivos en hilos de fondo.
"""

from __future__ import annotations
import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from typing import Callable, Optional

import customtkinter as ctk

from models.file_item import FileItem
from models.compression_result import CompressionResult
from compressors.base import CompressionOptions
from compressors.dispatcher import get_engine
from utils.logger import get_logger

logger = get_logger("worker")

# Número máximo de hilos concurrentes
_MAX_WORKERS = 3


class CompressionWorker:
    """
    Ejecuta la compresión de múltiples archivos en hilos de fondo.

    Mantiene la GUI responsiva usando threading.
    Notifica el progreso a la GUI a través de callbacks thread-safe
    usando el método `after()` de tkinter.

    Args:
        files: Lista de FileItems a comprimir.
        options: Opciones de compresión base.
        on_file_start: Callback (file_id) cuando inicia un archivo.
        on_file_progress: Callback (file_id, float) con progreso 0-1.
        on_file_done: Callback (file_id, CompressionResult) al terminar.
        on_all_done: Callback (total, success_count) al finalizar todo.
        progress_panel: Referencia al panel de progreso para actualizaciones globales.
    """

    def __init__(
        self,
        files: list[FileItem],
        options: CompressionOptions,
        on_file_start: Callable[[str], None],
        on_file_progress: Callable[[str, float], None],
        on_file_done: Callable[[str, CompressionResult], None],
        on_all_done: Callable[[int, int], None],
        progress_panel: Optional[object] = None,
    ) -> None:
        self._files = files
        self._options = options
        self._on_file_start = on_file_start
        self._on_file_progress = on_file_progress
        self._on_file_done = on_file_done
        self._on_all_done = on_all_done
        self._progress_panel = progress_panel
        self._cancelled = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Inicia el procesamiento en un hilo de fondo."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def cancel(self) -> None:
        """Señaliza la cancelación del procesamiento."""
        self._cancelled = True
        self._options.cancelled = True
        logger.info("Cancelación solicitada.")

    def _run(self) -> None:
        """Hilo principal de procesamiento."""
        total = len(self._files)
        success_count = 0
        completed = 0

        logger.info("Iniciando compresión de %d archivo(s).", total)

        # Procesar secuencialmente para archivos grandes o con CPU intensivo
        # (se puede cambiar a ThreadPoolExecutor con max_workers para batch)
        for item in self._files:
            if self._cancelled:
                break

            # Notificar inicio (thread-safe via after)
            self._gui_call(self._on_file_start, item.id)

            # Crear opciones con callback de progreso thread-safe
            opts = CompressionOptions(
                quality_level=self._options.quality_level,
                custom_quality=self._options.custom_quality,
                remove_metadata=self._options.remove_metadata,
                remove_revisions=self._options.remove_revisions,
                convert_to_webp=self._options.convert_to_webp,
                cancelled=False,
                progress_callback=lambda p, fid=item.id: self._gui_call(
                    self._on_file_progress, fid, p
                ),
            )

            # Obtener motor
            engine = get_engine(item.path)
            if engine is None:
                result = CompressionResult(
                    success=False,
                    original_size=item.original_size,
                    error_message="Formato no soportado.",
                    method_used="—",
                )
            else:
                try:
                    result = engine.compress(item.path, opts)
                except Exception as exc:
                    logger.exception("Error inesperado comprimiendo %s: %s", item.name, exc)
                    result = CompressionResult(
                        success=False,
                        original_size=item.original_size,
                        error_message=str(exc),
                        method_used=engine.name if engine else "—",
                    )

            completed += 1
            if result.success:
                success_count += 1

            # Notificar resultado
            self._gui_call(self._on_file_done, item.id, result)

            # Actualizar panel de progreso global
            if self._progress_panel:
                self._gui_call(
                    self._progress_panel.update_progress,  # type: ignore[attr-defined]
                    item.name,
                    completed,
                )

        logger.info(
            "Compresión finalizada: %d/%d exitosos.", success_count, total
        )
        self._gui_call(self._on_all_done, total if not self._cancelled else completed, success_count)

    def _gui_call(self, fn: Callable, *args) -> None:
        """
        Ejecuta una función en el hilo de la GUI de forma thread-safe.
        Usa `after(0, ...)` de tkinter para encolar en el loop principal.
        """
        try:
            import tkinter as tk
            # Buscar ventana raíz activa
            root = tk._default_root  # type: ignore[attr-defined]
            if root is not None:
                root.after(0, lambda f=fn, a=args: f(*a))
            else:
                fn(*args)
        except Exception:
            try:
                fn(*args)
            except Exception as exc:
                logger.debug("Error en GUI callback: %s", exc)
