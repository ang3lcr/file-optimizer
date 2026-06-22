"""
ui/theme.py
Sistema de diseño de FileOptimizer Pro.

Paleta corporativa profesional con soporte oscuro/claro.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class ColorPalette:
    """Paleta de colores para un tema."""
    # Fondos
    bg_primary: str      # Fondo principal de la ventana
    bg_secondary: str    # Fondo de paneles/sidebars
    bg_card: str         # Fondo de tarjetas/componentes
    bg_hover: str        # Hover sobre elementos interactivos
    bg_selected: str     # Elemento seleccionado

    # Texto
    text_primary: str    # Texto principal
    text_secondary: str  # Texto secundario / subtítulos
    text_muted: str      # Texto apagado / placeholders
    text_on_accent: str  # Texto sobre fondo de acento

    # Acentos
    accent_primary: str  # Azul corporativo principal
    accent_hover: str    # Hover del acento
    accent_light: str    # Versión tenue del acento

    # Estados
    success: str         # Verde éxito
    success_bg: str      # Fondo éxito tenue
    warning: str         # Amarillo advertencia
    warning_bg: str      # Fondo advertencia tenue
    error: str           # Rojo error
    error_bg: str        # Fondo error tenue
    processing: str      # Azul procesando

    # Bordes
    border: str          # Borde estándar
    border_focus: str    # Borde con foco

    # Drop zone
    drop_border: str
    drop_bg: str


DARK = ColorPalette(
    bg_primary="#0F1117",
    bg_secondary="#161B22",
    bg_card="#1C2128",
    bg_hover="#21262D",
    bg_selected="#3A2B4C",

    text_primary="#E6EDF3",
    text_secondary="#8B949E",
    text_muted="#484F58",
    text_on_accent="#FFFFFF",

    accent_primary="#b741c4",
    accent_hover="#9d2ea8",
    accent_light="#3a2b4c",

    success="#3FB950",
    success_bg="#0D2B14",
    warning="#D29922",
    warning_bg="#2B1D00",
    error="#F85149",
    error_bg="#2B0E0E",
    processing="#b741c4",

    border="#30363D",
    border_focus="#b741c4",

    drop_border="#b741c4",
    drop_bg="#161B22",
)

LIGHT = ColorPalette(
    bg_primary="#F9FAFB",
    bg_secondary="#FFFFFF",
    bg_card="#FFFFFF",
    bg_hover="#F3F4F6",
    bg_selected="#F3E8FF",

    text_primary="#111827",
    text_secondary="#4B5563",
    text_muted="#9CA3AF",
    text_on_accent="#FFFFFF",

    accent_primary="#b741c4",
    accent_hover="#9d2ea8",
    accent_light="#ebd5fc",

    success="#10B981",
    success_bg="#D1FAE5",
    warning="#F59E0B",
    warning_bg="#FEF3C7",
    error="#EF4444",
    error_bg="#FEE2E2",
    processing="#b741c4",

    border="#E5E7EB",
    border_focus="#b741c4",

    drop_border="#c084fc",
    drop_bg="#FAF5FF",
)


@dataclass(frozen=True)
class Typography:
    """Configuración tipográfica."""
    family: str
    size_xs: int = 9
    size_sm: int = 11
    size_base: int = 13
    size_md: int = 15
    size_lg: int = 18
    size_xl: int = 22
    size_2xl: int = 28

    def as_tuple(self, size: int, bold: bool = False, italic: bool = False) -> tuple:
        style = []
        if bold:
            style.append("bold")
        if italic:
            style.append("italic")
        return (self.family, size, " ".join(style)) if style else (self.family, size)


# Fuente preferida en Windows
FONT = Typography(family="Segoe UI")


def get_palette(theme: str) -> ColorPalette:
    """Retorna la paleta según el tema ('dark' o 'light')."""
    return DARK if theme == "dark" else LIGHT
