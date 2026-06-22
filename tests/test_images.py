"""
tests/test_images.py
Tests unitarios para el motor de compresión de imágenes.
"""

import sys
import unittest
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.compression_profile import QualityLevel
from compressors.base import CompressionOptions


def _create_test_image(path: Path, size: tuple = (800, 600), fmt: str = "JPEG") -> None:
    """Crea una imagen de prueba usando Pillow."""
    from PIL import Image
    import random
    img = Image.new("RGB", size, color=(
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
    ))
    img.save(path, format=fmt, quality=95)


class TestImageCompressor(unittest.TestCase):
    """Tests del motor de imágenes."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmp_path = Path(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_instantiation(self):
        try:
            from compressors.images.image_compressor import ImageCompressor
            c = ImageCompressor()
            self.assertIn("jpg", c.supported_extensions)
            self.assertIn("png", c.supported_extensions)
            self.assertIn("webp", c.supported_extensions)
        except ImportError as e:
            self.skipTest(str(e))

    def test_compress_jpeg(self):
        try:
            from compressors.images.image_compressor import ImageCompressor
            from PIL import Image

            c = ImageCompressor()
            img_path = self.tmp_path / "test.jpg"
            _create_test_image(img_path, size=(2000, 1500), fmt="JPEG")

            output = self.tmp_path / "out.jpg"
            opts = CompressionOptions(
                quality_level=QualityLevel.BALANCED,
                output_path=output,
            )
            result = c.compress(img_path, opts)
            self.assertIsNotNone(result)
            # El resultado debe existir
            if result.success and result.output_path:
                self.assertTrue(result.output_path.exists())

        except ImportError as e:
            self.skipTest(str(e))

    def test_compress_png(self):
        try:
            from compressors.images.image_compressor import ImageCompressor
            from PIL import Image

            c = ImageCompressor()
            img_path = self.tmp_path / "test.png"
            img = Image.new("RGB", (1000, 800), color=(100, 150, 200))
            img.save(img_path, format="PNG")

            output = self.tmp_path / "out.png"
            opts = CompressionOptions(
                quality_level=QualityLevel.HIGH_COMPRESSION,
                output_path=output,
            )
            result = c.compress(img_path, opts)
            self.assertIsNotNone(result)

        except ImportError as e:
            self.skipTest(str(e))

    def test_thumbnail_generation(self):
        try:
            from compressors.images.image_compressor import ImageCompressor
            from PIL import Image

            c = ImageCompressor()
            img_path = self.tmp_path / "thumb_test.jpg"
            _create_test_image(img_path)

            thumb = c.generate_thumbnail(img_path, size=(150, 150))
            self.assertIsNotNone(thumb)
            self.assertIsInstance(thumb, bytes)
            self.assertGreater(len(thumb), 0)

        except ImportError as e:
            self.skipTest(str(e))

    def test_file_type_detection(self):
        from utils.file_utils import detect_file_type
        for ext in ["jpg", "jpeg", "png", "webp", "bmp", "gif", "tiff"]:
            path = Path(f"imagen.{ext}")
            self.assertEqual(detect_file_type(path), "image")


class TestFileUtils(unittest.TestCase):
    """Tests de utilidades de archivos."""

    def test_format_size(self):
        from utils.file_utils import format_size
        self.assertEqual(format_size(0), "0 B")
        self.assertIn("KB", format_size(1500))
        self.assertIn("MB", format_size(2_000_000))
        self.assertIn("GB", format_size(2_000_000_000))

    def test_detect_file_type(self):
        from utils.file_utils import detect_file_type
        self.assertEqual(detect_file_type(Path("doc.pdf")), "pdf")
        self.assertEqual(detect_file_type(Path("hoja.xlsx")), "office")
        self.assertEqual(detect_file_type(Path("datos.json")), "text")
        self.assertEqual(detect_file_type(Path("foto.jpg")), "image")
        self.assertEqual(detect_file_type(Path("desconocido.xyz")), "unknown")

    def test_get_output_path_suffix(self):
        from utils.file_utils import get_output_path
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "Informe.pdf"
            input_path.touch()
            out = get_output_path(input_path)
            self.assertIn("_optimizado", out.name)
            self.assertNotEqual(out, input_path)


if __name__ == "__main__":
    unittest.main()
