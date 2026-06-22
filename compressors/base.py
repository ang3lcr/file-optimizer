"""
compressors/base.py
Clase base abstracta para todos los motores de compresión.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from models.compression_profile import QualityLevel
from models.compression_result import CompressionResult


@dataclass
class CompressionOptions:
    """
    Opciones configurables para una operación de compresión.

    Attributes:
        quality_level: Nivel de calidad seleccionado.
        custom_quality: Calidad personalizada 1-100 (solo si quality_level == CUSTOM).
        remove_metadata: Si se deben eliminar metadatos del archivo.
        remove_revisions: Si se deben eliminar revisiones/comentarios (Office).
        convert_to_webp: Si las imágenes deben convertirse a WebP.
        output_path: Ruta de salida explícita. Si None, se genera automáticamente.
        cancelled: Flag de cancelación (puede ser modificado desde otro hilo).
        progress_callback: Función llamada con progreso 0.0-1.0.
    """
    quality_level: QualityLevel = QualityLevel.BALANCED
    custom_quality: int = 75
    remove_metadata: bool = True
    remove_revisions: bool = False
    convert_to_webp: bool = False
    output_path: Optional[Path] = None
    cancelled: bool = False
    progress_callback: Optional[Callable[[float], None]] = field(
        default=None, repr=False
    )

    def get_image_quality(self) -> int:
        """Retorna la calidad de imagen efectiva (0-100)."""
        if self.quality_level == QualityLevel.CUSTOM:
            return max(1, min(100, self.custom_quality))
        return self.quality_level.image_quality

    def report_progress(self, value: float) -> None:
        """Llama al callback de progreso si está definido."""
        if self.progress_callback:
            self.progress_callback(max(0.0, min(1.0, value)))


class CompressionEngine(ABC):
    """
    Interfaz base para todos los motores de compresión.

    Cada motor concreto implementa `compress()` para un tipo de archivo.
    Los motores NO deben bloquear; el llamador maneja el threading.
    """

    @abstractmethod
    def compress(
        self,
        input_path: Path,
        options: CompressionOptions,
    ) -> CompressionResult:
        """
        Comprime el archivo especificado.

        Args:
            input_path: Ruta al archivo original (no se modifica).
            options: Opciones de compresión configuradas por el usuario.

        Returns:
            CompressionResult con los detalles del resultado.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre del motor para logs y reportes."""
        ...

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Lista de extensiones soportadas (sin punto, minúsculas)."""
        ...

    def can_handle(self, path: Path) -> bool:
        """Retorna True si este motor puede comprimir el archivo."""
        return path.suffix.lower().lstrip(".") in self.supported_extensions
