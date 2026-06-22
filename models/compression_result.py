"""
models/compression_result.py
Resultado de una operación de compresión.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CompressionResult:
    """
    Resultado completo de comprimir un archivo.

    Attributes:
        success: True si la compresión fue exitosa.
        original_size: Tamaño original en bytes.
        final_size: Tamaño comprimido en bytes.
        output_path: Ruta del archivo resultante.
        elapsed_seconds: Tiempo de procesamiento en segundos.
        error_message: Mensaje de error si success == False.
        method_used: Método/motor de compresión utilizado.
    """
    success: bool
    original_size: int
    final_size: int = 0
    output_path: Optional[Path] = None
    elapsed_seconds: float = 0.0
    error_message: Optional[str] = None
    method_used: str = ""

    @property
    def bytes_saved(self) -> int:
        """Bytes ahorrados."""
        return max(0, self.original_size - self.final_size)

    @property
    def reduction_percent(self) -> float:
        """Porcentaje de reducción (0.0 - 100.0)."""
        if self.original_size == 0:
            return 0.0
        return round((self.bytes_saved / self.original_size) * 100, 2)

    @property
    def original_size_str(self) -> str:
        return _format_size(self.original_size)

    @property
    def final_size_str(self) -> str:
        return _format_size(self.final_size)

    @property
    def bytes_saved_str(self) -> str:
        return _format_size(self.bytes_saved)

    @property
    def elapsed_str(self) -> str:
        if self.elapsed_seconds < 60:
            return f"{self.elapsed_seconds:.1f}s"
        minutes = int(self.elapsed_seconds // 60)
        seconds = self.elapsed_seconds % 60
        return f"{minutes}m {seconds:.0f}s"

    @property
    def is_larger(self) -> bool:
        """True si el resultado es más grande que el original (compresión inefectiva)."""
        return self.final_size > self.original_size


def _format_size(size_bytes: int) -> str:
    """Formatea bytes a string legible."""
    if size_bytes == 0:
        return "0 B"
    value = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"
