"""
models/__init__.py
Exporta los modelos de datos principales de FileOptimizer Pro.
"""

from .file_item import FileItem, FileStatus
from .compression_result import CompressionResult
from .compression_profile import QualityLevel, CompressionMode
from .history_entry import HistoryEntry

__all__ = [
    "FileItem",
    "FileStatus",
    "CompressionResult",
    "QualityLevel",
    "CompressionMode",
    "HistoryEntry",
]
