"""
main.py
Punto de entrada de FileOptimizer Pro.

Inicializa el sistema de logs, carga la configuración,
registra el manejador de excepciones no capturadas y lanza la GUI.
"""

from __future__ import annotations
import sys
import traceback
import tkinter as tk
from pathlib import Path

# Agregar el directorio raíz al path para imports relativos
_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))


def _setup_exception_handler() -> None:
    """Registra un manejador global de excepciones no capturadas."""
    import logging

    def handle_exception(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logger = logging.getLogger("fileoptimizer")
        logger.critical(
            "Excepción no capturada",
            exc_info=(exc_type, exc_value, exc_tb),
        )
        # Mostrar diálogo de error al usuario
        try:
            from tkinter import messagebox
            messagebox.showerror(
                "Error Crítico",
                f"Se produjo un error inesperado:\n\n{exc_value}\n\n"
                "Revisa el archivo de logs para más detalles.",
            )
        except Exception:
            pass

    sys.excepthook = handle_exception


def main() -> None:
    """Función principal de la aplicación."""
    # 1. Inicializar logs
    from utils.logger import setup_logger
    logger = setup_logger()
    logger.info("=" * 60)
    logger.info("FileOptimizer Pro v1.0.0 - Iniciando")
    logger.info("Python %s | Platform: %s", sys.version, sys.platform)
    logger.info("=" * 60)

    # 2. Manejador de excepciones
    _setup_exception_handler()

    # 3. Cargar configuración
    from utils.config_manager import ConfigManager
    config = ConfigManager()

    # 4. Verificar dependencias críticas
    _check_dependencies(logger)

    # 5. Lanzar GUI
    try:
        # Usar TkinterDnD como base si está disponible (para drag & drop)
        try:
            import tkinterdnd2 as dnd
            root_class = dnd.TkinterDnD.Tk  # type: ignore[attr-defined]
            logger.info("tkinterdnd2 disponible. Drag & Drop activado.")
        except ImportError:
            logger.warning("tkinterdnd2 no disponible. Drag & Drop desactivado.")
            root_class = None

        from ui.app import FileOptimizerApp
        import customtkinter as ctk

        if root_class is not None:
            # Para DnD necesitamos wrapping especial
            # CTk hereda de Tk, así que creamos la app normalmente
            # y tkinterdnd2 se maneja en drop_zone.py con fallback
            pass

        app = FileOptimizerApp(config)
        logger.info("GUI inicializada correctamente.")
        app.mainloop()

    except Exception as exc:
        logger.critical("Error fatal al iniciar la GUI: %s", exc, exc_info=True)
        try:
            from tkinter import messagebox
            messagebox.showerror(
                "Error de inicio",
                f"No se pudo iniciar FileOptimizer Pro:\n\n{exc}",
            )
        except Exception:
            print(f"ERROR FATAL: {exc}", file=sys.stderr)
        sys.exit(1)


def _check_dependencies(logger) -> None:
    """Verifica que las dependencias principales estén instaladas."""
    deps = {
        "customtkinter": "Interfaz gráfica",
        "PIL": "Compresión de imágenes (Pillow)",
        "pikepdf": "Compresión PDF",
        "fitz": "Compresión PDF avanzada (PyMuPDF)",
        "docx": "Documentos Word",
        "openpyxl": "Hojas de cálculo",
        "pptx": "Presentaciones PowerPoint",
        "reportlab": "Generación de reportes PDF",
    }

    for module, description in deps.items():
        try:
            __import__(module)
            logger.debug("✓ %s: %s", module, description)
        except ImportError:
            logger.warning("✗ %s no disponible: %s", module, description)


if __name__ == "__main__":
    main()
