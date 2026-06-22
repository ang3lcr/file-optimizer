"""
compressors/text/text_compressor.py
Motor de compresión de archivos de texto.

Técnicas según tipo:
- TXT / RTF / ODT: Limpieza de líneas vacías y espacios redundantes.
- JSON: Minificación (eliminar indentación y espacios).
- XML / HTML: Minificación + eliminación de comentarios.
- CSV: Limpieza de espacios alrededor de comas.
"""

from __future__ import annotations
import json
import re
import shutil
import time
from pathlib import Path
from xml.etree import ElementTree as ET

from utils.logger import get_logger
from utils.file_utils import get_output_path
from models.compression_result import CompressionResult
from compressors.base import CompressionEngine, CompressionOptions

logger = get_logger("text")


class TextCompressor(CompressionEngine):
    """Motor de compresión/optimización para archivos de texto."""

    @property
    def name(self) -> str:
        return "Text Compressor (minificación)"

    @property
    def supported_extensions(self) -> list[str]:
        return ["txt", "rtf", "odt", "html", "htm", "xml", "json", "csv", "doc"]

    def compress(self, input_path: Path, options: CompressionOptions) -> CompressionResult:
        start_time = time.monotonic()
        original_size = input_path.stat().st_size
        ext = input_path.suffix.lower().lstrip(".")

        output_path = options.output_path or get_output_path(input_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Comprimiendo texto: %s (tipo=%s)", input_path.name, ext)

        try:
            options.report_progress(0.1)

            if ext == "json":
                success = self._minify_json(input_path, output_path)
            elif ext in ("xml",):
                success = self._minify_xml(input_path, output_path)
            elif ext in ("html", "htm"):
                success = self._minify_html(input_path, output_path)
            elif ext == "csv":
                success = self._clean_csv(input_path, output_path)
            elif ext in ("txt", "rtf", "doc"):
                success = self._clean_text(input_path, output_path)
            elif ext == "odt":
                # ODT es ZIP internamente, similar a Office
                success = self._clean_text_copy(input_path, output_path)
            else:
                shutil.copy2(input_path, output_path)
                success = True

            options.report_progress(1.0)

            final_size = output_path.stat().st_size if output_path.exists() else original_size
            elapsed = time.monotonic() - start_time

            if final_size >= original_size:
                shutil.copy2(input_path, output_path)
                final_size = original_size

            return CompressionResult(
                success=success,
                original_size=original_size,
                final_size=final_size,
                output_path=output_path,
                elapsed_seconds=elapsed,
                method_used=self.name,
            )

        except Exception as exc:
            logger.exception("Error al comprimir texto %s: %s", input_path.name, exc)
            if output_path.exists():
                output_path.unlink(missing_ok=True)
            return CompressionResult(
                success=False,
                original_size=original_size,
                error_message=str(exc),
                method_used=self.name,
                elapsed_seconds=time.monotonic() - start_time,
            )

    def _minify_json(self, input_path: Path, output_path: Path) -> bool:
        """Minifica JSON eliminando indentación y espacios extra."""
        try:
            with open(input_path, encoding="utf-8", errors="replace") as f:
                data = json.load(f)
            minified = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(minified)
            return True
        except json.JSONDecodeError as exc:
            logger.warning("JSON inválido en %s: %s. Limpiando como texto.", input_path.name, exc)
            return self._clean_text(input_path, output_path)

    def _minify_xml(self, input_path: Path, output_path: Path) -> bool:
        """Minifica XML eliminando whitespace innecesario y comentarios."""
        try:
            # Leer como texto y aplicar regex para whitespace
            content = input_path.read_text(encoding="utf-8", errors="replace")
            # Eliminar comentarios XML
            content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
            # Eliminar whitespace entre tags
            content = re.sub(r">\s+<", "><", content)
            # Eliminar espacios al inicio/fin de líneas
            lines = [line.strip() for line in content.splitlines()]
            content = "".join(lines)
            output_path.write_text(content, encoding="utf-8")
            return True
        except Exception as exc:
            logger.warning("Error minificando XML: %s", exc)
            shutil.copy2(input_path, output_path)
            return False

    def _minify_html(self, input_path: Path, output_path: Path) -> bool:
        """Minifica HTML eliminando comentarios y whitespace extra."""
        try:
            content = input_path.read_text(encoding="utf-8", errors="replace")
            # Eliminar comentarios HTML (excepto condicionales IE)
            content = re.sub(r"<!--(?!\[if).*?-->", "", content, flags=re.DOTALL)
            # Colapsar whitespace dentro de líneas
            content = re.sub(r"[ \t]+", " ", content)
            # Eliminar líneas vacías múltiples
            content = re.sub(r"\n\s*\n", "\n", content)
            # Eliminar espacios alrededor de tags
            content = re.sub(r">\s+<", ">\n<", content)
            content = content.strip()
            output_path.write_text(content, encoding="utf-8")
            return True
        except Exception as exc:
            logger.warning("Error minificando HTML: %s", exc)
            shutil.copy2(input_path, output_path)
            return False

    def _clean_csv(self, input_path: Path, output_path: Path) -> bool:
        """Limpia espacios innecesarios en CSV."""
        try:
            content = input_path.read_text(encoding="utf-8", errors="replace")
            lines = []
            for line in content.splitlines():
                if line.strip():  # Omitir líneas vacías
                    # Limpiar espacios alrededor de comas
                    cleaned = ",".join(cell.strip() for cell in line.split(","))
                    lines.append(cleaned)
            output_path.write_text("\n".join(lines), encoding="utf-8")
            return True
        except Exception as exc:
            logger.warning("Error limpiando CSV: %s", exc)
            shutil.copy2(input_path, output_path)
            return False

    def _clean_text(self, input_path: Path, output_path: Path) -> bool:
        """Limpia espacios redundantes y líneas vacías múltiples en texto plano."""
        try:
            content = input_path.read_text(encoding="utf-8", errors="replace")
            # Eliminar líneas vacías consecutivas (máximo 1)
            content = re.sub(r"\n{3,}", "\n\n", content)
            # Eliminar espacios al final de cada línea
            lines = [line.rstrip() for line in content.splitlines()]
            content = "\n".join(lines).strip()
            output_path.write_text(content, encoding="utf-8")
            return True
        except Exception as exc:
            logger.warning("Error limpiando texto: %s", exc)
            shutil.copy2(input_path, output_path)
            return False

    def _clean_text_copy(self, input_path: Path, output_path: Path) -> bool:
        """Copia el archivo sin modificación (para formatos binarios como ODT)."""
        shutil.copy2(input_path, output_path)
        return True
