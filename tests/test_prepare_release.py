"""Exercise release provenance guards and the actual portable release payload."""

import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import unittest
import zipfile
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_release import (
    PAYLOAD_FILES, REPOSITORY, WORKFLOW_REF, checksum_text, prepare_release,
    validate_inputs, verify_archive, verify_payload,
)


class ReleaseInputTests(unittest.TestCase):
    def test_stable_version_and_full_lowercase_commit_are_required(self):
        sha = "a" * 40
        for version in ("v0.0.0", "v0.1.2", "v12.34.56"):
            validate_inputs(version, sha, sha)
        for version in ("0.1.2", "v01.2.3", "v1.02.3", "v1.2.03", "v1.2", "v1.2.3-rc.1",
                        "v1.2.3+build", "v1.2.3\n", " v1.2.3", "v1.2.3;false"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                validate_inputs(version, sha, sha)
        for invalid in ("a" * 39, "a" * 41, "A" * 40, "g" * 40, sha + "\n"):
            with self.subTest(sha=invalid), self.assertRaises(ValueError):
                validate_inputs("v1.2.3", invalid, invalid)
        with self.assertRaisesRegex(ValueError, "GITHUB_SHA"):
            validate_inputs("v1.2.3", sha, "b" * 40)


class PrepareReleaseTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        source = self.root / "skills/security-audit"
        (source / "agents").mkdir(parents=True)
        (source / "SKILL.md").write_text("Synthetic portable skill\n", encoding="utf-8")
        (source / "agents/openai.yaml").write_text("interface: {}\n", encoding="utf-8")
        (source / "LICENSE").write_text("Synthetic MIT notice\n", encoding="utf-8")
        (self.root / "LICENSE").write_text("Synthetic MIT notice\n", encoding="utf-8")
        (self.root / ".gitignore").write_text("dist/\n", encoding="utf-8")
        self.git("init", "--quiet")
        self.commit()

    def git(self, *arguments):
        return subprocess.run(["git", *arguments], cwd=self.root, check=True,
                              text=True, capture_output=True).stdout.strip()

    def commit(self):
        self.git("add", "--all")
        self.git("-c", "user.name=Release Test", "-c", "user.email=release-test@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "Synthetic release fixture")
        self.sha = self.git("rev-parse", "HEAD")
        self.environment = {
            "GITHUB_SHA": self.sha, "GITHUB_REPOSITORY": REPOSITORY,
            "GITHUB_SERVER_URL": "https://github.com", "GITHUB_REF": "refs/heads/main",
            "GITHUB_WORKFLOW_REF": WORKFLOW_REF, "GITHUB_WORKFLOW_SHA": self.sha,
            "GITHUB_RUN_ID": "123", "GITHUB_RUN_ATTEMPT": "2",
        }

    def prepare(self):
        return prepare_release(self.root, "v1.2.3", self.sha, self.environment)

    def test_payload_contains_only_portable_archive_checksums_and_runtime_metadata(self):
        output = self.prepare()
        self.assertEqual({path.name for path in output.iterdir()}, set(PAYLOAD_FILES))
        archive_path = output / "security-audit.zip"
        with zipfile.ZipFile(archive_path) as archive:
            self.assertEqual(set(archive.namelist()), {
                "security-audit/SKILL.md", "security-audit/agents/openai.yaml", "security-audit/LICENSE",
            })
            self.assertEqual(archive.read("security-audit/SKILL.md"),
                             (self.root / "skills/security-audit/SKILL.md").read_bytes())
        metadata = json.loads((output / "build-metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["source"], {
            "repository": REPOSITORY, "ref": "refs/heads/main", "commit": self.sha,
        })
        self.assertEqual(metadata["workflow"]["url"],
                         f"https://github.com/{REPOSITORY}/actions/runs/123/attempts/2")
        self.assertEqual(metadata["runtime"], {
            "python": platform.python_version(), "implementation": platform.python_implementation(),
            "zlib_compile": zlib.ZLIB_VERSION, "zlib_runtime": zlib.ZLIB_RUNTIME_VERSION,
        })
        self.assertEqual(metadata["artifact"]["sha256"], hashlib.sha256(archive_path.read_bytes()).hexdigest())
        self.assertEqual(metadata["artifact"]["size"], archive_path.stat().st_size)
        lines = (output / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        for line in lines:
            digest, name = line.split("  ")
            self.assertEqual(digest, hashlib.sha256((output / name).read_bytes()).hexdigest())
        self.assertNotIn(str(self.root), json.dumps(metadata))

    def test_same_commit_context_and_runtime_produce_identical_payload(self):
        output = self.prepare()
        first = {path.name: path.read_bytes() for path in output.iterdir()}
        self.prepare()
        self.assertEqual({path.name: path.read_bytes() for path in output.iterdir()}, first)

    def test_unexpected_workflow_context_is_rejected_before_packaging(self):
        cases = {
            "GITHUB_SHA": "b" * 40, "GITHUB_REPOSITORY": "other/fork",
            "GITHUB_SERVER_URL": "https://example.invalid", "GITHUB_REF": "refs/heads/feature",
            "GITHUB_WORKFLOW_REF": "other/workflow", "GITHUB_WORKFLOW_SHA": "b" * 40,
            "GITHUB_RUN_ID": "0", "GITHUB_RUN_ATTEMPT": "02",
        }
        for name, value in cases.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                prepare_release(self.root, "v1.2.3", self.sha, {**self.environment, name: value})
            self.assertFalse((self.root / "dist").exists())

    def test_checkout_head_must_match_even_when_environment_claims_expected_commit(self):
        expected = "b" * 40
        environment = {**self.environment, "GITHUB_SHA": expected, "GITHUB_WORKFLOW_SHA": expected}
        with self.assertRaisesRegex(ValueError, "Git HEAD"):
            prepare_release(self.root, "v1.2.3", expected, environment)
        self.assertFalse((self.root / "dist").exists())

    def test_tracked_changes_and_untracked_files_are_rejected(self):
        tracked = self.root / "skills/security-audit/SKILL.md"
        original = tracked.read_bytes()
        tracked.write_bytes(b"Uncommitted instructions\n")
        with self.assertRaisesRegex(ValueError, "clean"):
            self.prepare()
        tracked.write_bytes(original)
        (self.root / "untracked.txt").write_text("Not reviewed\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "clean"):
            self.prepare()
        self.assertFalse((self.root / "dist").exists())

    def test_package_license_mismatch_is_rejected(self):
        (self.root / "LICENSE").write_text("Different terms\n", encoding="utf-8")
        self.commit()
        with self.assertRaisesRegex(ValueError, "licenses must match"):
            self.prepare()
        self.assertFalse((self.root / "dist").exists())

    def test_output_symlink_is_rejected(self):
        try:
            (self.root / "dist").symlink_to(self.root / "skills", target_is_directory=True)
        except OSError as error:
            self.skipTest(f"Symbolic links unavailable: {error}")
        self.commit()
        with self.assertRaisesRegex(ValueError, "regular directory"):
            self.prepare()

    def test_package_source_symlink_is_rejected(self):
        source = self.root / "skills/security-audit/LICENSE"
        source.unlink()
        try:
            source.symlink_to("../../LICENSE")
        except OSError as error:
            self.skipTest(f"Symbolic links unavailable: {error}")
        self.commit()
        with self.assertRaisesRegex(ValueError, "symbolic links"):
            self.prepare()
        self.assertFalse((self.root / "dist").exists())

    def test_unexpected_output_file_is_rejected(self):
        (self.root / "dist").mkdir()
        (self.root / "dist/stale.zip").write_bytes(b"Unexpected artifact")
        with self.assertRaisesRegex(ValueError, "unexpected path"):
            self.prepare()

    def test_tampered_payload_and_unexpected_inventory_are_rejected(self):
        output = self.prepare()
        (output / "security-audit.zip").write_bytes(b"Replaced package")
        with self.assertRaisesRegex(ValueError, "checksum"):
            verify_payload(output, "v1.2.3", self.sha)
        (output / "extra.txt").write_bytes(b"Extra asset")
        with self.assertRaisesRegex(ValueError, "inventory"):
            verify_payload(output, "v1.2.3", self.sha)

    def test_metadata_cannot_claim_a_different_commit_even_with_matching_checksums(self):
        output = self.prepare()
        path = output / "build-metadata.json"
        metadata = json.loads(path.read_text(encoding="utf-8"))
        metadata["source"]["commit"] = "b" * 40
        path.write_text(json.dumps(metadata), encoding="utf-8")
        (output / "SHA256SUMS").write_text(checksum_text(output), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "selected version and commit"):
            verify_payload(output, "v1.2.3", self.sha)

    def test_archive_inventory_and_source_bytes_are_checked(self):
        output = self.prepare()
        archive_path = output / "security-audit.zip"
        with zipfile.ZipFile(archive_path, "a") as archive:
            archive.writestr("security-audit/unreviewed.txt", "Extra content")
        with self.assertRaisesRegex(ValueError, "exactly the three"):
            verify_archive(archive_path, self.root)
        self.prepare()
        (self.root / "skills/security-audit/SKILL.md").write_text("Different source\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "differs from"):
            verify_archive(archive_path, self.root)


if __name__ == "__main__":
    unittest.main()
