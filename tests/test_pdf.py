"""
tests/test_pdf.py
Tests unitarios para el motor de compresión PDF.
"""

import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Ajustar path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.compression_profile import QualityLevel
from compressors.base import CompressionOptions


class TestPdfCompressor(unittest.TestCase):
    """Tests del motor PDF."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmp_path = Path(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_minimal_pdf(self) -> Path:
        """Crea un PDF mínimo válido para pruebas."""
        pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
190
%%EOF"""
        path = self.tmp_path / "test.pdf"
        path.write_bytes(pdf_content)
        return path

    def test_compressor_instantiation(self):
        """El compresor PDF debe instanciarse sin errores."""
        try:
            from compressors.pdf.pdf_compressor import PdfCompressor
            compressor = PdfCompressor()
            self.assertIn("PDF Compressor", compressor.name)
            self.assertIn("pdf", compressor.supported_extensions)
        except ImportError as e:
            self.skipTest(f"Dependencias PDF no instaladas: {e}")

    def test_can_handle_pdf(self):
        """can_handle() debe retornar True para .pdf y False para otros."""
        try:
            from compressors.pdf.pdf_compressor import PdfCompressor
            c = PdfCompressor()
            self.assertTrue(c.can_handle(Path("documento.pdf")))
            self.assertFalse(c.can_handle(Path("imagen.jpg")))
            self.assertFalse(c.can_handle(Path("datos.xlsx")))
        except ImportError as e:
            self.skipTest(f"Dependencias PDF no instaladas: {e}")

    def test_compress_minimal_pdf(self):
        """Comprimir un PDF mínimo debe retornar un resultado."""
        try:
            from compressors.pdf.pdf_compressor import PdfCompressor
            compressor = PdfCompressor()
            pdf_path = self._make_minimal_pdf()
            output = self.tmp_path / "output.pdf"

            options = CompressionOptions(
                quality_level=QualityLevel.BALANCED,
                output_path=output,
            )
            result = compressor.compress(pdf_path, options)

            # No debe lanzar excepciones
            self.assertIsNotNone(result)
            self.assertIsInstance(result.original_size, int)
            self.assertGreater(result.original_size, 0)

        except ImportError as e:
            self.skipTest(f"Dependencias PDF no instaladas: {e}")

    def test_compression_result_properties(self):
        """Las propiedades calculadas de CompressionResult deben funcionar."""
        from models.compression_result import CompressionResult
        result = CompressionResult(
            success=True,
            original_size=10_000_000,
            final_size=4_200_000,
        )
        self.assertAlmostEqual(result.reduction_percent, 58.0, places=0)
        self.assertEqual(result.bytes_saved, 5_800_000)
        self.assertFalse(result.is_larger)


class TestCompressionProfile(unittest.TestCase):
    """Tests del modelo QualityLevel."""

    def test_all_levels_have_labels(self):
        for level in QualityLevel:
            self.assertIsInstance(level.label, str)
            self.assertTrue(len(level.label) > 0)

    def test_image_quality_range(self):
        for level in QualityLevel:
            q = level.image_quality
            self.assertGreaterEqual(q, 1)
            self.assertLessEqual(q, 100)

    def test_pdf_dpi_range(self):
        for level in QualityLevel:
            dpi = level.pdf_dpi
            self.assertGreaterEqual(dpi, 72)
            self.assertLessEqual(dpi, 300)


if __name__ == "__main__":
    unittest.main()
