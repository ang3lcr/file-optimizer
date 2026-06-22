"""
models/compression_profile.py
Define los niveles de calidad y modos de compresión disponibles.
"""

from enum import Enum


class QualityLevel(Enum):
    """Niveles de calidad de compresión."""
    MAXIMUM = "maximum"          # Máxima calidad (mínima compresión)
    HIGH = "high"                # Alta calidad
    BALANCED = "balanced"        # Calidad equilibrada
    HIGH_COMPRESSION = "high_compression"  # Alta compresión
    EXTREME = "extreme"          # Compresión extrema (menor calidad)
    CUSTOM = "custom"            # Personalizado

    @property
    def label(self) -> str:
        """Etiqueta legible en español."""
        labels = {
            "maximum": "Máxima calidad",
            "high": "Alta calidad",
            "balanced": "Calidad equilibrada",
            "high_compression": "Alta compresión",
            "extreme": "Compresión extrema",
            "custom": "Personalizado",
        }
        return labels[self.value]

    @property
    def image_quality(self) -> int:
        """Calidad de imagen asociada (0-100)."""
        qualities = {
            "maximum": 95,
            "high": 85,
            "balanced": 75,
            "high_compression": 55,
            "extreme": 30,
            "custom": 75,
        }
        return qualities[self.value]

    @property
    def pdf_dpi(self) -> int:
        """DPI para re-renderizado de imágenes en PDF."""
        dpis = {
            "maximum": 200,
            "high": 150,
            "balanced": 120,
            "high_compression": 96,
            "extreme": 72,
            "custom": 120,
        }
        return dpis[self.value]


class CompressionMode(Enum):
    """Modo de detección del tipo de compresión."""
    AUTO = "auto"          # Detección automática por extensión
    PDF = "pdf"
    IMAGE = "image"
    OFFICE = "office"
    TEXT = "text"

    @property
    def label(self) -> str:
        labels = {
            "auto": "Automático",
            "pdf": "PDF",
            "image": "Imagen",
            "office": "Office",
            "text": "Texto",
        }
        return labels[self.value]
