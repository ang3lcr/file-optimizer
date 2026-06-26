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
    bg_primary="#093C5D",
    bg_secondary="#052033",
    bg_card="#0C456A",
    bg_hover="#145580",
    bg_selected="#1C6494",

    text_primary="#EFFFFD",
    text_secondary="#B8FFF9",
    text_muted="#A9CADF",
    text_on_accent="#052033",

    accent_primary="#5DF8D8",
    accent_hover="#6FD1D7",
    accent_light="#3B7597",

    success="#26E6A2",
    success_bg="#082A1D",
    warning="#F1C40F",
    warning_bg="#2D2503",
    error="#E74C3C",
    error_bg="#2D0F0C",
    processing="#5DF8D8",

    border="#3B7597",
    border_focus="#5DF8D8",

    drop_border="#5DF8D8",
    drop_bg="#0A324C",
)

LIGHT = ColorPalette(
    bg_primary="#EFFFFD",
    bg_secondary="#B8FFF9",
    bg_card="#FFFFFF",
    bg_hover="#DFFDFF",
    bg_selected="#85F4FF",

    text_primary="#052033",
    text_secondary="#1D557A",
    text_muted="#3B7597",
    text_on_accent="#052033",

    accent_primary="#42C2FF",
    accent_hover="#00B2FF",
    accent_light="#85F4FF",

    success="#10B981",
    success_bg="#D1FAE5",
    warning="#F59E0B",
    warning_bg="#FEF3C7",
    error="#EF4444",
    error_bg="#FEE2E2",
    processing="#42C2FF",

    border="#85F4FF",
    border_focus="#42C2FF",

    drop_border="#42C2FF",
    drop_bg="#EFFFFD",
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
