#!/usr/bin/env python3
"""Build a reproducible ZIP containing only the portable skill and MIT license."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys
import zipfile


PORTABLE_FILES = ("SKILL.md", "agents/openai.yaml", "LICENSE")


def build_package(repository: Path) -> Path:
    root = repository.resolve()
    source = root / "skills/security-audit"
    payload: dict[str, bytes] = {}
    for relative in PORTABLE_FILES:
        path = source / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Missing regular package source: {path}")
        payload[relative] = path.read_bytes()
    license_path = root / "LICENSE"
    if license_path.is_symlink() or not license_path.is_file():
        raise ValueError("Root LICENSE must be a regular file")
    if payload["LICENSE"] != license_path.read_bytes():
        raise ValueError("Portable and root licenses must match")

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in sorted(payload):
            entry = zipfile.ZipInfo(f"security-audit/{relative}", date_time=(2026, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, payload[relative])
    destination = root / "dist/security-audit.zip"
    destination.parent.mkdir(exist_ok=True)
    destination.write_bytes(buffer.getvalue())
    return destination


def main() -> int:
    try:
        destination = build_package(Path(__file__).resolve().parents[1])
    except (OSError, ValueError) as error:
        print(f"Packaging failed: {error}", file=sys.stderr)
        return 1
    print(f"Created {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
