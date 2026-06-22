"""
compressors/pdf/pdf_compressor.py
Motor de compresión de archivos PDF.

Estrategia (corregida):
1. pikepdf: Compresión de imágenes con reemplazo correcto del objeto imagen
   (actualiza /Filter, /Width, /Height, /ColorSpace correctamente).
2. pikepdf: Optimización estructural del PDF (streams, objetos, metadatos).
3. PyMuPDF: Optimización adicional de streams (deflate/garbage) como etapa final.

El error anterior usaba fitz.update_stream() que reemplazaba el stream sin
actualizar el diccionario del objeto imagen, corrompiendo las imágenes.
"""

from __future__ import annotations
import io
import shutil
import tempfile
import time
from pathlib import Path

from utils.logger import get_logger
from utils.file_utils import get_output_path
from models.compression_result import CompressionResult
from compressors.base import CompressionEngine, CompressionOptions

logger = get_logger("pdf")


class PdfCompressor(CompressionEngine):
    """Motor de compresión PDF usando pikepdf + PyMuPDF."""

    @property
    def name(self) -> str:
        return "PDF Compressor (pikepdf + PyMuPDF)"

    @property
    def supported_extensions(self) -> list[str]:
        return ["pdf"]

    def compress(self, input_path: Path, options: CompressionOptions) -> CompressionResult:
        """
        Comprime un PDF en dos etapas:
        1. pikepdf: Re-compresión de imágenes con DCTDecode correcto + metadatos.
        2. PyMuPDF: Optimización adicional de streams (solo structural, sin tocar imágenes).
        """
        start_time = time.monotonic()
        original_size = input_path.stat().st_size

        output_path = options.output_path or get_output_path(input_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Comprimiendo PDF: %s (%.1f MB, calidad=%s)",
            input_path.name,
            original_size / (1024 * 1024),
            options.quality_level.label,
        )

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir) / "stage1.pdf"

                if options.cancelled:
                    return _cancelled_result(original_size)

                options.report_progress(0.05)

                # Etapa 1: Compresión de imágenes + metadatos con pikepdf
                stage1_ok = self._compress_images_pikepdf(input_path, tmp_path, options)
                source_for_stage2 = tmp_path if stage1_ok and tmp_path.exists() else input_path

                if options.cancelled:
                    return _cancelled_result(original_size)

                options.report_progress(0.8)

                # Etapa 2: Optimización estructural con PyMuPDF (SIN tocar imágenes)
                stage2_ok = self._optimize_streams_fitz(source_for_stage2, output_path, options)
                if not stage2_ok:
                    # Fallback: usar resultado de etapa 1 directamente
                    if source_for_stage2.exists():
                        shutil.copy2(source_for_stage2, output_path)
                    else:
                        shutil.copy2(input_path, output_path)

                options.report_progress(1.0)

            final_size = output_path.stat().st_size if output_path.exists() else original_size
            elapsed = time.monotonic() - start_time

            # Si el resultado es mayor, conservar el original
            if final_size >= original_size:
                logger.warning(
                    "PDF ya optimizado (resultado >= original). Copiando original."
                )
                shutil.copy2(input_path, output_path)
                final_size = output_path.stat().st_size

            logger.info(
                "PDF comprimido: %s → %s (%.1f%%)",
                _mb(original_size),
                _mb(final_size),
                (1 - final_size / original_size) * 100 if original_size > 0 else 0,
            )

            return CompressionResult(
                success=True,
                original_size=original_size,
                final_size=final_size,
                output_path=output_path,
                elapsed_seconds=elapsed,
                method_used=self.name,
            )

        except Exception as exc:
            logger.exception("Error al comprimir PDF %s: %s", input_path.name, exc)
            if output_path.exists():
                output_path.unlink(missing_ok=True)
            return CompressionResult(
                success=False,
                original_size=original_size,
                error_message=str(exc),
                method_used=self.name,
                elapsed_seconds=time.monotonic() - start_time,
            )

    # ------------------------------------------------------------------
    # Etapa 1: Compresión de imágenes con pikepdf (CORRECTO)
    # ------------------------------------------------------------------

    def _compress_images_pikepdf(
        self, input_path: Path, output_path: Path, options: CompressionOptions
    ) -> bool:
        """
        Comprime imágenes embebidas en el PDF usando pikepdf.

        A diferencia de fitz.update_stream(), este método actualiza correctamente
        el diccionario del objeto imagen (/Filter, /Width, /Height, /ColorSpace,
        /BitsPerComponent), garantizando que las imágenes se conserven.

        Returns:
            True si fue exitoso.
        """
        try:
            import pikepdf
            from PIL import Image

            quality = options.get_image_quality()
            dpi_target = options.quality_level.pdf_dpi

            with pikepdf.open(str(input_path)) as pdf:
                # Eliminar metadatos si se solicita
                if options.remove_metadata:
                    _strip_metadata(pdf)

                # Recopilar todos los xrefs de imágenes (evitar duplicados)
                visited: set[int] = set()
                all_images = _collect_image_xobjects(pdf)
                total_images = len(all_images)

                for i, (xref_id, img_obj) in enumerate(all_images):
                    if options.cancelled:
                        return False

                    if xref_id in visited:
                        continue
                    visited.add(xref_id)

                    try:
                        _recompress_image_object(pdf, img_obj, quality, dpi_target, logger)
                    except Exception as img_exc:
                        logger.debug(
                            "Imagen xref=%d omitida: %s", xref_id, img_exc
                        )

                    # Progreso parcial de esta etapa (0.05 → 0.75)
                    options.report_progress(
                        0.05 + 0.70 * (i + 1) / max(total_images, 1)
                    )

                pdf.save(
                    str(output_path),
                    compress_streams=True,
                    object_stream_mode=pikepdf.ObjectStreamMode.generate,
                    recompress_flate=True,
                )

            return True

        except ImportError:
            logger.warning("pikepdf no disponible.")
            return False
        except Exception as exc:
            logger.error("Error en compresión pikepdf: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Etapa 2: Optimización estructural con PyMuPDF (SIN modificar imágenes)
    # ------------------------------------------------------------------

    def _optimize_streams_fitz(
        self, input_path: Path, output_path: Path, options: CompressionOptions
    ) -> bool:
        """
        Usa PyMuPDF únicamente para compresión de streams y limpieza de
        objetos huérfanos. NO modifica datos de imágenes.

        Returns:
            True si fue exitoso.
        """
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(str(input_path))
            doc.save(
                str(output_path),
                garbage=4,      # Eliminar objetos no referenciados
                deflate=True,   # Comprimir streams de contenido
                clean=True,     # Limpiar operadores de contenido
                # deflate_images y deflate_fonts son los defaults
            )
            doc.close()
            return True

        except ImportError:
            logger.warning("PyMuPDF no disponible. Saltando etapa 2.")
            return False
        except Exception as exc:
            logger.warning("Error en optimización PyMuPDF: %s. Usando resultado de etapa 1.", exc)
            return False


# ------------------------------------------------------------------
# Funciones auxiliares
# ------------------------------------------------------------------

def _collect_image_xobjects(pdf: "pikepdf.Pdf") -> list[tuple[int, object]]:
    """
    Recorre todas las páginas y recopila los XObjects de tipo /Image.
    Retorna lista de (objgen_id, pikepdf_object).
    """
    import pikepdf

    results: list[tuple[int, object]] = []
    seen_objgens: set = set()

    for page in pdf.pages:
        try:
            resources = page.get("/Resources")
            if resources is None:
                continue
            xobjects = resources.get("/XObject")
            if xobjects is None:
                continue

            for key in xobjects.keys():
                xobj = xobjects[key]
                # Verificar que es una referencia indirecta (objeto compartido)
                try:
                    objgen = xobj.objgen
                except Exception:
                    objgen = id(xobj)

                if objgen in seen_objgens:
                    continue

                try:
                    subtype = xobj.get("/Subtype")
                    if subtype == pikepdf.Name("/Image"):
                        seen_objgens.add(objgen)
                        results.append((id(objgen), xobj))
                except Exception:
                    pass
        except Exception:
            pass

    return results


def _recompress_image_object(
    pdf: "pikepdf.Pdf",
    img_obj: object,
    quality: int,
    dpi_target: int,
    log: object,
) -> None:
    """
    Re-comprime un objeto imagen de pikepdf con JPEG a la calidad indicada.

    Actualiza correctamente:
    - El stream de datos (bytes JPEG)
    - /Filter → /DCTDecode
    - /Width, /Height (si se redimensionó)
    - /ColorSpace, /BitsPerComponent
    - Elimina /DecodeParms si existía
    """
    import pikepdf
    from PIL import Image

    # Leer el stream de la imagen actual
    try:
        img_pil = pikepdf.PdfImage(img_obj).as_pil_image()
    except Exception:
        # Si PdfImage falla (e.g. imagen con máscara compleja), omitir
        return

    orig_w, orig_h = img_pil.size

    # Imágenes con canal alfa → no convertir a JPEG (pérdida de transparencia)
    # Se optimizan los streams pero no se recodifican
    if img_pil.mode in ("RGBA", "LA"):
        return

    # Convertir modo para JPEG
    if img_pil.mode == "CMYK":
        # CMYK se guarda como JPEG CMYK (soportado por los lectores PDF)
        pass
    elif img_pil.mode not in ("RGB", "L"):
        img_pil = img_pil.convert("RGB")

    # Reducir resolución si DPI objetivo es menor
    # Estimamos que la imagen fue escaneada a ~150 DPI
    if dpi_target < 150 and orig_w > 100 and orig_h > 100:
        scale = dpi_target / 150.0
        new_w = max(int(orig_w * scale), 32)
        new_h = max(int(orig_h * scale), 32)
        if new_w < orig_w:
            img_pil = img_pil.resize((new_w, new_h), Image.LANCZOS)

    # Comprimir como JPEG en memoria
    buf = io.BytesIO()
    img_pil.save(buf, format="JPEG", quality=quality, optimize=True)
    jpeg_bytes = buf.getvalue()

    # Solo reemplazar si el resultado es más pequeño
    try:
        raw_len = len(img_obj.read_raw_bytes())
    except Exception:
        raw_len = len(jpeg_bytes) + 1  # Forzar reemplazo si no se puede medir

    if len(jpeg_bytes) >= raw_len:
        return  # La imagen ya está bien comprimida

    # ---------------------------------------------------------------
    # Reemplazar stream con la API correcta de pikepdf:
    # write() actualiza el stream Y el diccionario (/Filter, etc.)
    # de forma atómica, garantizando que el PDF sea válido.
    # ---------------------------------------------------------------
    img_obj.write(  # type: ignore[attr-defined]
        jpeg_bytes,
        filter=pikepdf.Name("/DCTDecode"),
    )

    # Actualizar dimensiones y espacio de color en el diccionario del objeto
    img_obj["/Width"] = img_pil.width   # type: ignore[index]
    img_obj["/Height"] = img_pil.height  # type: ignore[index]
    img_obj["/BitsPerComponent"] = 8     # type: ignore[index]

    if img_pil.mode == "L":
        img_obj["/ColorSpace"] = pikepdf.Name("/DeviceGray")   # type: ignore[index]
    elif img_pil.mode == "CMYK":
        img_obj["/ColorSpace"] = pikepdf.Name("/DeviceCMYK")   # type: ignore[index]
    else:
        img_obj["/ColorSpace"] = pikepdf.Name("/DeviceRGB")    # type: ignore[index]


def _strip_metadata(pdf: "pikepdf.Pdf") -> None:
    """Elimina metadatos XMP y DocInfo del PDF."""
    try:
        with pdf.open_metadata() as meta:
            for key in list(meta.keys()):
                try:
                    del meta[key]
                except Exception:
                    pass
    except Exception:
        pass

    # Limpiar también el diccionario de información /Info
    try:
        if "/Info" in pdf.trailer:
            info = pdf.trailer["/Info"]
            sensitive_keys = [
                "/Author", "/Creator", "/Producer", "/Subject",
                "/Keywords", "/Manager", "/Company",
            ]
            for k in sensitive_keys:
                if k in info:
                    try:
                        del info[k]
                    except Exception:
                        pass
    except Exception:
        pass


def _cancelled_result(original_size: int) -> CompressionResult:
    return CompressionResult(
        success=False,
        original_size=original_size,
        error_message="Cancelado por el usuario.",
        method_used="PDF Compressor",
    )


def _mb(size: int) -> str:
    return f"{size / (1024 * 1024):.2f} MB"
