"""Unit tests for VariantManager."""

import unittest
import tempfile
from pathlib import Path
from resume_forge.core.variants import VariantManager


class TestVariantManager(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.vm = VariantManager(base_dir=self.tmpdir.name)
        self.sample_src = Path(__file__).parent.parent / "examples" / "kanishk_cern_fullstack_resume.tex"

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_create_and_list_variants(self):
        self.assertEqual(len(self.vm.list_variants()), 0)
        self.vm.create_variant("frontend", str(self.sample_src))
        self.vm.create_variant("backend", str(self.sample_src))

        variants = self.vm.list_variants()
        self.assertEqual(len(variants), 2)
        names = [v["name"] for v in variants]
        self.assertIn("frontend", names)
        self.assertIn("backend", names)

    def test_diff_variants(self):
        self.vm.create_variant("v1", str(self.sample_src))
        self.vm.create_variant("v2", str(self.sample_src))

        # Initially identical
        diff_same = self.vm.diff_variants("v1", "v2")
        self.assertEqual(diff_same, "")

        # Modify v2
        p2 = self.vm.get_variant_path("v2")
        p2.write_text(p2.read_text(encoding="utf-8") + "\n% extra comment", encoding="utf-8")

        diff_changed = self.vm.diff_variants("v1", "v2")
        self.assertIn("extra comment", diff_changed)

    def test_compile_variant(self):
        self.vm.create_variant("cern", str(self.sample_src))
        out_pdf = Path(self.tmpdir.name) / "cern.pdf"
        success = self.vm.compile_variant("cern", output_pdf=str(out_pdf))
        self.assertTrue(success)
        self.assertTrue(out_pdf.exists())
        self.assertGreater(out_pdf.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
