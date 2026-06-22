"""
utils/profile_analyzer.py
Analiza un archivo y recomienda la configuración de compresión óptima.
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from .file_utils import detect_file_type, format_size
from .logger import get_logger
from models.compression_profile import QualityLevel

logger = get_logger("profile_analyzer")


@dataclass
class CompressionProfile:
    """Perfil de compresión recomendado para un archivo."""
    recommended_quality: QualityLevel
    estimated_reduction_percent: float   # Estimación (0-100)
    method_description: str
    notes: str = ""

    @property
    def estimated_reduction_str(self) -> str:
        return f"~{self.estimated_reduction_percent:.0f}%"


# Umbrales de tamaño (bytes)
_10_MB = 10 * 1024 * 1024
_5_MB = 5 * 1024 * 1024
_1_MB = 1 * 1024 * 1024


def analyze(path: Path) -> CompressionProfile:
    """
    Analiza un archivo y devuelve un perfil de compresión recomendado.

    El análisis es heurístico (basado en tipo y tamaño) sin leer el contenido
    completo del archivo, para ser rápido y no bloquear la UI.

    Args:
        path: Ruta al archivo a analizar.

    Returns:
        CompressionProfile con la recomendación.
    """
    file_type = detect_file_type(path)
    size = path.stat().st_size if path.exists() else 0
    ext = path.suffix.lower().lstrip(".")

    logger.debug("Analizando %s (tipo=%s, tamaño=%s)", path.name, file_type, format_size(size))

    if file_type == "pdf":
        return _analyze_pdf(size)
    elif file_type == "image":
        return _analyze_image(size, ext)
    elif file_type == "office":
        return _analyze_office(size, ext)
    elif file_type == "text":
        return _analyze_text(size, ext)
    else:
        return CompressionProfile(
            recommended_quality=QualityLevel.BALANCED,
            estimated_reduction_percent=10.0,
            method_description="Formato no optimizable",
            notes="El formato no tiene un motor de compresión específico.",
        )


def _analyze_pdf(size: int) -> CompressionProfile:
    if size > _10_MB:
        return CompressionProfile(
            recommended_quality=QualityLevel.HIGH_COMPRESSION,
            estimated_reduction_percent=65.0,
            method_description="pikepdf + re-renderizado de imágenes internas",
            notes="Archivo grande. Se recomienda alta compresión para reducción máxima.",
        )
    elif size > _5_MB:
        return CompressionProfile(
            recommended_quality=QualityLevel.BALANCED,
            estimated_reduction_percent=50.0,
            method_description="pikepdf + optimización de imágenes",
            notes="Tamaño moderado. Compresión equilibrada.",
        )
    else:
        return CompressionProfile(
            recommended_quality=QualityLevel.HIGH,
            estimated_reduction_percent=35.0,
            method_description="pikepdf + eliminación de metadatos",
            notes="Archivo pequeño. Alta calidad con ligera optimización.",
        )


def _analyze_image(size: int, ext: str) -> CompressionProfile:
    if ext in ("bmp", "tiff", "tif"):
        return CompressionProfile(
            recommended_quality=QualityLevel.HIGH,
            estimated_reduction_percent=70.0,
            method_description="Conversión a JPEG/WebP + ajuste de calidad",
            notes="Formato sin compresión nativa. Conversión recomendada.",
        )
    elif ext == "png":
        return CompressionProfile(
            recommended_quality=QualityLevel.HIGH,
            estimated_reduction_percent=40.0,
            method_description="Optimización PNG + reducción de paleta",
            notes="PNG puede conservar transparencia.",
        )
    elif ext in ("jpg", "jpeg"):
        if size > _1_MB:
            return CompressionProfile(
                recommended_quality=QualityLevel.BALANCED,
                estimated_reduction_percent=45.0,
                method_description="Re-compresión JPEG con calidad optimizada",
            )
        return CompressionProfile(
            recommended_quality=QualityLevel.HIGH,
            estimated_reduction_percent=25.0,
            method_description="Ligera re-compresión JPEG",
        )
    else:
        return CompressionProfile(
            recommended_quality=QualityLevel.BALANCED,
            estimated_reduction_percent=35.0,
            method_description="Conversión a formato eficiente",
        )


def _analyze_office(size: int, ext: str) -> CompressionProfile:
    if ext == "pptx":
        return CompressionProfile(
            recommended_quality=QualityLevel.BALANCED,
            estimated_reduction_percent=40.0,
            method_description="Optimización de imágenes + recompresión ZIP",
            notes="Las presentaciones suelen tener imágenes de alta resolución.",
        )
    elif ext in ("xlsx", "xls", "ods"):
        return CompressionProfile(
            recommended_quality=QualityLevel.HIGH,
            estimated_reduction_percent=20.0,
            method_description="Limpieza de estilos + recompresión ZIP",
            notes="Hojas de cálculo tienen compresión limitada salvo imágenes embebidas.",
        )
    else:  # docx
        return CompressionProfile(
            recommended_quality=QualityLevel.BALANCED,
            estimated_reduction_percent=30.0,
            method_description="Optimización de imágenes + limpieza de metadatos",
        )


def _analyze_text(size: int, ext: str) -> CompressionProfile:
    if ext in ("json", "xml", "html", "htm"):
        return CompressionProfile(
            recommended_quality=QualityLevel.HIGH_COMPRESSION,
            estimated_reduction_percent=60.0,
            method_description="Minificación de whitespace y comentarios",
            notes="Archivos de marcado pueden reducirse significativamente.",
        )
    else:
        return CompressionProfile(
            recommended_quality=QualityLevel.BALANCED,
            estimated_reduction_percent=20.0,
            method_description="Limpieza de espacios redundantes",
        )
