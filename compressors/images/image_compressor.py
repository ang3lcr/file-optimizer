"""
compressors/images/image_compressor.py
Motor de compresión de imágenes usando Pillow.

Soporta: JPG, JPEG, PNG, WEBP, BMP, TIFF, GIF
"""

from __future__ import annotations
import io
import shutil
import time
from pathlib import Path
from typing import Optional

from utils.logger import get_logger
from utils.file_utils import get_output_path
from models.compression_result import CompressionResult
from compressors.base import CompressionEngine, CompressionOptions

logger = get_logger("images")


class ImageCompressor(CompressionEngine):
    """Motor de compresión de imágenes con Pillow."""

    @property
    def name(self) -> str:
        return "Image Compressor (Pillow)"

    @property
    def supported_extensions(self) -> list[str]:
        return ["jpg", "jpeg", "png", "webp", "bmp", "tiff", "tif", "gif"]

    def compress(self, input_path: Path, options: CompressionOptions) -> CompressionResult:
        start_time = time.monotonic()
        original_size = input_path.stat().st_size

        # Determinar extensión de salida
        ext = input_path.suffix.lower()
        if options.convert_to_webp and ext not in (".webp",):
            out_suffix = ".webp"
        else:
            out_suffix = ext

        output_path = options.output_path or get_output_path(
            input_path.with_suffix(out_suffix)
        )
        # Si cambió la extensión, ajustar output_path
        if out_suffix != ext:
            output_path = output_path.with_suffix(out_suffix)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Comprimiendo imagen: %s → %s (calidad=%d)",
            input_path.name,
            output_path.name,
            options.get_image_quality(),
        )

        try:
            from PIL import Image

            options.report_progress(0.1)
            img = Image.open(input_path)
            options.report_progress(0.3)

            if options.cancelled:
                return _cancelled_result(original_size)

            # Guardar con optimización
            final_path = self._save_optimized(img, output_path, options)
            options.report_progress(1.0)

            final_size = final_path.stat().st_size
            elapsed = time.monotonic() - start_time

            # Si salió más grande (por ejemplo GIF o PNG con muy poca info),
            # copiar el original
            if final_size >= original_size:
                logger.warning("Imagen ya optimizada. Copiando original.")
                shutil.copy2(input_path, output_path)
                final_size = original_size

            logger.info(
                "Imagen: %d → %d bytes (%.1f%%)",
                original_size,
                final_size,
                (1 - final_size / original_size) * 100 if original_size > 0 else 0,
            )

            return CompressionResult(
                success=True,
                original_size=original_size,
                final_size=final_size,
                output_path=final_path,
                elapsed_seconds=elapsed,
                method_used=self.name,
            )

        except Exception as exc:
            logger.exception("Error al comprimir imagen %s: %s", input_path.name, exc)
            if output_path.exists():
                output_path.unlink(missing_ok=True)
            return CompressionResult(
                success=False,
                original_size=original_size,
                error_message=str(exc),
                method_used=self.name,
                elapsed_seconds=time.monotonic() - start_time,
            )

    def _save_optimized(
        self,
        img: "Image.Image",
        output_path: Path,
        options: CompressionOptions,
    ) -> Path:
        """Guarda la imagen con la estrategia apropiada según el formato de salida."""
        from PIL import Image

        quality = options.get_image_quality()
        target_ext = output_path.suffix.lower()

        # Eliminar metadatos EXIF si se solicita
        if options.remove_metadata:
            img = _strip_exif(img)

        # Convertir modo según el formato de destino
        if target_ext in (".jpg", ".jpeg"):
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")
            img.save(
                output_path,
                format="JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
            )

        elif target_ext == ".webp":
            if img.mode == "P":
                img = img.convert("RGBA")
            img.save(
                output_path,
                format="WEBP",
                quality=quality,
                method=6,  # Mejor compresión (más lento)
            )

        elif target_ext == ".png":
            # PNG es lossless: optimizar con paleta y compresión máxima
            compress_level = _png_compress_level(quality)
            if img.mode == "RGB" and quality < 85:
                # Cuantizar a 256 colores para mayor compresión
                img = img.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
            img.save(
                output_path,
                format="PNG",
                optimize=True,
                compress_level=compress_level,
            )

        elif target_ext == ".gif":
            img.save(output_path, format="GIF", optimize=True)

        else:
            # BMP, TIFF → convertir a JPEG o guardar tal cual
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")
            jpeg_path = output_path.with_suffix(".jpg")
            img.save(jpeg_path, format="JPEG", quality=quality, optimize=True)
            return jpeg_path

        return output_path

    def generate_thumbnail(
        self, input_path: Path, size: tuple[int, int] = (300, 300)
    ) -> Optional[bytes]:
        """
        Genera un thumbnail para la vista previa antes/después.

        Args:
            input_path: Ruta de la imagen.
            size: Tamaño máximo del thumbnail.

        Returns:
            Bytes de la imagen thumbnail en PNG, o None si falla.
        """
        try:
            from PIL import Image
            import io

            img = Image.open(input_path)
            img.thumbnail(size, Image.LANCZOS)
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        except Exception as exc:
            logger.warning("No se pudo generar thumbnail de %s: %s", input_path.name, exc)
            return None


def _strip_exif(img: "Image.Image") -> "Image.Image":
    """Elimina los metadatos EXIF de la imagen creando una copia limpia."""
    try:
        from PIL import Image

        # Crear imagen nueva sin metadatos EXIF
        clean = Image.new(img.mode, img.size)
        clean.putdata(list(img.getdata()))
        return clean
    except Exception:
        return img


def _png_compress_level(quality: int) -> int:
    """Convierte calidad 1-100 a nivel de compresión PNG 0-9."""
    # Invertido: mayor calidad → menor compresión (más rápido, mayor archivo)
    return max(1, min(9, int((100 - quality) / 10)))


def _cancelled_result(original_size: int) -> CompressionResult:
    return CompressionResult(
        success=False,
        original_size=original_size,
        error_message="Cancelado por el usuario.",
        method_used="Image Compressor",
    )
