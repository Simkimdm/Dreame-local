"""resolve_material: leer -> Fallback, Pfad bleibt Pfad, inline-PEM wird nach /data/generated materialisiert."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dreame_local" / "app"))
from certutil import resolve_material


class ResolveMaterialTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data_dir = Path(self.tmp.name)

    def test_empty_uses_fallback(self):
        self.assertEqual(resolve_material("", "/fallback.pem", self.data_dir, "x.pem"), "/fallback.pem")
        self.assertEqual(resolve_material("   ", "/fallback.pem", self.data_dir, "x.pem"), "/fallback.pem")
        self.assertEqual(resolve_material(None, "/fallback.pem", self.data_dir, "x.pem"), "/fallback.pem")  # type: ignore[arg-type]

    def test_path_passthrough(self):
        self.assertEqual(
            resolve_material("/data/certs/api_chain.pem", "/fallback.pem", self.data_dir, "x.pem"),
            "/data/certs/api_chain.pem",
        )

    def test_inline_pem_is_materialized(self):
        pem = "-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----"
        out = resolve_material(pem, "/fallback.pem", self.data_dir, "api_chain.pem")
        self.assertEqual(out, str(self.data_dir / "generated" / "api_chain.pem"))
        self.assertIn("-----BEGIN CERTIFICATE-----", Path(out).read_text())


if __name__ == "__main__":
    unittest.main()
