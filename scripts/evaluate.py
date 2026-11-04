#!/usr/bin/env python3
"""Prepare isolated native-host evaluations and record explicit human grades.

This tool does not call a provider, alter host permissions, or infer review
quality from response text. Keep reports and traces private until redacted.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
import subprocess
import sys
from typing import Any


HOSTS = {"claude": ".claude", "codex": ".agents"}
PORTABLE = ("SKILL.md", "agents/openai.yaml", "LICENSE")
STATES = {
    "invocation": {"verified", "unverified", "failed"},
    "quality": {"pass", "fail", "ungraded"},
    "usability": {"pass", "fail", "not-applicable", "ungraded"},
    "trace_review": {"clean", "prohibited-action", "unavailable"},
}


class EvaluationError(ValueError):
    """An evaluation input or evidence record is incomplete or unsafe."""


def digest(content: bytes) -> str:
    return sha256(content).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8") as output:
        json.dump(value, output, indent=2, sort_keys=True)
        output.write("\n")


def _relative(value: str, *, dot: bool = False) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise EvaluationError("Use a nonempty relative POSIX path")
    path = Path(value)
    if path.is_absolute() or PureWindowsPath(value).drive or ".." in path.parts or (path == Path(".") and not dot):
        raise EvaluationError(f"Unsafe relative path: {value}")
    return path


def load_suite(repository: Path) -> dict[str, Any]:
    repository = repository.expanduser().resolve()
    suite = json.loads((repository / "evals/suite.json").read_text(encoding="utf-8"))
    if suite.get("schema_version") != 1 or not isinstance(suite.get("cases"), list):
        raise EvaluationError("Unsupported evaluation suite schema")
    seen = set()
    for case in suite["cases"]:
        case_id = case.get("id", "")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", case_id) or case_id in seen:
            raise EvaluationError("Case IDs must be unique lowercase hyphenated names")
        seen.add(case_id)
        source = _relative(case["source"])
        if source.parts[:2] not in {("evals", "cases"), ("evals", "packets")}:
            raise EvaluationError("Reviewer inputs must come from evals/cases or evals/packets")
        _relative(case["target"], dot=True)
        if case.get("mode") not in {"static", "local-tests"}:
            raise EvaluationError(f"Unsupported case mode: {case_id}")
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            raise EvaluationError(f"Missing reviewer prompt: {case_id}")
        # Listing is also the read-only CI check of the real fixture inventory.
        # Validate every case before returning, without preparing a run or host.
        _input_files(repository, case)
    return suite


def snapshot(workspace: Path) -> dict[str, dict[str, str]]:
    """Hash all entries without following symlinks, including dangling links."""
    entries: dict[str, dict[str, str]] = {}

    def walk(directory: Path) -> None:
        for path in sorted(directory.iterdir()):
            name = path.relative_to(workspace).as_posix()
            if path.is_symlink():
                entries[name] = {"kind": "symlink", "target": os.readlink(path)}
            elif path.is_dir():
                entries[name] = {"kind": "directory"}
                walk(path)
            elif path.is_file():
                entries[name] = {"kind": "file", "sha256": digest(path.read_bytes())}
            else:
                entries[name] = {"kind": "special"}

    walk(workspace)
    return entries


def _input_files(repository: Path, case: dict[str, Any]) -> dict[Path, bytes]:
    source = repository / _relative(case["source"])
    if not source.resolve().is_relative_to(repository) or source.is_symlink():
        raise EvaluationError("Input source escapes the repository or is a symlink")
    # Reject intermediate links too: input provenance should identify real files.
    if any(parent.is_symlink() for parent in source.parents if parent != repository and parent.is_relative_to(repository)):
        raise EvaluationError("Input source has a symlink parent")
    target = _relative(case["target"], dot=True)
    if source.is_file():
        paths = [(source, target)]
    elif source.is_dir():
        paths = [(path, target / path.relative_to(source)) for path in source.rglob("*")]
    else:
        raise EvaluationError("Input source is missing")
    result = {}
    for path, relative in paths:
        if path.is_symlink():
            raise EvaluationError("Fixture inputs must not contain symlinks")
        if path.is_dir():
            continue
        if not path.is_file() or relative == Path("."):
            raise EvaluationError("Fixtures must contain regular files with file targets")
        if any(part.lower() in {".claude", ".agents", ".codex", ".git", "reviewer-approved"} for part in relative.parts):
            raise EvaluationError("Fixture collides with host metadata or the sentinel")
        if relative.name.lower() in {"agents.md", "claude.md", "claude.local.md"}:
            raise EvaluationError("Host instructions must be inert review text, not active instruction files")
        if relative.name.lower() in {"rubric.md", "suite.json", "results.json", "matrix.md"}:
            raise EvaluationError("Evaluator-only files must not be copied to reviewer inputs")
        result[relative] = path.read_bytes()
    if not result:
        raise EvaluationError("Fixture contains no input files")
    return result


def _git(repository: Path, *args: str) -> str:
    try:
        result = subprocess.run(["git", "-C", str(repository), *args], capture_output=True, text=True, check=False)
    except OSError:
        return "unavailable"
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def prepare(repository: Path, case_id: str, host: str, run: Path) -> dict[str, Any]:
    """Create a fresh run/workspace, with operator material beside it."""
    repository = repository.expanduser().resolve()
    run = run.expanduser().resolve()
    if host not in HOSTS:
        raise EvaluationError("Host must be claude or codex")
    if run.is_relative_to(repository):
        raise EvaluationError("Evaluation runs must be outside the source repository")
    if os.path.lexists(run):
        raise EvaluationError("Run destination already exists; use a fresh directory")
    suite = load_suite(repository)
    matches = [case for case in suite["cases"] if case["id"] == case_id]
    if not matches:
        raise EvaluationError(f"Unknown case: {case_id}")
    case = matches[0]
    inputs = _input_files(repository, case)
    skill = {}
    for name in PORTABLE:
        path = repository / "skills/security-audit" / name
        if path.is_symlink() or not path.is_file():
            raise EvaluationError(f"Missing regular portable skill file: {name}")
        skill[name] = path.read_bytes()
    run.mkdir(parents=True, exist_ok=False)
    workspace = run / "workspace"
    workspace.mkdir()
    for relative, content in inputs.items():
        destination = workspace / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    skill_root = workspace / HOSTS[host] / "skills/security-audit"
    for name, content in skill.items():
        destination = skill_root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    prefix = "/security-audit" if host == "claude" else "$security-audit"
    prompt = prefix + " " + case["prompt"].strip() + "\n"
    (run / "prompt.txt").write_text(prompt, encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "run_id": run.name,
        "case_id": case_id,
        "case_title": case["title"],
        "mode": case["mode"],
        "host": host,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": _git(repository, "rev-parse", "HEAD"),
        "source_working_tree": _git(repository, "status", "--porcelain"),
        "suite_sha256": digest((repository / "evals/suite.json").read_bytes()),
        "prompt_sha256": digest(prompt.encode()),
        "input_sha256": {path.as_posix(): digest(content) for path, content in inputs.items()},
        "skill_sha256": {name: digest(content) for name, content in skill.items()},
        "before": snapshot(workspace),
    }
    _write_json(run / "manifest.json", manifest)
    return manifest


def check(run: Path) -> dict[str, Any]:
    manifest_path = run / "manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise EvaluationError("Run manifest must be a regular JSON file")
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    before = manifest["before"]
    after = snapshot(run / "workspace")
    changes = {
        name: {"before": before.get(name), "after": after.get(name)}
        for name in sorted(before.keys() | after.keys())
        if before.get(name) != after.get(name)
    }
    sentinel = os.path.lexists(run / "workspace/reviewer-approved")
    return {"matching": not changes and not sentinel, "sentinel_present": sentinel, "changes": changes, "after": after}


def _evidence(source: Path, run: Path, name: str, *, copy: bool = True) -> dict[str, str]:
    source = source.expanduser().resolve()
    if source.is_relative_to((run / "workspace").resolve()) or not source.is_file():
        raise EvaluationError("Reports and traces must be regular files outside the review workspace")
    content = source.read_bytes()
    if not content.strip():
        raise EvaluationError("Evidence file is empty")
    destination = run / name
    if source != destination.resolve():
        if os.path.lexists(destination):
            raise EvaluationError("Evidence destination already exists")
        if copy:
            shutil.copyfile(source, destination)
    return {"path": name, "sha256": digest(content)}


def _overall(invocation: str, quality: str, integrity: str, usability: str) -> str:
    if "fail" in {quality, integrity, usability}:
        return "fail"
    # A failed login or interrupted run without an assessed report is incomplete,
    # not a review-quality failure or a completed behavioral observation.
    if quality == "ungraded":
        return "incomplete"
    if invocation == "failed":
        return "fail"
    if invocation == "verified" and quality == "pass" and integrity == "pass" and usability in {"pass", "not-applicable"}:
        return "pass"
    return "incomplete"


def record(
    run: Path, *, report: Path | None = None, trace: Path | None = None, host_version: str, model: str,
    invocation: str, quality: str, trace_review: str,
    usability: str = "not-applicable", invocation_evidence: str = "",
    quality_evidence: str = "", trace_evidence: str = "", usability_evidence: str = "",
    notes: str = "",
) -> dict[str, Any]:
    """Save explicit operator grades; integrity also needs a reviewed trace.

    A clean filesystem does not prove a prohibited action was never attempted.
    Invocation and review quality are independent, never inferred from wording.
    """
    run = run.resolve()
    if (run / "result.json").exists():
        raise EvaluationError("Result already recorded; use a fresh run for a recheck")
    values = {"invocation": invocation, "quality": quality, "trace_review": trace_review, "usability": usability}
    for name, value in values.items():
        if value not in STATES[name]:
            raise EvaluationError(f"Invalid {name} state: {value}")
    if not host_version.strip() or not model.strip():
        raise EvaluationError("Record the observed host version and model (or explicitly unknown)")
    for state, evidence, label in [
        (invocation in {"verified", "failed"}, invocation_evidence, "invocation"),
        (quality in {"pass", "fail"}, quality_evidence, "quality"),
        (trace_review != "unavailable", trace_evidence, "trace review"),
        (usability in {"pass", "fail"}, usability_evidence, "usability"),
    ]:
        if state and not evidence.strip():
            raise EvaluationError(f"An explicit evidence note is required for {label}")
    manifest_path = run / "manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise EvaluationError("Run manifest must be a regular JSON file")
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest["mode"] == "local-tests" and usability == "not-applicable":
        raise EvaluationError("Local-tests cases need a usability grade or ungraded")
    if report is None and quality != "ungraded":
        raise EvaluationError("A graded review needs a nonempty report; otherwise use ungraded")
    if trace is None and trace_review != "unavailable":
        raise EvaluationError("A reviewed trace needs a nonempty evidence file; otherwise use unavailable")
    integrity_check = check(run)
    integrity = "fail" if not integrity_check["matching"] or trace_review == "prohibited-action" else (
        "pass" if trace_review == "clean" else "unverified"
    )
    result = {
        "schema_version": 1,
        "run_id": manifest["run_id"], "case_id": manifest["case_id"], "host": manifest["host"],
        "source_revision": manifest["source_revision"], "suite_sha256": manifest["suite_sha256"],
        "skill_sha256": manifest["skill_sha256"]["SKILL.md"],
        "manifest_sha256": digest(manifest_bytes),
        "input_sha256": manifest.get("input_sha256"),
        "prompt_sha256": manifest.get("prompt_sha256"),
        "source_working_tree": manifest.get("source_working_tree"),
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "host_version": host_version, "model": model,
        "invocation": invocation, "quality": quality, "integrity": integrity, "usability": usability,
        "overall": _overall(invocation, quality, integrity, usability),
        "invocation_evidence": invocation_evidence, "quality_evidence": quality_evidence,
        "trace_review": trace_review, "trace_evidence": trace_evidence,
        "usability_evidence": usability_evidence, "notes": notes,
        "integrity_check": integrity_check,
    }
    # Validate both before copying either, so a missing trace is easy to repair.
    for name, source, destination in (("report", report, "report.md"), ("trace", trace, "trace.jsonl")):
        if source is not None:
            _evidence(source, run, destination, copy=False)
    for name, source, destination in (("report", report, "report.md"), ("trace", trace, "trace.jsonl")):
        result[name] = _evidence(source, run, destination) if source is not None else None
    _write_json(run / "result.json", result)
    return result


def matrix(runs: list[Path], output: Path) -> list[dict[str, Any]]:
    """Render saved grades with bound evidence; do not collapse failed runs."""
    if any(os.path.lexists(output.with_suffix(suffix)) for suffix in (".json", ".md")):
        raise EvaluationError("Matrix output exists; choose a new output prefix")
    results = []
    seen = set()
    for run in runs:
        result = json.loads((run / "result.json").read_text(encoding="utf-8"))
        manifest_path = run / "manifest.json"
        if manifest_path.is_symlink() or not manifest_path.is_file():
            raise EvaluationError("Run manifest must be a regular JSON file")
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes)
        for name in ("run_id", "case_id", "host", "source_revision", "suite_sha256"):
            if result[name] != manifest[name]:
                raise EvaluationError(f"Saved {name} differs from run manifest")
        if result["skill_sha256"] != manifest["skill_sha256"]["SKILL.md"]:
            raise EvaluationError("Saved skill digest differs from run manifest")
        bound_manifest = "manifest_sha256" in result
        if bound_manifest:
            if result["manifest_sha256"] != digest(manifest_bytes):
                raise EvaluationError("Changed run manifest; recorded provenance no longer matches")
            for name in ("input_sha256", "prompt_sha256", "source_working_tree"):
                if result.get(name) != manifest.get(name):
                    raise EvaluationError(f"Saved {name} differs from bound run manifest")
        identity = (result["run_id"], result["host"], result["case_id"])
        if identity in seen:
            raise EvaluationError("A run cannot appear twice in the results matrix")
        seen.add(identity)
        for name in ("invocation", "quality", "usability", "trace_review"):
            if result[name] not in STATES[name]:
                raise EvaluationError(f"Invalid saved {name} grade")
        integrity = "fail" if not result["integrity_check"]["matching"] or result["trace_review"] == "prohibited-action" else (
            "pass" if result["trace_review"] == "clean" else "unverified"
        )
        if result["integrity"] != integrity or result["overall"] != _overall(result["invocation"], result["quality"], integrity, result["usability"]):
            raise EvaluationError("Saved grades are inconsistent with integrity/telemetry evidence")
        for name in ("report", "trace"):
            evidence = result[name]
            if evidence is None:
                expected = result["quality"] == "ungraded" if name == "report" else result["trace_review"] == "unavailable"
                if not expected:
                    raise EvaluationError(f"Missing {name} evidence for a saved grade")
                continue
            path = run / _relative(evidence["path"])
            if not path.is_file() or digest(path.read_bytes()) != evidence["sha256"]:
                raise EvaluationError(f"Changed or missing {name} evidence in {run.name}")
        # Preserve the original grade when later fixture research invalidates it.
        # This overlay cannot overwrite evidence or clear a prior invalidation.
        rendered = dict(
            result, recorded_overall=result["overall"], fixture_status="valid",
            provenance_binding="manifest-sha256" if bound_manifest else "legacy-unbound",
        )
        if not bound_manifest:
            # Older records were not bound to the manifest when graded. Expose
            # current context for inspection without silently upgrading them.
            inputs = manifest.get("input_sha256")
            after = result["integrity_check"].get("after", {})
            rendered["observed_manifest"] = {
                "source": "current-saved-manifest",
                "sha256": digest(manifest_bytes),
                "input_sha256": inputs,
                "prompt_sha256": manifest.get("prompt_sha256"),
                "source_working_tree": manifest.get("source_working_tree"),
                "recorded_after_matches_inputs": (
                    all(after.get(name) == {"kind": "file", "sha256": value} for name, value in inputs.items())
                    if isinstance(inputs, dict) else None
                ),
            }
        adjudication = run / "adjudication.json"
        if os.path.lexists(adjudication):
            if adjudication.is_symlink() or not adjudication.is_file():
                raise EvaluationError("Fixture adjudication must be a regular JSON file")
            decision = json.loads(adjudication.read_text(encoding="utf-8"))
            if (
                not isinstance(decision, dict)
                or set(decision) != {"fixture_status", "reason", "evidence"}
                or decision["fixture_status"] != "invalid"
                or any(not isinstance(decision[name], str) or not decision[name].strip() for name in ("reason", "evidence"))
            ):
                raise EvaluationError("Fixture adjudication must invalidate with a reason and evidence")
            rendered.update(fixture_status="invalid", overall="invalid-fixture", adjudication=decision)
        results.append(rendered)
    results.sort(key=lambda item: (item["case_id"], item["host"], item["run_id"]))
    lines = [
        "# Native-host evaluation results", "",
        "Operator-reviewed observations for these inputs, versions, and settings. No detection-rate or host-parity claim.", "",
        "| Run | Host | Case | Invocation | Quality | Integrity | Usability | Fixture | Provenance | Overall |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in results:
        values = [item[key] for key in ("run_id", "host", "case_id", "invocation", "quality", "integrity", "usability", "fixture_status", "provenance_binding", "overall")]
        lines.append("| " + " | ".join(str(value).replace("|", "\\|").replace("\n", " ") for value in values) + " |")
    output.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output.with_suffix(".json"), {"schema_version": 1, "results": results})
    with output.with_suffix(".md").open("x", encoding="utf-8") as destination:
        destination.write("\n".join(lines) + "\n")
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[1])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="list case IDs and titles")
    prepare_parser = commands.add_parser("prepare", help="create an isolated workspace and operator manifest")
    prepare_parser.add_argument("case")
    prepare_parser.add_argument("--host", choices=HOSTS, required=True)
    prepare_parser.add_argument("--run", type=Path, required=True)
    check_parser = commands.add_parser("check", help="compare current workspace with its before snapshot")
    check_parser.add_argument("run", type=Path)
    record_parser = commands.add_parser("record", help="save explicit evidence-based operator grades")
    record_parser.add_argument("run", type=Path)
    for name in ("report", "trace"):
        record_parser.add_argument("--" + name, type=Path, help="omit only for an ungraded report or unavailable trace")
    for name in ("host-version", "model"):
        record_parser.add_argument("--" + name, required=True)
    for name, choices in STATES.items():
        record_parser.add_argument("--" + name.replace("_", "-"), choices=sorted(choices), required=name != "usability", default="not-applicable" if name == "usability" else None)
    for name in ("invocation-evidence", "quality-evidence", "trace-evidence", "usability-evidence", "notes"):
        record_parser.add_argument("--" + name, default="")
    matrix_parser = commands.add_parser("matrix", help="render all supplied recorded runs, including failures")
    matrix_parser.add_argument("runs", type=Path, nargs="+")
    matrix_parser.add_argument("--output", type=Path, required=True, help="new output prefix for .md and .json")
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            for case in load_suite(args.repository)["cases"]:
                print(f"{case['id']}: {case['title']}")
        elif args.command == "prepare":
            print(json.dumps(prepare(args.repository, args.case, args.host, args.run), indent=2))
        elif args.command == "check":
            result = check(args.run)
            print(json.dumps(result, indent=2))
            return 0 if result["matching"] else 1
        elif args.command == "record":
            values = vars(args).copy()
            for name in ("command", "repository", "run"):
                values.pop(name)
            print(json.dumps(record(args.run, **values), indent=2))
        else:
            print(f"Recorded {len(matrix(args.runs, args.output))} runs")
    except (OSError, ValueError, KeyError) as error:
        print(f"Evaluation error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
