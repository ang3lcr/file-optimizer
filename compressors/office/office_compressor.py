"""
compressors/office/office_compressor.py
Motor de compresión de archivos Office (DOCX, XLSX, PPTX, ODS, XLS).

Estrategia:
- Los archivos DOCX/XLSX/PPTX son ZIPs internamente.
  Se exploran, se optimizan imágenes embebidas con Pillow,
  se eliminan metadatos XML y se recomprime el ZIP.
- Para XLS/ODS se hace una conversión/limpieza básica.
"""

from __future__ import annotations
import io
import shutil
import time
import zipfile
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

from utils.logger import get_logger
from utils.file_utils import get_output_path
from models.compression_result import CompressionResult
from compressors.base import CompressionEngine, CompressionOptions

logger = get_logger("office")

# Extensiones de imagen dentro del ZIP de Office
_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".gif", ".emf", ".wmf"}

# Namespaces XML de metadatos a limpiar
_META_TAGS_TO_CLEAR = {
    "dc:creator", "dc:lastModifiedBy", "cp:revision",
    "cp:lastPrinted", "dcterms:created", "dcterms:modified",
}

# Relaciones XML de revisiones a eliminar
_REVISION_RELS = {
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments",
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes",
}


class OfficeCompressor(CompressionEngine):
    """Motor de compresión para archivos Microsoft Office."""

    @property
    def name(self) -> str:
        return "Office Compressor (ZIP repack + Pillow)"

    @property
    def supported_extensions(self) -> list[str]:
        return ["docx", "xlsx", "pptx", "ods", "xls"]

    def compress(self, input_path: Path, options: CompressionOptions) -> CompressionResult:
        start_time = time.monotonic()
        original_size = input_path.stat().st_size
        ext = input_path.suffix.lower().lstrip(".")

        output_path = options.output_path or get_output_path(input_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Comprimiendo Office: %s (%.1f MB, tipo=%s)",
            input_path.name,
            original_size / (1024 * 1024),
            ext,
        )

        try:
            if ext in ("docx", "xlsx", "pptx"):
                success = self._repack_zip(input_path, output_path, options)
            elif ext == "ods":
                success = self._repack_zip(input_path, output_path, options)
            elif ext == "xls":
                success = self._process_xls(input_path, output_path, options)
            else:
                shutil.copy2(input_path, output_path)
                success = True

            final_size = output_path.stat().st_size if output_path.exists() else original_size
            elapsed = time.monotonic() - start_time

            if final_size >= original_size:
                logger.warning("Archivo Office ya optimizado. Copiando original.")
                shutil.copy2(input_path, output_path)
                final_size = original_size

            logger.info(
                "Office comprimido: %d → %d bytes (%.1f%%)",
                original_size, final_size,
                (1 - final_size / original_size) * 100 if original_size > 0 else 0,
            )

            return CompressionResult(
                success=success,
                original_size=original_size,
                final_size=final_size,
                output_path=output_path,
                elapsed_seconds=elapsed,
                method_used=self.name,
            )

        except Exception as exc:
            logger.exception("Error al comprimir Office %s: %s", input_path.name, exc)
            if output_path.exists():
                output_path.unlink(missing_ok=True)
            return CompressionResult(
                success=False,
                original_size=original_size,
                error_message=str(exc),
                method_used=self.name,
                elapsed_seconds=time.monotonic() - start_time,
            )

    def _repack_zip(
        self,
        input_path: Path,
        output_path: Path,
        options: CompressionOptions,
    ) -> bool:
        """
        Repaqueta el ZIP interno de un archivo Office:
        1. Optimiza imágenes embebidas con Pillow.
        2. Limpia metadatos XML si remove_metadata == True.
        3. Elimina revisiones si remove_revisions == True.
        4. Recomprime con ZIP_DEFLATED nivel 9.
        """
        quality = options.get_image_quality()

        try:
            with zipfile.ZipFile(input_path, "r") as zin:
                entries = zin.namelist()
                total = len(entries)

                with zipfile.ZipFile(
                    output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
                ) as zout:
                    for idx, entry in enumerate(entries):
                        if options.cancelled:
                            return False

                        data = zin.read(entry)
                        entry_lower = entry.lower()
                        entry_path = Path(entry_lower)

                        # Optimizar imágenes
                        if entry_path.suffix in _IMAGE_EXTS and not entry_lower.endswith(".emf"):
                            data = self._compress_embedded_image(data, entry_path.suffix, quality)

                        # Limpiar metadatos XML
                        if options.remove_metadata and _is_meta_xml(entry):
                            data = _clean_metadata_xml(data)

                        # Eliminar revisiones
                        if options.remove_revisions and _is_revision_part(entry):
                            continue  # Omitir esta entrada

                        zout.writestr(entry, data)
                        options.report_progress((idx + 1) / total)

            return True

        except zipfile.BadZipFile as exc:
            logger.error("Archivo ZIP inválido %s: %s", input_path.name, exc)
            shutil.copy2(input_path, output_path)
            return False

    def _compress_embedded_image(
        self, data: bytes, suffix: str, quality: int
    ) -> bytes:
        """Re-comprime una imagen embebida."""
        try:
            from PIL import Image

            img = Image.open(io.BytesIO(data))
            buf = io.BytesIO()

            if suffix in (".jpg", ".jpeg"):
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")
                img.save(buf, format="JPEG", quality=quality, optimize=True)
            elif suffix == ".png":
                img.save(buf, format="PNG", optimize=True, compress_level=7)
            else:
                # Para otros formatos, convertir a JPEG
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")
                img.save(buf, format="JPEG", quality=quality, optimize=True)
                suffix = ".jpg"

            compressed = buf.getvalue()
            # Solo usar si es más pequeño
            return compressed if len(compressed) < len(data) else data

        except Exception as exc:
            logger.debug("No se pudo comprimir imagen embebida: %s", exc)
            return data

    def _process_xls(
        self,
        input_path: Path,
        output_path: Path,
        options: CompressionOptions,
    ) -> bool:
        """Procesa XLS copiándolo (openpyxl no lee XLS directamente)."""
        # XLS es formato binario legado; la mejor estrategia es copiar
        # y recomendar al usuario convertir a XLSX
        shutil.copy2(input_path, output_path)
        logger.info("XLS: copiado sin modificaciones (formato legado).")
        return True


def _is_meta_xml(entry: str) -> bool:
    """Retorna True si la entrada es un archivo de metadatos."""
    return entry.lower() in (
        "docprops/core.xml",
        "docprops/app.xml",
        "docprops/custom.xml",
    )


def _clean_metadata_xml(data: bytes) -> bytes:
    """Limpia campos de metadatos sensibles de un XML de propiedades."""
    try:
        tree = ET.fromstring(data.decode("utf-8", errors="replace"))
        # Limpiar valores de nodos de metadatos
        _SENSITIVE_LOCALS = {
            "creator", "lastModifiedBy", "lastPrinted",
            "company", "manager", "Template",
        }
        for elem in tree.iter():
            local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if local in _SENSITIVE_LOCALS and elem.text:
                elem.text = ""
        return ET.tostring(tree, encoding="unicode", xml_declaration=False).encode("utf-8")
    except Exception:
        return data


def _is_revision_part(entry: str) -> bool:
    """Retorna True si la entrada corresponde a revisiones o comentarios."""
    lower = entry.lower()
    return any(part in lower for part in ("comments", "revisions", "footnotes"))
