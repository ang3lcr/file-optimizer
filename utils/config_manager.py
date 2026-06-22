"""
utils/config_manager.py
Gestión de configuración persistente en JSON.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from .logger import get_logger

logger = get_logger("config")

_CONFIG_PATH = Path(__file__).parent.parent / "config.json"

# Configuración por defecto
_DEFAULTS: dict[str, Any] = {
    "output_mode": "same_folder",       # 'same_folder' | 'custom_folder'
    "output_folder": "",                 # Solo se usa si output_mode == 'custom_folder'
    "quality_level": "balanced",         # QualityLevel.value
    "compression_mode": "auto",          # CompressionMode.value
    "theme": "light",                    # 'dark' | 'light'
    "remove_metadata": True,
    "remove_revisions": False,
    "convert_images_to_webp": False,
    "custom_image_quality": 75,          # 1-100
    "log_level": "DEBUG",
    "window_geometry": "",               # ej: "1280x800+100+50"
    "window_maximized": False,
    "last_output_folder": "",
}


class ConfigManager:
    """
    Gestiona la configuración persistente de la aplicación.

    La configuración se guarda en config.json en el directorio raíz.
    Si el archivo no existe, se crea con valores por defecto.

    Uso::

        config = ConfigManager()
        theme = config.get("theme")
        config.set("theme", "light")
        config.save()
    """

    def __init__(self) -> None:
        self._data: dict[str, Any] = dict(_DEFAULTS)
        self._path = _CONFIG_PATH
        self._load()

    def _load(self) -> None:
        """Carga config desde disco, completando claves faltantes con defaults."""
        if self._path.exists():
            try:
                with open(self._path, encoding="utf-8") as f:
                    stored = json.load(f)
                # Merge: los defaults llenan claves nuevas sin pisar las guardadas
                self._data = {**_DEFAULTS, **stored}
                logger.debug("Configuración cargada desde %s", self._path)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("No se pudo leer config.json: %s. Usando defaults.", exc)
        else:
            logger.info("config.json no encontrado. Creando con valores por defecto.")
            self.save()

    def save(self) -> None:
        """Escribe la configuración actual a disco."""
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            logger.debug("Configuración guardada en %s", self._path)
        except OSError as exc:
            logger.error("Error al guardar configuración: %s", exc)

    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Establece un valor y guarda automáticamente."""
        self._data[key] = value
        self.save()

    def get_all(self) -> dict[str, Any]:
        """Retorna una copia de toda la configuración."""
        return dict(self._data)

    def reset_to_defaults(self) -> None:
        """Restaura todos los valores a los defaults."""
        self._data = dict(_DEFAULTS)
        self.save()
        logger.info("Configuración restaurada a valores por defecto.")
