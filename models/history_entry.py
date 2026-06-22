"""
models/history_entry.py
Entrada del historial de comprensiones realizadas.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class HistoryEntry:
    """
    Registro persistente de una compresión realizada.

    Attributes:
        id: Identificador único en la base de datos.
        timestamp: Fecha y hora del procesamiento.
        filename: Nombre del archivo procesado.
        file_type: Tipo/extensión del archivo.
        original_size: Tamaño original en bytes.
        final_size: Tamaño final en bytes.
        reduction_percent: Porcentaje de reducción.
        elapsed_seconds: Tiempo de procesamiento.
        output_path: Ruta del archivo resultante.
        method_used: Motor de compresión utilizado.
        success: Si la operación fue exitosa.
    """
    filename: str
    file_type: str
    original_size: int
    final_size: int
    reduction_percent: float
    elapsed_seconds: float
    output_path: str
    method_used: str
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    id: Optional[int] = None

    @property
    def timestamp_str(self) -> str:
        return self.timestamp.strftime("%d/%m/%Y %H:%M")

    @property
    def original_size_str(self) -> str:
        return _format_size(self.original_size)

    @property
    def final_size_str(self) -> str:
        return _format_size(self.final_size)

    @property
    def bytes_saved(self) -> int:
        return max(0, self.original_size - self.final_size)

    @property
    def bytes_saved_str(self) -> str:
        return _format_size(self.bytes_saved)

    def to_dict(self) -> dict:
        """Serializa para exportación CSV/XLSX."""
        return {
            "Fecha": self.timestamp_str,
            "Archivo": self.filename,
            "Tipo": self.file_type.upper(),
            "Tamaño Original": self.original_size_str,
            "Tamaño Final": self.final_size_str,
            "Ahorro": self.bytes_saved_str,
            "Reducción %": f"{self.reduction_percent:.1f}%",
            "Tiempo": f"{self.elapsed_seconds:.1f}s",
            "Método": self.method_used,
            "Estado": "Exitoso" if self.success else "Error",
        }


def _format_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    value = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"
