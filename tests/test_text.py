"""
tests/test_text.py  
Tests adicionales para compresores de texto y utilidades.
"""

import sys
import unittest
import tempfile
import shutil
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestProfileAnalyzer(unittest.TestCase):
    """Tests del analizador de perfiles."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmp_path = Path(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_file(self, name: str, size_bytes: int) -> Path:
        path = self.tmp_path / name
        path.write_bytes(b"x" * size_bytes)
        return path

    def test_pdf_large_recommends_high_compression(self):
        from utils.profile_analyzer import analyze
        from models.compression_profile import QualityLevel

        path = self._make_file("big.pdf", 15 * 1024 * 1024)  # 15 MB
        profile = analyze(path)
        self.assertEqual(profile.recommended_quality, QualityLevel.HIGH_COMPRESSION)

    def test_pdf_small_recommends_high_quality(self):
        from utils.profile_analyzer import analyze
        from models.compression_profile import QualityLevel

        path = self._make_file("small.pdf", 1 * 1024 * 1024)  # 1 MB
        profile = analyze(path)
        self.assertEqual(profile.recommended_quality, QualityLevel.HIGH)

    def test_bmp_recommends_high_quality(self):
        from utils.profile_analyzer import analyze
        from models.compression_profile import QualityLevel

        path = self._make_file("image.bmp", 500 * 1024)
        profile = analyze(path)
        self.assertEqual(profile.recommended_quality, QualityLevel.HIGH)
        self.assertGreater(profile.estimated_reduction_percent, 50)

    def test_json_recommends_high_compression(self):
        from utils.profile_analyzer import analyze
        from models.compression_profile import QualityLevel

        path = self._make_file("data.json", 200 * 1024)
        profile = analyze(path)
        self.assertEqual(profile.recommended_quality, QualityLevel.HIGH_COMPRESSION)

    def test_profile_has_description(self):
        from utils.profile_analyzer import analyze

        path = self._make_file("doc.docx", 2 * 1024 * 1024)
        profile = analyze(path)
        self.assertIsInstance(profile.method_description, str)
        self.assertTrue(len(profile.method_description) > 0)
        self.assertIsInstance(profile.estimated_reduction_str, str)


class TestConfigManager(unittest.TestCase):
    """Tests del gestor de configuración."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Parchear la ruta de config para pruebas
        import utils.config_manager as cm
        self._original_path = cm._CONFIG_PATH
        cm._CONFIG_PATH = Path(self.tmpdir) / "test_config.json"

    def tearDown(self):
        import utils.config_manager as cm
        cm._CONFIG_PATH = self._original_path
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_default_values(self):
        from utils.config_manager import ConfigManager
        import utils.config_manager as cm
        cm._CONFIG_PATH = Path(self.tmpdir) / "test_config.json"
        config = ConfigManager()
        self.assertEqual(config.get("theme"), "light")
        self.assertEqual(config.get("quality_level"), "balanced")
        self.assertTrue(config.get("remove_metadata"))

    def test_set_and_persist(self):
        from utils.config_manager import ConfigManager
        import utils.config_manager as cm
        cm._CONFIG_PATH = Path(self.tmpdir) / "test_config.json"
        config = ConfigManager()
        config.set("theme", "dark")

        config2 = ConfigManager()
        self.assertEqual(config2.get("theme"), "dark")

    def test_reset_to_defaults(self):
        from utils.config_manager import ConfigManager
        import utils.config_manager as cm
        cm._CONFIG_PATH = Path(self.tmpdir) / "test_config.json"
        config = ConfigManager()
        config.set("theme", "dark")
        config.reset_to_defaults()
        self.assertEqual(config.get("theme"), "light")


class TestCompressionResultProperties(unittest.TestCase):
    def test_reduction_zero_when_same_size(self):
        from models.compression_result import CompressionResult
        r = CompressionResult(success=True, original_size=1000, final_size=1000)
        self.assertEqual(r.reduction_percent, 0.0)
        self.assertEqual(r.bytes_saved, 0)

    def test_is_larger_flag(self):
        from models.compression_result import CompressionResult
        r = CompressionResult(success=True, original_size=1000, final_size=1100)
        self.assertTrue(r.is_larger)

    def test_format_elapsed(self):
        from models.compression_result import CompressionResult
        r = CompressionResult(success=True, original_size=0, elapsed_seconds=90.5)
        self.assertIn("m", r.elapsed_str)

    def test_history_entry_dict(self):
        from models.history_entry import HistoryEntry
        entry = HistoryEntry(
            filename="test.pdf", file_type="pdf",
            original_size=1_000_000, final_size=400_000,
            reduction_percent=60.0, elapsed_seconds=1.5,
            output_path="/out/test_optimizado.pdf",
            method_used="TestEngine", success=True,
        )
        d = entry.to_dict()
        self.assertIn("Fecha", d)
        self.assertIn("Reducción %", d)
        self.assertEqual(d["Reducción %"], "60.0%")


if __name__ == "__main__":
    unittest.main()
