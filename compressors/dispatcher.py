"""
compressors/dispatcher.py
Selecciona el motor de compresión adecuado para cada archivo.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional

from .base import CompressionEngine
from utils.file_utils import detect_file_type
from utils.logger import get_logger

logger = get_logger("dispatcher")

# Importación lazy para evitar fallos si una librería no está instalada
_engines: Optional[dict[str, CompressionEngine]] = None


def _build_engines() -> dict[str, CompressionEngine]:
    """Instancia todos los motores disponibles."""
    engines: dict[str, CompressionEngine] = {}

    try:
        from compressors.pdf.pdf_compressor import PdfCompressor
        engines["pdf"] = PdfCompressor()
    except ImportError as e:
        logger.warning("Motor PDF no disponible: %s", e)

    try:
        from compressors.images.image_compressor import ImageCompressor
        engines["image"] = ImageCompressor()
    except ImportError as e:
        logger.warning("Motor de imágenes no disponible: %s", e)

    try:
        from compressors.office.office_compressor import OfficeCompressor
        engines["office"] = OfficeCompressor()
    except ImportError as e:
        logger.warning("Motor Office no disponible: %s", e)

    try:
        from compressors.text.text_compressor import TextCompressor
        engines["text"] = TextCompressor()
    except ImportError as e:
        logger.warning("Motor de texto no disponible: %s", e)

    return engines


def get_engine(path: Path) -> Optional[CompressionEngine]:
    """
    Retorna el motor de compresión apropiado para el archivo dado.

    Args:
        path: Ruta al archivo a comprimir.

    Returns:
        Motor de compresión o None si el formato no es soportado.
    """
    global _engines
    if _engines is None:
        _engines = _build_engines()

    file_type = detect_file_type(path)
    engine = _engines.get(file_type)

    if engine is None:
        logger.warning("Sin motor para tipo '%s': %s", file_type, path.name)

    return engine
