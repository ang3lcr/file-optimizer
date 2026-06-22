"""
utils/file_utils.py
Utilidades de detección de tipo de archivo y manejo de rutas.
"""

from __future__ import annotations
import mimetypes
from pathlib import Path
from typing import Literal

# ---------------------------------------------------------------------------
# Mapeo de extensiones soportadas por categoría
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS: dict[str, list[str]] = {
    "pdf": ["pdf"],
    "image": ["jpg", "jpeg", "png", "webp", "bmp", "tiff", "tif", "gif"],
    "office": ["docx", "xlsx", "pptx", "xls", "ods"],
    "text": ["txt", "doc", "rtf", "odt", "html", "htm", "xml", "json", "csv"],
}

# Set plano para búsqueda rápida
_ALL_SUPPORTED: set[str] = {
    ext
    for exts in SUPPORTED_EXTENSIONS.values()
    for ext in exts
}

FileCategory = Literal["pdf", "image", "office", "text", "unknown"]


def detect_file_type(path: Path) -> FileCategory:
    """
    Detecta la categoría de compresión de un archivo por su extensión.

    Args:
        path: Ruta al archivo.

    Returns:
        Categoría: 'pdf', 'image', 'office', 'text', o 'unknown'.
    """
    ext = path.suffix.lower().lstrip(".")
    for category, extensions in SUPPORTED_EXTENSIONS.items():
        if ext in extensions:
            return category  # type: ignore[return-value]
    return "unknown"


def is_supported(path: Path) -> bool:
    """Retorna True si el archivo tiene una extensión soportada."""
    ext = path.suffix.lower().lstrip(".")
    return ext in _ALL_SUPPORTED


def format_size(size_bytes: int) -> str:
    """
    Formatea un tamaño en bytes a una cadena legible.

    Examples:
        >>> format_size(1536)
        '1.5 KB'
        >>> format_size(2_097_152)
        '2.0 MB'
    """
    if size_bytes <= 0:
        return "0 B"
    value = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024.0:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} PB"


def get_output_path(input_path: Path, output_dir: Path | None = None) -> Path:
    """
    Genera la ruta de salida para el archivo comprimido.

    Si no se especifica output_dir, usa la misma carpeta del archivo original.
    El nombre tendrá el sufijo '_optimizado' antes de la extensión.

    Args:
        input_path: Ruta del archivo original.
        output_dir: Carpeta de destino opcional.

    Returns:
        Ruta de salida única (nunca sobreescribe el original).

    Examples:
        >>> get_output_path(Path("C:/docs/Informe.pdf"))
        PosixPath('C:/docs/Informe_optimizado.pdf')
    """
    stem = input_path.stem
    suffix = input_path.suffix
    folder = output_dir if output_dir else input_path.parent

    candidate = folder / f"{stem}_optimizado{suffix}"

    # Evitar colisiones si ya existe
    counter = 1
    while candidate.exists():
        candidate = folder / f"{stem}_optimizado_{counter}{suffix}"
        counter += 1

    return candidate


def collect_files_from_paths(paths: list[Path], recursive: bool = True) -> list[Path]:
    """
    Expande carpetas a lista de archivos soportados.

    Args:
        paths: Lista de rutas (archivos o carpetas).
        recursive: Si True, escanea subcarpetas.

    Returns:
        Lista de archivos soportados encontrados.
    """
    result: list[Path] = []
    for path in paths:
        if path.is_file():
            if is_supported(path):
                result.append(path)
        elif path.is_dir():
            pattern = "**/*" if recursive else "*"
            for child in path.glob(pattern):
                if child.is_file() and is_supported(child):
                    result.append(child)
    return result


def get_mime_type(path: Path) -> str:
    """Retorna el MIME type del archivo usando la librería estándar."""
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "application/octet-stream"
