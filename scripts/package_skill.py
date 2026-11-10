#!/usr/bin/env python3
"""Build a reproducible, offline Skill ZIP and SHA256SUMS (Python 3.10+).

Only documented source directories and root project files are included. Text is
encoded as UTF-8 with LF line endings; archives use fixed timestamps and stored
entries so platform-specific compression does not change their checksums.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import zipfile

from validate_skill import parse_frontmatter, validate

ROOT_FILES = (
    "SKILL.md", "LICENSE", "README.md", "README.en.md", "CHANGELOG.md",
    "CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md",
    ".editorconfig", ".gitattributes", ".gitignore",
)
SOURCE_DIRS = ("agents", "references", "scripts", "tests", "examples", ".github")
SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".txt"}
EXCLUDED_DIRS = {"__pycache__", ".git", ".venv", "dist", ".pytest_cache", ".ruff_cache"}
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?\Z")


def _is_link(path: Path) -> bool:
    try:
        attributes = path.lstat()
    except FileNotFoundError:
        return False
    # is_junction() is unavailable on Python 3.10/3.11. Windows junctions
    # are reparse points and os.walk may follow them even with followlinks=False.
    return stat.S_ISLNK(attributes.st_mode) or bool(
        getattr(attributes, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    )


def source_files(root: Path) -> list[Path]:
    """Enumerate an allowlist; never follow links into unrelated local files."""
    selected = []
    for filename in ROOT_FILES:
        path = root / filename
        if _is_link(path):
            raise ValueError(f"Refusing linked package file: {filename}")
        if path.is_file():
            selected.append(path)
    for folder in SOURCE_DIRS:
        base = root / folder
        if _is_link(base):
            raise ValueError(f"Refusing linked package directory: {folder}")
        if not base.is_dir():
            continue
        for current, directories, filenames in os.walk(base, followlinks=False):
            for name in list(directories):
                child = Path(current) / name
                if _is_link(child):
                    raise ValueError(f"Refusing linked package directory: {child.relative_to(root)}")
                if name in EXCLUDED_DIRS or name.startswith("."):
                    directories.remove(name)
            for name in filenames:
                path = Path(current) / name
                if _is_link(path):
                    raise ValueError(f"Refusing linked package file: {path.relative_to(root)}")
                if not name.startswith(".") and (path.suffix in SUFFIXES or name == "CODEOWNERS"):
                    selected.append(path)
    for path in selected:
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Package file escapes source directory: {path}")
    return sorted(selected, key=lambda path: path.relative_to(root).as_posix())


def _atomic_write(path: Path, data: bytes) -> None:
    descriptor, name = tempfile.mkstemp(prefix=".xindaya-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def build(root: Path, output: Path) -> Path:
    root = root.resolve()
    issues = validate(root)
    if issues:
        raise ValueError("Package validation failed:\n" + "\n".join(issues))
    if not (root / "LICENSE").is_file():
        raise ValueError("A distributable archive must include LICENSE")
    meta = parse_frontmatter((root / "SKILL.md").read_text(encoding="utf-8-sig"))
    version = meta.get("metadata", {}).get("version", "")
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise ValueError("metadata.version must be a safe semantic version, e.g. 1.1.0")
    name = meta["name"]
    entries = {}
    for path in source_files(root):
        # Encoding errors fail the build rather than shipping a damaged document.
        content = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        entries[path.relative_to(root).as_posix()] = content.encode("utf-8")
    manifest = {
        "name": name,
        "version": version,
        "format": 1,
        "files": {key: hashlib.sha256(value).hexdigest() for key, value in sorted(entries.items())},
    }
    entries["MANIFEST.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"{name}-v{version}.zip"
    descriptor, temp_name = tempfile.mkstemp(prefix=".xindaya-", suffix=".zip", dir=output)
    os.close(descriptor)
    try:
        with zipfile.ZipFile(temp_name, "w", compression=zipfile.ZIP_STORED) as bundle:
            for relative, content in sorted(entries.items()):
                info = zipfile.ZipInfo(f"{name}/{relative}", date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                bundle.writestr(info, content)
        os.replace(temp_name, archive)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    _atomic_write(output / "SHA256SUMS", f"{digest}  {archive.name}\n".encode("ascii"))
    return archive


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="Skill source directory")
    parser.add_argument("--output", type=Path, default=Path("dist"), help="Output directory (default: ./dist)")
    args = parser.parse_args()
    try:
        archive = build(args.root, args.output)
    except (OSError, UnicodeError, ValueError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Built {archive}")
    print(f"Checksums: {archive.parent / 'SHA256SUMS'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
