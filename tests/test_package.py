"""Verify the distributable keeps its license and excludes repository-only files."""

from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from package import build_package


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        source = self.root / "skills/security-audit"
        (source / "agents").mkdir(parents=True)
        (source / "SKILL.md").write_text("Synthetic skill\n", encoding="utf-8")
        (source / "agents/openai.yaml").write_text('interface: {}\n', encoding="utf-8")
        (source / "LICENSE").write_text("MIT notice\n", encoding="utf-8")
        (self.root / "LICENSE").write_text("MIT notice\n", encoding="utf-8")

    def test_only_portable_files_and_license_are_distributed(self):
        (self.root / ".env").write_text("SYNTHETIC=private\n", encoding="utf-8")
        (self.root / "README.md").write_text("Repository docs\n", encoding="utf-8")
        (self.root / "skills/security-audit/scratch.txt").write_text("Not portable\n", encoding="utf-8")
        with zipfile.ZipFile(build_package(self.root)) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(set(archive.namelist()), {
                "security-audit/SKILL.md",
                "security-audit/agents/openai.yaml",
                "security-audit/LICENSE",
            })
            self.assertEqual(archive.read("security-audit/LICENSE"), (self.root / "LICENSE").read_bytes())

    def test_repeated_build_is_reproducible(self):
        first = build_package(self.root).read_bytes()
        self.assertEqual(build_package(self.root).read_bytes(), first)

    def test_missing_source_creates_no_archive(self):
        (self.root / "skills/security-audit/SKILL.md").unlink()
        with self.assertRaises(ValueError):
            build_package(self.root)
        self.assertFalse((self.root / "dist").exists())

    def test_license_mismatch_creates_no_archive(self):
        (self.root / "LICENSE").write_text("Different terms\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            build_package(self.root)
        self.assertFalse((self.root / "dist").exists())


if __name__ == "__main__":
    unittest.main()
