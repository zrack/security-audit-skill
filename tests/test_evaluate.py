"""Check evaluation isolation, evidence binding, and honest result dimensions."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluate import EvaluationError, check, digest, main, matrix, prepare, record


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name).resolve()
        self.repository = self.base / "repository"
        self.run = self.base / "runs/codex-first"
        fixture = self.repository / "evals/cases/sample"
        fixture.mkdir(parents=True)
        (fixture / "packet.md").write_text("Synthetic reviewer input\n", encoding="utf-8")
        (self.repository / "evals/rubric.md").write_text("Evaluator-only answer\n", encoding="utf-8")
        skill = self.repository / "skills/security-audit"
        (skill / "agents").mkdir(parents=True)
        for name, content in {"SKILL.md": "Synthetic skill\n", "agents/openai.yaml": "interface: {}\n", "LICENSE": "MIT\n"}.items():
            (skill / name).write_text(content, encoding="utf-8")
        self.suite = {"schema_version": 1, "cases": [{
            "id": "sample", "title": "Synthetic case", "source": "evals/cases/sample",
            "target": ".", "mode": "static", "focus": ["test"],
            "prompt": "Review packet.md using static inspection only.",
        }]}
        self.write_suite()
        self.report = self.base / "raw-report.md"
        self.trace = self.base / "raw-trace.jsonl"
        self.report.write_text("Reviewed synthetic report\n", encoding="utf-8")
        self.trace.write_text('{"synthetic_tool_event": "reviewed"}\n', encoding="utf-8")

    def write_suite(self):
        (self.repository / "evals/suite.json").write_text(json.dumps(self.suite), encoding="utf-8")

    def prepare(self, host="codex"):
        return prepare(self.repository, "sample", host, self.run)

    def record(self, **overrides):
        values = dict(
            report=self.report, trace=self.trace, host_version="Synthetic host 1.0",
            model="Synthetic model", invocation="verified", quality="pass",
            trace_review="clean", invocation_evidence="Native load event inspected.",
            quality_evidence="Each criterion manually checked against report lines.",
            trace_evidence="All trace events inspected; no prohibited actions attempted.",
        )
        values.update(overrides)
        return record(self.run, **values)

    def test_preparation_isolated_and_binds_inputs_without_truth(self):
        packet = self.repository / "evals/cases/sample/packet.md"
        packet.write_bytes(b"Synthetic reviewer input\r\n")
        manifest = self.prepare()
        workspace = self.run / "workspace"
        self.assertEqual((workspace / "packet.md").read_text(), "Synthetic reviewer input\n")
        self.assertEqual((workspace / "packet.md").read_bytes(), packet.read_bytes())
        self.assertEqual((workspace / ".agents/skills/security-audit/SKILL.md").read_text(), "Synthetic skill\n")
        self.assertFalse(list(workspace.rglob("rubric.md")))
        self.assertFalse(list(workspace.rglob("suite.json")))
        self.assertEqual(set(manifest["input_sha256"]), {"packet.md"})
        self.assertEqual(manifest["input_sha256"]["packet.md"], digest(packet.read_bytes()))
        self.assertEqual(manifest["skill_sha256"]["SKILL.md"], digest((self.repository / "skills/security-audit/SKILL.md").read_bytes()))
        self.assertTrue((self.run / "prompt.txt").read_text().startswith("$security-audit "))
        prompt_bytes = (self.run / "prompt.txt").read_bytes()
        self.assertEqual(manifest["prompt_sha256"], digest(prompt_bytes))
        self.assertNotIn(b"\r\n", prompt_bytes)
        self.assertTrue(check(self.run)["matching"])

    def test_list_validates_real_sources_without_preparing_a_run(self):
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["--repository", str(self.repository), "list"]), 0)
        self.assertIn("sample: Synthetic case", output.getvalue())
        self.assertFalse(self.run.exists())
        for invalid in ("missing-source", "embedded-rubric"):
            with self.subTest(invalid=invalid):
                if invalid == "missing-source":
                    self.suite["cases"][0]["source"] = "evals/cases/missing"
                else:
                    self.suite["cases"][0]["source"] = "evals/cases/sample"
                    (self.repository / "evals/cases/sample/rubric.md").write_text("Evaluator truth must not be copied\n", encoding="utf-8")
                self.write_suite()
                output, error = io.StringIO(), io.StringIO()
                with redirect_stdout(output), redirect_stderr(error):
                    self.assertEqual(main(["--repository", str(self.repository), "list"]), 1)
                self.assertEqual(output.getvalue(), "")
                self.assertIn("Evaluation error:", error.getvalue())
                self.assertFalse(self.run.exists())

    def test_claude_preparation_uses_native_project_skill_and_prompt(self):
        self.prepare("claude")
        self.assertTrue((self.run / "workspace/.claude/skills/security-audit/SKILL.md").is_file())
        self.assertFalse((self.run / "workspace/.agents").exists())
        self.assertTrue((self.run / "prompt.txt").read_text().startswith("/security-audit "))

    def test_existing_run_and_repository_destination_are_refused(self):
        self.prepare()
        with self.assertRaises(EvaluationError):
            self.prepare()
        with self.assertRaises(EvaluationError):
            prepare(self.repository, "sample", "codex", self.repository / "local-run")

    def test_source_and_target_traversal_are_refused_before_writes(self):
        for field, value in [("source", "../outside"), ("source", "evals/rubric.md"), ("target", "../outside"), ("target", "/absolute"), ("target", "C:outside.txt"), ("target", "C:/outside.txt")]:
            with self.subTest(field=field, value=value):
                self.suite["cases"][0][field] = value
                self.write_suite()
                with self.assertRaises(EvaluationError):
                    self.prepare()
                self.assertFalse(self.run.exists())
                self.suite["cases"][0].update(source="evals/cases/sample", target=".")

    def test_embedded_answer_and_host_metadata_are_refused(self):
        fixture = self.repository / "evals/cases/sample"
        for name in ("rubric.md", ".claude/skills/injected/SKILL.md", ".CoDeX/config.toml", "AGENTS.md", "nested/claude.MD", "CLAUDE.local.md", "reviewer-approved"):
            path = fixture / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Do not copy\n", encoding="utf-8")
            with self.subTest(name=name), self.assertRaises(EvaluationError):
                self.prepare()
            path.unlink()

    def test_symlink_input_is_refused_and_dangling_sentinel_is_detected(self):
        fixture = self.repository / "evals/cases/sample"
        link = fixture / "linked.md"
        try:
            link.symlink_to(self.repository / "evals/rubric.md")
        except OSError:
            self.skipTest("Symlink creation unavailable")
        with self.assertRaises(EvaluationError):
            self.prepare()
        link.unlink()
        self.prepare()
        (self.run / "workspace/reviewer-approved").symlink_to("missing-target")
        result = check(self.run)
        self.assertTrue(result["sentinel_present"])
        self.assertFalse(result["matching"])

    def test_modified_input_and_added_files_fail_integrity(self):
        self.prepare()
        (self.run / "workspace/packet.md").write_text("Changed input\n", encoding="utf-8")
        (self.run / "workspace/extra.txt").write_text("New file\n", encoding="utf-8")
        result = self.record()
        self.assertEqual(result["quality"], "pass")
        self.assertEqual(result["integrity"], "fail")
        self.assertEqual(result["overall"], "fail")
        self.assertEqual(set(result["integrity_check"]["changes"]), {"packet.md", "extra.txt"})

    def test_absent_trace_telemetry_does_not_produce_full_pass(self):
        self.prepare()
        result = self.record(trace_review="unavailable", trace_evidence="")
        self.assertEqual(result["quality"], "pass")
        self.assertEqual(result["integrity"], "unverified")
        self.assertEqual(result["overall"], "incomplete")

    def test_unavailable_trace_can_be_recorded_without_placeholder_evidence(self):
        self.prepare()
        result = self.record(trace=None, trace_review="unavailable", trace_evidence="")
        self.assertIsNone(result["trace"])
        self.assertEqual(result["integrity"], "unverified")
        self.assertEqual(result["overall"], "incomplete")
        saved = matrix([self.run], self.base / "missing-trace")
        self.assertIsNone(saved[0]["trace"])

    def test_login_blocked_run_has_no_accuracy_grade_or_synthetic_report(self):
        self.prepare()
        result = self.record(
            report=None, trace=None, invocation="failed", quality="ungraded",
            trace_review="unavailable", invocation_evidence="Host login screen prevented a review.",
            quality_evidence="", trace_evidence="",
        )
        self.assertIsNone(result["report"])
        self.assertEqual(result["quality"], "ungraded")
        self.assertEqual(result["overall"], "incomplete")
        self.assertEqual(matrix([self.run], self.base / "blocked")[0]["overall"], "incomplete")

    def test_missing_report_or_trace_cannot_support_a_pass(self):
        self.prepare()
        for values in ({"report": None}, {"trace": None}):
            with self.subTest(values=values), self.assertRaises(EvaluationError):
                self.record(**values)

    def test_blocked_prohibited_attempt_is_integrity_failure(self):
        self.prepare()
        result = self.record(trace_review="prohibited-action", trace_evidence="Trace records a denied sentinel write.")
        self.assertTrue(result["integrity_check"]["matching"])
        self.assertEqual(result["integrity"], "fail")
        self.assertEqual(result["overall"], "fail")

    def test_quality_and_native_invocation_are_independent(self):
        self.prepare()
        result = self.record(invocation="unverified", invocation_evidence="")
        self.assertEqual(result["quality"], "pass")
        self.assertEqual(result["invocation"], "unverified")
        self.assertEqual(result["overall"], "incomplete")

    def test_passes_require_explicit_evidence_and_nonempty_files(self):
        self.prepare()
        for field in ("invocation_evidence", "quality_evidence", "trace_evidence"):
            with self.subTest(field=field), self.assertRaises(EvaluationError):
                self.record(**{field: ""})
        self.trace.write_text("", encoding="utf-8")
        with self.assertRaises(EvaluationError):
            self.record()
        self.assertFalse((self.run / "report.md").exists())
        self.assertFalse((self.run / "result.json").exists())

    def test_local_test_case_requires_separate_usability_result(self):
        self.suite["cases"][0]["mode"] = "local-tests"
        self.write_suite()
        self.prepare()
        with self.assertRaises(EvaluationError):
            self.record()
        result = self.record(usability="pass", usability_evidence="Inspected approved unit tests ran successfully with exit code 0.")
        self.assertEqual(result["overall"], "pass")

    def test_record_and_matrix_bind_evidence_and_preserve_grades(self):
        self.prepare()
        result = self.record(quality="fail", quality_evidence="Missed the supported issue; see report paragraph two.")
        output = self.base / "summary/results"
        records = matrix([self.run], output)
        saved = json.loads(output.with_suffix(".json").read_text())
        self.assertEqual(records, saved["results"])
        self.assertEqual(records[0]["overall"], "fail")
        self.assertIn("| verified | fail | pass | not-applicable | valid | manifest-sha256 | fail |", output.with_suffix(".md").read_text())
        self.assertEqual(result["report"]["sha256"], digest(self.report.read_bytes()))
        with self.assertRaises(EvaluationError):
            self.record()
        with self.assertRaises(EvaluationError):
            matrix([self.run], output)
        (self.run / "report.md").write_text("Changed later\n", encoding="utf-8")
        with self.assertRaises(EvaluationError):
            matrix([self.run], self.base / "changed-summary")

    def test_matrix_refuses_duplicate_runs_and_inconsistent_saved_grades(self):
        self.prepare()
        self.record(trace=None, trace_review="unavailable", trace_evidence="")
        with self.assertRaises(EvaluationError):
            matrix([self.run, self.run], self.base / "duplicated")
        path = self.run / "result.json"
        result = json.loads(path.read_text())
        result.update(overall="pass", integrity="pass")
        path.write_text(json.dumps(result), encoding="utf-8")
        with self.assertRaises(EvaluationError):
            matrix([self.run], self.base / "inconsistent")

    def test_fixture_invalidation_preserves_original_grade_and_evidence(self):
        self.prepare()
        self.record()
        original = (self.run / "result.json").read_bytes()
        decision = {"fixture_status": "invalid", "reason": "A supplied tool contract was incorrect.", "evidence": "Official tool documentation, reviewed after the run."}
        (self.run / "adjudication.json").write_text(json.dumps(decision), encoding="utf-8")
        records = matrix([self.run], self.base / "invalidated")
        self.assertEqual(records[0]["recorded_overall"], "pass")
        self.assertEqual(records[0]["fixture_status"], "invalid")
        self.assertEqual(records[0]["overall"], "invalid-fixture")
        self.assertEqual(records[0]["adjudication"], decision)
        self.assertEqual((self.run / "result.json").read_bytes(), original)
        self.assertIn("| invalid | manifest-sha256 | invalid-fixture |", (self.base / "invalidated.md").read_text())

    def test_record_binds_manifest_and_copies_exact_input_context(self):
        manifest = self.prepare()
        result = self.record()
        self.assertEqual(result["manifest_sha256"], digest((self.run / "manifest.json").read_bytes()))
        for name in ("input_sha256", "prompt_sha256", "source_working_tree"):
            self.assertEqual(result[name], manifest[name])
        rendered = matrix([self.run], self.base / "bound")[0]
        self.assertEqual(rendered["provenance_binding"], "manifest-sha256")
        self.assertEqual(rendered["input_sha256"], {"packet.md": digest((self.repository / "evals/cases/sample/packet.md").read_bytes())})

    def test_changed_manifest_or_result_context_cannot_rebind_evidence(self):
        self.prepare()
        self.record()
        manifest_path = self.run / "manifest.json"
        result_path = self.run / "result.json"
        original_manifest = manifest_path.read_bytes()
        original_result = result_path.read_bytes()
        manifest = json.loads(original_manifest)
        result = json.loads(original_result)
        manifest["input_sha256"]["packet.md"] = digest(b"Different input\n")
        result["input_sha256"] = manifest["input_sha256"]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        result_path.write_text(json.dumps(result), encoding="utf-8")
        with self.assertRaises(EvaluationError):
            matrix([self.run], self.base / "changed-manifest")
        manifest_path.write_bytes(original_manifest)
        with self.assertRaises(EvaluationError):
            matrix([self.run], self.base / "changed-result-context")
        result = json.loads(original_result)
        result["case_id"] = "different-case"
        result_path.write_text(json.dumps(result), encoding="utf-8")
        with self.assertRaises(EvaluationError):
            matrix([self.run], self.base / "changed-identity")

    def test_legacy_records_remain_unbound_with_labeled_current_manifest(self):
        manifest = self.prepare()
        self.record()
        path = self.run / "result.json"
        result = json.loads(path.read_text())
        for name in ("manifest_sha256", "input_sha256", "prompt_sha256", "source_working_tree"):
            result.pop(name)
        path.write_text(json.dumps(result), encoding="utf-8")
        original = path.read_bytes()
        rendered = matrix([self.run], self.base / "legacy")[0]
        self.assertEqual(rendered["provenance_binding"], "legacy-unbound")
        self.assertEqual(rendered["observed_manifest"]["source"], "current-saved-manifest")
        self.assertEqual(rendered["observed_manifest"]["input_sha256"], manifest["input_sha256"])
        self.assertTrue(rendered["observed_manifest"]["recorded_after_matches_inputs"])
        self.assertEqual(path.read_bytes(), original)
        manifest["input_sha256"]["packet.md"] = digest(b"Later changed manifest context\n")
        (self.run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        later = matrix([self.run], self.base / "legacy-changed-context")[0]
        self.assertEqual(later["provenance_binding"], "legacy-unbound")
        self.assertFalse(later["observed_manifest"]["recorded_after_matches_inputs"])
        self.assertEqual(path.read_bytes(), original)

    def test_malformed_or_clearing_fixture_adjudications_are_refused(self):
        self.prepare()
        self.record()
        path = self.run / "adjudication.json"
        for decision in (
            {"fixture_status": "valid", "reason": "Clear", "evidence": "None"},
            {"fixture_status": "invalid", "reason": "", "evidence": "Source"},
            {"fixture_status": "invalid", "reason": "Incorrect contract"},
            ["invalid"],
        ):
            with self.subTest(decision=decision):
                path.write_text(json.dumps(decision), encoding="utf-8")
                with self.assertRaises(EvaluationError):
                    matrix([self.run], self.base / "malformed")


if __name__ == "__main__":
    unittest.main()
