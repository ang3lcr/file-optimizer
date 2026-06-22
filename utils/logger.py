"""
utils/logger.py
Sistema de logs rotatorios para FileOptimizer Pro.
"""

from __future__ import annotations
import logging
import logging.handlers
from pathlib import Path
from typing import Optional

# Directorio de logs relativo al ejecutable / script
_LOGS_DIR = Path(__file__).parent.parent / "logs"
_LOG_FILE = _LOGS_DIR / "fileoptimizer.log"

# Máximo 5 MB por archivo, 3 backups
_MAX_BYTES = 5 * 1024 * 1024
_BACKUP_COUNT = 3

_ROOT_LOGGER_NAME = "fileoptimizer"


def setup_logger(level: int = logging.DEBUG) -> logging.Logger:
    """
    Configura el logger raíz de la aplicación.

    Se llama una sola vez al iniciar la aplicación.
    Los logs van a archivo rotatorio + consola (DEBUG en archivo, INFO en consola).

    Args:
        level: Nivel mínimo de log.

    Returns:
        Logger raíz configurado.
    """
    _LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(_ROOT_LOGGER_NAME)
    logger.setLevel(level)

    if logger.handlers:
        # Ya inicializado (evitar duplicados)
        return logger

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler de archivo rotatorio
    file_handler = logging.handlers.RotatingFileHandler(
        filename=_LOG_FILE,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    # Handler de consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("Logger inicializado. Archivo de log: %s", _LOG_FILE)
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger hijo del logger raíz.

    Args:
        name: Nombre del submódulo (ej: 'pdf', 'images').

    Returns:
        Logger configurado.
    """
    return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")
