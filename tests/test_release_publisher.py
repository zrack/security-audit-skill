"""Run the actual workflow publisher against an offline GitHub command fixture."""

from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest
from unittest.mock import patch


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/release.yml"
PUBLISHER_STEP = "      - name: Stage assets, publish, and check immutability\n"
publisher_step = WORKFLOW.read_text(encoding="utf-8").split(PUBLISHER_STEP, 1)[1]
publisher_body = publisher_step.split("          python3 - <<'PY'\n", 1)[1].split("\n          PY", 1)[0]
PUBLISHER = compile(textwrap.dedent(publisher_body), str(WORKFLOW), "exec")
ASSETS = {"security-audit.zip", "build-metadata.json", "SHA256SUMS", "security-audit.intoto.jsonl"}
VERSION = "v1.2.3"
COMMIT = "a" * 40
BASE = "repos/zrack/security-audit-skill"


class OfflineGitHub:
    """Small stateful service fixture; no publisher decisions are implemented here."""

    def __init__(self, *, tag_sha=None, releases=None, corrupt=None, immutable=True):
        self.tag_sha = tag_sha
        self.releases = [] if releases is None else releases
        self.corrupt = corrupt
        self.immutable = immutable
        self.assets = []
        self.calls = []
        self.writes = []
        self.created_files = []
        self.notes = ""

    def run(self, command, *, input, text, capture_output):
        if command[0] != "gh" or text is not True or capture_output is not True:
            raise AssertionError(f"Unexpected subprocess: {command}")
        payload = None if input is None else json.loads(input)
        self.calls.append((command, payload))
        if command[1] == "api":
            path = command[2]
            if path == f"{BASE}/releases?per_page=100":
                response = [self.releases]
            elif path == f"{BASE}/git/matching-refs/tags/{VERSION}":
                response = [] if self.tag_sha is None else [{
                    "ref": f"refs/tags/{VERSION}", "object": {"type": "commit", "sha": self.tag_sha},
                }]
            elif path == f"{BASE}/git/refs" and "POST" in command:
                self.writes.append("create-tag")
                self.tag_sha = payload["sha"]
                response = {"ref": payload["ref"], "object": {"type": "commit", "sha": self.tag_sha}}
            elif path == f"{BASE}/releases/123/assets?per_page=100":
                response = [dict(asset) for asset in self.assets]
                if self.corrupt == "digest":
                    response[0]["digest"] = "sha256:" + "0" * 64
                elif self.corrupt == "size":
                    response[0]["size"] += 1
                elif self.corrupt == "inventory":
                    response.append({**response[0], "name": "unexpected.zip"})
            elif path == f"{BASE}/releases/123":
                response = self.releases[0]
            else:
                raise AssertionError(f"Unexpected GitHub API request: {command}")
        elif command[1:3] == ["release", "create"]:
            self.writes.append("create-draft")
            self.releases.append({"id": 123, "tag_name": command[3], "draft": "--draft" in command,
                                  "target_commitish": command[command.index("--target") + 1]})
            notes_index = command.index("--notes-file") + 1
            self.notes = Path(command[notes_index]).read_text(encoding="utf-8")
            self.created_files = command[notes_index + 1:]
            self.assets = [{"name": Path(filename).name, "state": "uploaded",
                            "digest": "sha256:" + hashlib.sha256(Path(filename).read_bytes()).hexdigest(),
                            "size": Path(filename).stat().st_size} for filename in self.created_files]
            response = ""
        elif command[1:3] == ["release", "edit"]:
            self.writes.append("publish")
            self.releases[0].update(draft=False, immutable=self.immutable)
            response = ""
        else:
            raise AssertionError(f"Unexpected GitHub command: {command}")
        return subprocess.CompletedProcess(command, 0, json.dumps(response), "")


class ReleasePublisherTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        (self.root / "release").mkdir()
        (self.root / "temporary").mkdir()
        for name in ASSETS:
            (self.root / "release" / name).write_bytes(f"Synthetic asset: {name}\n".encode())

    def execute(self, service):
        previous = Path.cwd()
        environment = {"RELEASE_VERSION": VERSION, "EXPECTED_SHA": COMMIT,
                       "GITHUB_RUN_ID": "456", "RUNNER_TEMP": str(self.root / "temporary")}
        try:
            os.chdir(self.root)
            with patch.dict(os.environ, environment, clear=True), \
                    patch("subprocess.run", side_effect=service.run), redirect_stdout(io.StringIO()) as output:
                exec(PUBLISHER, {"__name__": "offline_release_publisher"})
            return output.getvalue()
        finally:
            os.chdir(previous)

    def assert_no_replacement(self, service):
        for command, _ in service.calls:
            self.assertFalse({"delete", "--clobber", "--force"}.intersection(command), command)

    def test_success_publishes_exact_commit_and_verified_assets(self):
        service = OfflineGitHub()
        output = self.execute(service)
        self.assertEqual(service.writes, ["create-tag", "create-draft", "publish"])
        self.assertEqual(service.tag_sha, COMMIT)
        tag_payload = next(payload for command, payload in service.calls if command[2] == f"{BASE}/git/refs")
        self.assertEqual(tag_payload, {"ref": f"refs/tags/{VERSION}", "sha": COMMIT})
        create = next(command for command, _ in service.calls if command[1:3] == ["release", "create"])
        self.assertEqual(create[create.index("--target") + 1], COMMIT)
        self.assertIn("--verify-tag", create)
        self.assertIn("--draft", create)
        self.assertEqual({Path(filename).name for filename in service.created_files}, ASSETS)
        for asset in service.assets:
            content = (self.root / "release" / asset["name"]).read_bytes()
            self.assertEqual(asset["digest"], "sha256:" + hashlib.sha256(content).hexdigest())
            self.assertEqual(asset["size"], len(content))
        self.assertIn(f"Source commit: {COMMIT}", service.notes)
        self.assertIn("actions/runs/456", service.notes)
        self.assertEqual(service.releases[0], {"id": 123, "tag_name": VERSION, "draft": False,
                                              "target_commitish": COMMIT, "immutable": True})
        self.assertIn(f"Published immutable release {VERSION} from {COMMIT}", output)
        self.assertEqual(sum(command[2] == f"{BASE}/releases/123/assets?per_page=100"
                             for command, _ in service.calls), 2)
        self.assert_no_replacement(service)

    def test_existing_draft_refuses_before_any_write(self):
        service = OfflineGitHub(releases=[{"id": 123, "tag_name": VERSION, "draft": True}])
        with self.assertRaisesRegex(SystemExit, "already has a release or draft"):
            self.execute(service)
        self.assertEqual(service.writes, [])
        self.assertEqual(len(service.calls), 1)
        self.assert_no_replacement(service)

    def test_mismatched_existing_tag_refuses_before_release_creation(self):
        service = OfflineGitHub(tag_sha="b" * 40)
        with self.assertRaisesRegex(SystemExit, "does not resolve to the selected commit"):
            self.execute(service)
        self.assertEqual(service.writes, [])
        self.assertEqual(service.tag_sha, "b" * 40)
        self.assertEqual(service.releases, [])
        self.assert_no_replacement(service)

    def test_bad_remote_assets_leave_the_draft_unpublished(self):
        for corruption in ("digest", "size", "inventory"):
            with self.subTest(corruption=corruption):
                service = OfflineGitHub(corrupt=corruption)
                with self.assertRaisesRegex(SystemExit, "asset (digest or size|inventory) mismatch"):
                    self.execute(service)
                self.assertEqual(service.writes, ["create-tag", "create-draft"])
                self.assertTrue(service.releases[0]["draft"])
                self.assert_no_replacement(service)

    def test_mutable_publication_fails_without_attempting_cleanup(self):
        service = OfflineGitHub(immutable=False)
        with self.assertRaisesRegex(SystemExit, "did not produce an immutable release.*will not delete or replace"):
            self.execute(service)
        self.assertEqual(service.writes, ["create-tag", "create-draft", "publish"])
        self.assertFalse(service.releases[0]["draft"])
        self.assertFalse(service.releases[0]["immutable"])
        self.assert_no_replacement(service)


if __name__ == "__main__":
    unittest.main()
