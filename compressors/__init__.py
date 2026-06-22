"""
compressors/__init__.py
"""
from .base import CompressionEngine, CompressionOptions
from .dispatcher import get_engine

__all__ = ["CompressionEngine", "CompressionOptions", "get_engine"]
