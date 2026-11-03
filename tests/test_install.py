"""Filesystem integration tests for the dependency-free installer."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


INSTALLER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "install.py"
SPEC = importlib.util.spec_from_file_location("security_audit_installer", INSTALLER_PATH)
assert SPEC is not None and SPEC.loader is not None
installer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer
SPEC.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="security-audit-installer-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.repository = self.root / "checkout"
        self.source = self.repository / "skills" / "security-audit"
        (self.source / "agents").mkdir(parents=True)
        (self.source / "SKILL.md").write_text("---\nname: security-audit\n---\nReview supported findings.\n", encoding="utf-8")
        (self.source / "agents" / "openai.yaml").write_text("interface:\n  display_name: Security Audit\n", encoding="utf-8")
        (self.repository / "LICENSE").write_text("MIT License\nFixture copyright\n", encoding="utf-8")
        self.home = self.root / "temporary home"
        self.home.mkdir()

    def destination(self, target: str, base: Path | None = None) -> Path:
        folder = ".claude" if target == "claude" else ".agents"
        return (base or self.home) / folder / "skills" / "security-audit"

    def run_install(self, **options):
        return installer.install(self.repository, home=self.home, **options)

    def symlink(self, destination: Path, source: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            destination.symlink_to(source, target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"Directory symlinks are unavailable: {error}")

    def snapshot(self, directory: Path) -> dict[str, bytes]:
        return {
            path.relative_to(directory).as_posix(): path.read_bytes()
            for path in directory.rglob("*")
            if path.is_file()
        }

    def test_both_targets_receive_only_portable_files_and_root_license(self) -> None:
        (self.source / "machine-private.txt").write_text("exclude me", encoding="utf-8")
        (self.source / "hooks").mkdir()
        (self.source / "hooks" / "run.sh").write_text("do not install", encoding="utf-8")
        (self.repository / "README.md").write_text("Repository documentation", encoding="utf-8")

        results = self.run_install()

        self.assertEqual([result.status for result in results], ["installed", "installed"])
        expected = {
            "SKILL.md": (self.source / "SKILL.md").read_bytes(),
            "agents/openai.yaml": (self.source / "agents" / "openai.yaml").read_bytes(),
            "LICENSE": (self.repository / "LICENSE").read_bytes(),
        }
        for target in ("claude", "codex"):
            with self.subTest(target=target):
                self.assertEqual(self.snapshot(self.destination(target)), expected)

    def test_single_target_does_not_create_other_target(self) -> None:
        self.run_install(target="codex")
        self.assertTrue(self.destination("codex").is_dir())
        self.assertFalse((self.home / ".claude").exists())

    def test_identical_install_is_noop_preserving_files_and_timestamps(self) -> None:
        self.run_install()
        paths = [path for path in self.home.rglob("*") if path.is_file()]
        for path in paths:
            os.utime(path, ns=(1_600_000_000_000_000_000, 1_600_000_000_000_000_000))
        before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}

        results = self.run_install()

        self.assertEqual([result.status for result in results], ["unchanged", "unchanged"])
        self.assertEqual({path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}, before)

    def test_changed_install_is_refused_and_preserved(self) -> None:
        self.run_install(target="codex")
        customized = self.destination("codex") / "SKILL.md"
        customized.write_text("My existing customization\n", encoding="utf-8")
        before = self.snapshot(self.destination("codex"))

        with self.assertRaisesRegex(installer.InstallError, "Back up and remove"):
            self.run_install()

        self.assertEqual(self.snapshot(self.destination("codex")), before)
        self.assertFalse((self.home / ".claude").exists())

    def test_extra_files_make_existing_install_divergent(self) -> None:
        self.run_install(target="claude")
        extra = self.destination("claude") / "personal-notes.md"
        extra.write_text("Preserve this", encoding="utf-8")

        with self.assertRaises(installer.InstallError):
            self.run_install(target="claude")

        self.assertEqual(extra.read_text(encoding="utf-8"), "Preserve this")

    def test_empty_existing_directory_is_refused(self) -> None:
        destination = self.destination("claude")
        destination.mkdir(parents=True)

        with self.assertRaises(installer.InstallError):
            self.run_install()

        self.assertEqual(list(destination.iterdir()), [])
        self.assertFalse((self.home / ".agents").exists())

    def test_existing_file_is_refused_without_partial_other_target(self) -> None:
        destination = self.destination("codex")
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b"preserve existing file")

        with self.assertRaisesRegex(installer.InstallError, "Refusing to overwrite"):
            self.run_install()

        self.assertEqual(destination.read_bytes(), b"preserve existing file")
        self.assertFalse((self.home / ".claude").exists())

    def test_parent_file_blocks_all_targets_before_writes(self) -> None:
        parent_file = self.home / ".agents"
        parent_file.write_bytes(b"not a directory")

        with self.assertRaisesRegex(installer.InstallError, "parent is not a directory"):
            self.run_install()

        self.assertEqual(parent_file.read_bytes(), b"not a directory")
        self.assertFalse((self.home / ".claude").exists())

    def test_symlink_to_current_source_is_noop_and_other_target_installs(self) -> None:
        destination = self.destination("claude")
        relative_source = Path(os.path.relpath(self.source, destination.parent))
        self.symlink(destination, relative_source)
        before = os.readlink(destination)

        results = self.run_install()

        self.assertEqual([result.status for result in results], ["source-link", "installed"])
        self.assertTrue(destination.is_symlink())
        self.assertEqual(os.readlink(destination), before)
        self.assertFalse((self.source / "LICENSE").exists())
        self.assertEqual((self.destination("codex") / "LICENSE").read_bytes(), (self.repository / "LICENSE").read_bytes())

    def test_symlink_to_another_checkout_is_refused_and_preserved(self) -> None:
        other_source = self.root / "older-checkout"
        shutil.copytree(self.source, other_source)
        destination = self.destination("codex")
        self.symlink(destination, other_source)

        with self.assertRaises(installer.InstallError):
            self.run_install()

        self.assertTrue(destination.is_symlink())
        self.assertEqual(destination.resolve(), other_source)
        self.assertFalse((self.home / ".claude").exists())

    def test_dangling_symlink_is_refused_and_preserved(self) -> None:
        destination = self.destination("codex")
        missing = self.root / "missing-checkout"
        self.symlink(destination, missing)
        original_link = os.readlink(destination)

        with self.assertRaises(installer.InstallError):
            self.run_install()

        self.assertTrue(destination.is_symlink())
        self.assertEqual(os.readlink(destination), original_link)
        self.assertFalse((self.home / ".claude").exists())

    def test_symlinks_inside_installed_folder_are_not_treated_as_identical(self) -> None:
        self.run_install(target="codex")
        skill = self.destination("codex") / "SKILL.md"
        skill.unlink()
        try:
            skill.symlink_to(self.source / "SKILL.md")
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"File symlinks are unavailable: {error}")

        with self.assertRaises(installer.InstallError):
            self.run_install()

        self.assertTrue(skill.is_symlink())
        self.assertFalse((self.home / ".claude").exists())

    def test_missing_required_source_fails_before_creating_targets(self) -> None:
        required_files = (
            self.source / "SKILL.md",
            self.source / "agents" / "openai.yaml",
            self.repository / "LICENSE",
        )
        for path in required_files:
            with self.subTest(missing=path.name):
                content = path.read_bytes()
                path.unlink()
                try:
                    with self.assertRaisesRegex(installer.InstallError, "Required source file"):
                        self.run_install()
                    self.assertEqual(list(self.home.iterdir()), [])
                finally:
                    path.write_bytes(content)

    def test_dry_run_validates_without_creating_directories(self) -> None:
        results = self.run_install(dry_run=True)
        self.assertEqual([result.status for result in results], ["would-install", "would-install"])
        self.assertEqual(list(self.home.iterdir()), [])

    def test_dry_run_refuses_collision(self) -> None:
        self.destination("codex").mkdir(parents=True)
        before = set(self.home.rglob("*"))

        with self.assertRaises(installer.InstallError):
            self.run_install(dry_run=True)

        self.assertEqual(set(self.home.rglob("*")), before)

    def test_project_destination_takes_precedence_over_personal_home(self) -> None:
        project = self.root / "project with spaces"
        project.mkdir()

        self.run_install(project=project)

        self.assertTrue(self.destination("claude", project).is_dir())
        self.assertTrue(self.destination("codex", project).is_dir())
        self.assertEqual(list(self.home.iterdir()), [])

    def test_missing_project_is_not_created(self) -> None:
        missing_project = self.root / "does-not-exist"

        with self.assertRaisesRegex(installer.InstallError, "Project directory does not exist"):
            self.run_install(project=missing_project)

        self.assertFalse(missing_project.exists())
        self.assertEqual(list(self.home.iterdir()), [])

    def test_write_failure_rolls_back_only_new_installations_and_parents(self) -> None:
        preserved_parent = self.home / ".agents"
        preserved_parent.mkdir()
        sentinel = preserved_parent / "existing-config"
        sentinel.write_bytes(b"unrelated user data")
        original_open = Path.open
        failing_file = self.destination("codex") / "SKILL.md"

        def fail_second_destination(path, mode="r", *args, **kwargs):
            if path == failing_file and mode == "xb":
                raise OSError("simulated disk write failure")
            return original_open(path, mode, *args, **kwargs)

        with mock.patch.object(Path, "open", new=fail_second_destination):
            with self.assertRaisesRegex(installer.InstallError, "rolled back"):
                self.run_install()

        self.assertFalse((self.home / ".claude").exists())
        self.assertFalse(self.destination("codex").exists())
        self.assertTrue(preserved_parent.is_dir())
        self.assertEqual(sentinel.read_bytes(), b"unrelated user data")
        self.assertEqual(list(preserved_parent.iterdir()), [sentinel])

    def test_write_failure_preserves_existing_identical_installation(self) -> None:
        self.run_install(target="claude")
        existing = self.snapshot(self.destination("claude"))
        original_open = Path.open
        failing_file = self.destination("codex") / "LICENSE"

        def fail_license_write(path, mode="r", *args, **kwargs):
            if path == failing_file and mode == "xb":
                raise OSError("simulated disk write failure")
            return original_open(path, mode, *args, **kwargs)

        with mock.patch.object(Path, "open", new=fail_license_write):
            with self.assertRaises(installer.InstallError):
                self.run_install()

        self.assertEqual(self.snapshot(self.destination("claude")), existing)
        self.assertFalse((self.home / ".agents").exists())

    def test_cli_installs_from_its_checkout_into_project(self) -> None:
        script = self.repository / "scripts" / "install.py"
        script.parent.mkdir()
        shutil.copyfile(INSTALLER_PATH, script)
        project = self.root / "CLI project with spaces"
        project.mkdir()

        result = subprocess.run(
            [sys.executable, str(script), "--target", "codex", "--project", str(project)],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("codex: Installed:", result.stdout)
        self.assertEqual((self.destination("codex", project) / "LICENSE").read_bytes(), (self.repository / "LICENSE").read_bytes())
        self.assertFalse((project / ".claude").exists())

    def test_cli_missing_source_returns_actionable_error_without_writes(self) -> None:
        script = self.repository / "scripts" / "install.py"
        script.parent.mkdir()
        shutil.copyfile(INSTALLER_PATH, script)
        (self.repository / "LICENSE").unlink()

        result = subprocess.run(
            [sys.executable, str(script), "--project", str(self.home)],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("Required source file", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(list(self.home.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
