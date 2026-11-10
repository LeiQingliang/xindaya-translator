"""Portable archive behavior: reproducibility, integrity and scope."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import package_skill  # noqa: E402


class PackageTests(unittest.TestCase):
    def make_skill(self, base: Path) -> Path:
        root = base / "xindaya-translator"
        root.mkdir()
        (root / "SKILL.md").write_text(
            '---\nname: xindaya-translator\ndescription: Translate content into Chinese.\n'
            'metadata:\n  version: "1.1.0"\n---\n\nTranslate the supplied text.\n',
            encoding="utf-8",
        )
        (root / "LICENSE").write_text("Test license\n", encoding="utf-8")
        return root

    def test_archive_reproducible_and_manifest_matches(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = self.make_skill(base)
            first = package_skill.build(root, base / "one")
            second = package_skill.build(root, base / "two")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as bundle:
                manifest = json.loads(bundle.read("xindaya-translator/MANIFEST.json"))
                for relative, expected in manifest["files"].items():
                    self.assertEqual(hashlib.sha256(bundle.read(f"xindaya-translator/{relative}")).hexdigest(), expected)
                self.assertTrue(all(not path.startswith("/") and ".." not in path.split("/") for path in bundle.namelist()))
            checksum = (first.parent / "SHA256SUMS").read_text(encoding="ascii").split()[0]
            self.assertEqual(checksum, hashlib.sha256(first.read_bytes()).hexdigest())

    def test_unrelated_files_and_caches_are_excluded(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = self.make_skill(base)
            (root / ".env").write_text("PRIVATE=example", encoding="utf-8")
            (root / "unrelated.txt").write_text("private", encoding="utf-8")
            cache = root / "scripts" / "__pycache__"
            cache.mkdir(parents=True)
            (cache / "secret.txt").write_text("private", encoding="utf-8")
            archive = package_skill.build(root, base / "out")
            with zipfile.ZipFile(archive) as bundle:
                self.assertEqual(len(bundle.namelist()), 3)

    def test_line_endings_do_not_change_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = self.make_skill(base)
            first = package_skill.build(root, base / "one").read_bytes()
            skill = root / "SKILL.md"
            skill.write_bytes(skill.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
            self.assertEqual(first, package_skill.build(root, base / "two").read_bytes())

    def test_missing_license_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = self.make_skill(base)
            (root / "LICENSE").unlink()
            with self.assertRaisesRegex(ValueError, "LICENSE"):
                package_skill.build(root, base / "out")

    def test_linked_file_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = self.make_skill(base)
            outside = base / "private.txt"
            outside.write_text("private", encoding="utf-8")
            try:
                (root / "README.md").symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("Platform does not permit creating symbolic links")
            with self.assertRaisesRegex(ValueError, "linked"):
                package_skill.source_files(root)

    @unittest.skipUnless(os.name == "nt", "Windows junction behavior")
    def test_windows_junction_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = self.make_skill(base)
            outside = base / "private"
            outside.mkdir()
            (outside / "private.txt").write_text("private", encoding="utf-8")
            scripts = root / "scripts"
            scripts.mkdir()
            junction = scripts / "external"
            result = subprocess.run(
                ["cmd", "/d", "/c", "mklink", "/J", str(junction), str(outside)],
                capture_output=True,
            )
            if result.returncode:
                self.fail(f"Could not create junction fixture: {result.stderr!r}")
            try:
                with self.assertRaisesRegex(ValueError, "linked"):
                    package_skill.source_files(root)
            finally:
                # Remove the junction itself, never recursively delete its target.
                os.rmdir(junction)
            self.assertTrue((outside / "private.txt").is_file())


if __name__ == "__main__":
    unittest.main()
