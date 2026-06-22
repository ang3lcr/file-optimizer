"""
models/file_item.py
Representa un archivo en la cola de procesamiento.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
import uuid


class FileStatus(Enum):
    """Estado de procesamiento de un archivo."""
    PENDING = "pending"           # En cola
    ANALYZING = "analyzing"       # Analizando perfil
    PROCESSING = "processing"     # Comprimiendo
    COMPLETED = "completed"       # Terminado exitosamente
    ERROR = "error"               # Error durante compresión
    CANCELLED = "cancelled"       # Cancelado por el usuario

    @property
    def label(self) -> str:
        labels = {
            "pending": "Pendiente",
            "analyzing": "Analizando...",
            "processing": "Procesando...",
            "completed": "Completado",
            "error": "Error",
            "cancelled": "Cancelado",
        }
        return labels[self.value]

    @property
    def color(self) -> str:
        """Color hex asociado al estado."""
        colors = {
            "pending": "#6B7280",
            "analyzing": "#3B82F6",
            "processing": "#F59E0B",
            "completed": "#10B981",
            "error": "#EF4444",
            "cancelled": "#9CA3AF",
        }
        return colors[self.value]


@dataclass
class FileItem:
    """
    Representa un archivo en la cola de compresión.

    Attributes:
        path: Ruta absoluta al archivo original.
        id: Identificador único (UUID generado automáticamente).
        status: Estado actual del procesamiento.
        error_message: Mensaje de error si status == ERROR.
        progress: Progreso individual 0.0 - 1.0.
    """
    path: Path
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: FileStatus = FileStatus.PENDING
    error_message: Optional[str] = None
    progress: float = 0.0

    def __post_init__(self) -> None:
        if isinstance(self.path, str):
            self.path = Path(self.path)

    @property
    def name(self) -> str:
        """Nombre del archivo con extensión."""
        return self.path.name

    @property
    def extension(self) -> str:
        """Extensión en minúsculas sin punto."""
        return self.path.suffix.lower().lstrip(".")

    @property
    def original_size(self) -> int:
        """Tamaño original en bytes."""
        try:
            return self.path.stat().st_size
        except OSError:
            return 0

    @property
    def original_size_str(self) -> str:
        """Tamaño original formateado."""
        return _format_size(self.original_size)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FileItem):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


def _format_size(size_bytes: int) -> str:
    """Formatea bytes a string legible."""
    if size_bytes == 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024  # type: ignore[assignment]
    return f"{size_bytes:.1f} TB"
