#!/usr/bin/env python3
"""Install the portable security-audit skill using only Python's standard library."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import sys
from typing import Mapping


SKILL_NAME = "security-audit"
PORTABLE_FILES = (Path("SKILL.md"), Path("agents/openai.yaml"))
TARGET_PATHS = {"claude": Path(".claude/skills"), "codex": Path(".agents/skills")}


class InstallError(RuntimeError):
    """An installation cannot proceed safely."""


@dataclass(frozen=True)
class InstallResult:
    target: str
    destination: Path
    status: str


def _exists(path: Path) -> bool:
    """Include dangling symlinks in collision checks."""
    return os.path.lexists(path)


def _source_files(repository: Path) -> tuple[Path, dict[Path, bytes]]:
    source = repository / "skills" / SKILL_NAME
    required = {relative: source / relative for relative in PORTABLE_FILES}
    required[Path("LICENSE")] = repository / "LICENSE"
    contents = {}
    for relative, path in required.items():
        if path.is_symlink() or not path.is_file():
            raise InstallError(f"Required source file is missing or is not a regular file: {path}")
        try:
            contents[relative] = path.read_bytes()
        except OSError as error:
            raise InstallError(f"Cannot read required source file {path}: {error}") from error
    return source.resolve(), contents


def _identical(destination: Path, contents: Mapping[Path, bytes]) -> bool:
    expected_directories = {
        parent
        for relative in contents
        for parent in relative.parents
        if parent != Path(".")
    }
    actual_files = set()
    actual_directories = set()

    def inspect(directory: Path) -> bool:
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                relative = path.relative_to(destination)
                if entry.is_symlink():
                    return False
                if entry.is_dir(follow_symlinks=False):
                    actual_directories.add(relative)
                    if relative not in expected_directories or not inspect(path):
                        return False
                elif entry.is_file(follow_symlinks=False):
                    actual_files.add(relative)
                    if relative not in contents or path.read_bytes() != contents[relative]:
                        return False
                else:
                    return False
        return True

    return (
        inspect(destination)
        and actual_files == set(contents)
        and actual_directories == expected_directories
    )


def _collision(destination: Path) -> InstallError:
    return InstallError(
        f"Refusing to overwrite existing destination: {destination}. "
        "Back up and remove the previous installation, then run this installer again. "
        "Existing installations must exactly match the packaged files, or be a symlink "
        "to this checkout's skills/security-audit directory."
    )


def _preflight(destination: Path, source: Path, contents: Mapping[Path, bytes]) -> str:
    if destination.is_symlink():
        try:
            if destination.resolve(strict=True) == source:
                return "source-link"
        except OSError:
            pass
        except RuntimeError:  # A symlink loop on Python versions using RuntimeError.
            pass
        raise _collision(destination)
    if _exists(destination):
        try:
            if destination.is_dir() and _identical(destination, contents):
                return "unchanged"
        except OSError as error:
            raise InstallError(f"Cannot inspect existing destination {destination}: {error}") from error
        raise _collision(destination)
    for parent in destination.parents:
        if _exists(parent):
            if not parent.is_dir():
                raise InstallError(f"Installation parent is not a directory: {parent}")
            break
    return "install"


def _make_parents(directory: Path, created: list[Path]) -> None:
    missing = []
    current = directory
    while not _exists(current):
        missing.append(current)
        current = current.parent
    for path in reversed(missing):
        try:
            path.mkdir()
        except FileExistsError:
            if not path.is_dir():
                raise
        else:
            created.append(path)


def install(
    repository: Path,
    *,
    target: str = "both",
    project: Path | None = None,
    home: Path | None = None,
    dry_run: bool = False,
) -> list[InstallResult]:
    """Preflight all targets, then install; never replace an existing destination.

    ``home`` is an explicit destination base for library callers and tests. The CLI
    defaults to Path.home() unless --project selects an existing project directory.
    """
    if target not in (*TARGET_PATHS, "both"):
        raise InstallError(f"Unknown target: {target}")
    repository = Path(repository).expanduser().resolve()
    source, contents = _source_files(repository)
    base = Path(project) if project is not None else (Path(home) if home is not None else Path.home())
    base = base.expanduser().resolve()
    if not base.is_dir():
        location = "Project" if project is not None else "Home"
        raise InstallError(f"{location} directory does not exist or is not a directory: {base}")

    selected = tuple(TARGET_PATHS) if target == "both" else (target,)
    plan = [
        InstallResult(name, base / TARGET_PATHS[name] / SKILL_NAME, "")
        for name in selected
    ]
    plan = [
        InstallResult(item.target, item.destination, _preflight(item.destination, source, contents))
        for item in plan
    ]
    if dry_run:
        return [
            InstallResult(item.target, item.destination, "would-install" if item.status == "install" else item.status)
            for item in plan
        ]

    created_destinations: list[Path] = []
    created_parents: list[Path] = []
    results = []
    try:
        for item in plan:
            if item.status != "install":
                results.append(item)
                continue
            _make_parents(item.destination.parent, created_parents)
            item.destination.mkdir()  # exist_ok=False prevents replacing a late collision.
            created_destinations.append(item.destination)
            for relative, content in contents.items():
                path = item.destination / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as output:
                    output.write(content)
            results.append(InstallResult(item.target, item.destination, "installed"))
    except BaseException as error:
        cleanup_failures = []
        for destination in reversed(created_destinations):
            try:
                shutil.rmtree(destination)
            except OSError as cleanup_error:
                cleanup_failures.append(f"{destination}: {cleanup_error}")
        for parent in reversed(created_parents):
            try:
                parent.rmdir()  # Only remove empty parent directories created by this run.
            except OSError:
                pass
        if not isinstance(error, Exception):
            raise
        detail = f" Cleanup could not remove: {'; '.join(cleanup_failures)}." if cleanup_failures else ""
        raise InstallError(f"Installation failed; newly created installations were rolled back: {error}.{detail}") from error
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("both", "claude", "codex"), default="both")
    parser.add_argument("--project", type=Path, metavar="PATH", help="install in an existing project's .claude/skills and/or .agents/skills")
    parser.add_argument("--dry-run", action="store_true", help="check all destinations without writing files")
    args = parser.parse_args(argv)
    try:
        results = install(Path(__file__).resolve().parents[1], target=args.target, project=args.project, dry_run=args.dry_run)
    except InstallError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    labels = {
        "installed": "Installed",
        "unchanged": "Already installed; unchanged",
        "source-link": "Already linked to this checkout; unchanged",
        "would-install": "Would install",
    }
    for result in results:
        print(f"{result.target}: {labels[result.status]}: {result.destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
