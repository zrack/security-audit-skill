#!/usr/bin/env python3
"""Prepare a release payload from the exact clean commit selected in Actions."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import stat
import subprocess
import sys
from typing import Mapping
import zipfile
import zlib

from package import PORTABLE_FILES, build_package


REPOSITORY = "zrack/security-audit-skill"
WORKFLOW_REF = f"{REPOSITORY}/.github/workflows/release.yml@refs/heads/main"
PAYLOAD_FILES = ("security-audit.zip", "build-metadata.json", "SHA256SUMS")
VERSION_PATTERN = re.compile(r"v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")
SHA_PATTERN = re.compile(r"[0-9a-f]{40}")


def validate_inputs(version: str, expected_sha: str, github_sha: str) -> None:
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError("Version must be a stable vX.Y.Z without leading zeroes")
    if not SHA_PATTERN.fullmatch(expected_sha):
        raise ValueError("Expected SHA must contain exactly 40 lowercase hexadecimal characters")
    if not SHA_PATTERN.fullmatch(github_sha) or github_sha != expected_sha:
        raise ValueError("Expected SHA must exactly match GITHUB_SHA")


def git_output(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=repository, text=True, capture_output=True, check=True,
    )
    return result.stdout.strip()


def validate_context(repository: Path, version: str, expected_sha: str, environment: Mapping[str, str]) -> None:
    validate_inputs(version, expected_sha, environment.get("GITHUB_SHA", ""))
    required = {
        "GITHUB_REPOSITORY": REPOSITORY,
        "GITHUB_SERVER_URL": "https://github.com",
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_WORKFLOW_REF": WORKFLOW_REF,
        "GITHUB_WORKFLOW_SHA": expected_sha,
    }
    for name, expected in required.items():
        if environment.get(name) != expected:
            raise ValueError(f"Unexpected release context: {name}")
    for name in ("GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT"):
        if not re.fullmatch(r"[1-9][0-9]*", environment.get(name, "")):
            raise ValueError(f"Invalid release context: {name}")
    if Path(git_output(repository, "rev-parse", "--show-toplevel")).resolve() != repository:
        raise ValueError("Release repository must be the Git checkout root")
    if git_output(repository, "rev-parse", "HEAD") != expected_sha:
        raise ValueError("Git HEAD must exactly match the expected SHA")
    if git_output(repository, "status", "--porcelain", "--untracked-files=normal"):
        raise ValueError("Release checkout must be clean, including untracked files")


def regular_source(path: Path, repository: Path) -> None:
    if not path.resolve().is_relative_to(repository):
        raise ValueError("Package source must remain inside the repository")
    if any(parent.is_symlink() for parent in (path, *path.parents) if parent != repository):
        raise ValueError("Package sources must not use symbolic links")
    if not path.is_file():
        raise ValueError(f"Missing regular package source: {path.name}")


def verify_archive(archive_path: Path, repository: Path) -> None:
    expected = {f"security-audit/{relative}" for relative in PORTABLE_FILES}
    with zipfile.ZipFile(archive_path) as archive:
        if len(archive.infolist()) != len(expected) or set(archive.namelist()) != expected:
            raise ValueError("Portable archive must contain exactly the three portable files")
        if archive.testzip() is not None:
            raise ValueError("Portable archive failed its CRC check")
        for entry in archive.infolist():
            if entry.is_dir() or not stat.S_ISREG(entry.external_attr >> 16) or entry.flag_bits & 1:
                raise ValueError("Portable archive must contain only unencrypted regular files")
            relative = entry.filename.removeprefix("security-audit/")
            if archive.read(entry) != (repository / "skills/security-audit" / relative).read_bytes():
                raise ValueError("Portable archive differs from the selected source files")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checksum_text(directory: Path) -> str:
    return "".join(f"{sha256(directory / name)}  {name}\n" for name in sorted(PAYLOAD_FILES) if name != "SHA256SUMS")


def verify_payload(directory: Path, version: str, expected_sha: str) -> None:
    if {path.name for path in directory.iterdir()} != set(PAYLOAD_FILES):
        raise ValueError("Release payload has an unexpected file inventory")
    for name in PAYLOAD_FILES:
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("Release payload must contain only regular files")
    if (directory / "SHA256SUMS").read_text(encoding="utf-8") != checksum_text(directory):
        raise ValueError("Release payload checksum mismatch")
    metadata = json.loads((directory / "build-metadata.json").read_text(encoding="utf-8"))
    if metadata.get("version") != version or metadata.get("source") != {
        "repository": REPOSITORY, "ref": "refs/heads/main", "commit": expected_sha,
    }:
        raise ValueError("Release metadata does not match the selected version and commit")
    if metadata.get("artifact") != {
        "name": "security-audit.zip", "sha256": sha256(directory / "security-audit.zip"),
        "size": (directory / "security-audit.zip").stat().st_size,
    }:
        raise ValueError("Release metadata does not match the portable archive")


def prepare_release(repository: Path, version: str, expected_sha: str, environment: Mapping[str, str] | None = None) -> Path:
    root = repository.resolve()
    environment = os.environ if environment is None else environment
    validate_context(root, version, expected_sha, environment)
    for relative in PORTABLE_FILES:
        regular_source(root / "skills/security-audit" / relative, root)
    regular_source(root / "LICENSE", root)
    destination = root / "dist"
    if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
        raise ValueError("Release output must be a regular directory")
    if destination.exists():
        if any(path.name not in PAYLOAD_FILES or path.is_symlink() or not path.is_file() for path in destination.iterdir()):
            raise ValueError("Release output contains an unexpected path")
    archive = build_package(root)
    verify_archive(archive, root)
    run_id = environment["GITHUB_RUN_ID"]
    run_attempt = environment["GITHUB_RUN_ATTEMPT"]
    metadata = {
        "schema_version": 1,
        "version": version,
        "source": {"repository": REPOSITORY, "ref": "refs/heads/main", "commit": expected_sha},
        "workflow": {
            "ref": environment["GITHUB_WORKFLOW_REF"], "commit": environment["GITHUB_WORKFLOW_SHA"],
            "run_id": run_id, "run_attempt": run_attempt,
            "url": f"https://github.com/{REPOSITORY}/actions/runs/{run_id}/attempts/{run_attempt}",
        },
        "runtime": {
            "python": platform.python_version(), "implementation": platform.python_implementation(),
            "zlib_compile": zlib.ZLIB_VERSION, "zlib_runtime": zlib.ZLIB_RUNTIME_VERSION,
        },
        "artifact": {"name": archive.name, "sha256": sha256(archive), "size": archive.stat().st_size},
    }
    (destination / "build-metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (destination / "SHA256SUMS").write_text(checksum_text(destination), encoding="utf-8")
    verify_payload(destination, version, expected_sha)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--expected-sha", required=True)
    arguments = parser.parse_args()
    try:
        directory = prepare_release(Path(__file__).resolve().parents[1], arguments.version, arguments.expected_sha)
    except (OSError, ValueError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        print(f"Release preparation failed: {error}", file=sys.stderr)
        return 1
    print(f"Prepared verified release payload in {directory.name}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
