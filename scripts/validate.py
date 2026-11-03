#!/usr/bin/env python3
"""Check the repository's portable package and documentation without dependencies."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET


class ValidationError(ValueError):
    """A repository invariant is not satisfied."""


def scalar_fields(lines: list[str]) -> dict[str, str]:
    """Read the small single-line string subset used by this package's YAML.

    This deliberately does not implement a general YAML parser. Keep package
    metadata to plain or JSON-quoted, single-line string values.
    """
    result: dict[str, str] = {}
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"([a-z_]+): (.+)", line)
        if not match:
            raise ValidationError(f"Use single-line string metadata: {line!r}")
        key, value = match.groups()
        if key in result:
            raise ValidationError(f"Duplicate metadata key: {key}")
        if value.startswith('"'):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as error:
                raise ValidationError(f"Invalid quoted metadata: {key}") from error
        elif (
            value[0] in "'[{&*!|>"
            or re.search(r":\s|\s#", value)
            or value.lower() in {"true", "false", "null", "~"}
        ):
            raise ValidationError(f"Quote this metadata value with double quotes: {key}")
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"Empty or non-string metadata: {key}")
        result[key] = value
    return result


def validate(repository: Path) -> list[str]:
    root = repository.resolve()
    skill = root / "skills/security-audit"
    required = [
        "README.md", "LICENSE", "CONTRIBUTING.md", "SECURITY.md",
        "skills/security-audit/SKILL.md", "skills/security-audit/LICENSE",
        "skills/security-audit/agents/openai.yaml",
        "assets/security-audit-workflow.svg", "docs/validation.md",
        "examples/review-packet.md", "examples/review-report.md",
        "scripts/install.py", "scripts/package.py", ".github/workflows/validate.yml",
    ]
    for relative in required:
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise ValidationError(f"Missing regular repository file: {relative}")

    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise ValidationError("SKILL.md must start with unfenced YAML frontmatter")
    fields = scalar_fields(match.group(1).splitlines())
    if set(fields) != {"name", "description", "license"}:
        raise ValidationError("Portable frontmatter must contain name, description, and license")
    if fields["name"] != skill.name or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fields["name"]):
        raise ValidationError("Skill name must match its folder and use lowercase hyphenated words")
    if len(fields["name"]) > 64 or len(fields["description"]) > 1024:
        raise ValidationError("Skill name or description exceeds Agent Skills limits")
    if fields["license"] != "MIT":
        raise ValidationError("Skill license must match the repository's MIT license")
    if (skill / "LICENSE").read_bytes() != (root / "LICENSE").read_bytes():
        raise ValidationError("Portable LICENSE differs from the root LICENSE")
    if "Copyright (c) 2026 Scott Zeitner" not in (root / "LICENSE").read_text(encoding="utf-8"):
        raise ValidationError("Root LICENSE is missing the copyright notice")
    if re.search(r"!`|\$ARGUMENTS|\$\{CLAUDE_", text):
        raise ValidationError("The portable skill contains host-specific command interpolation")

    metadata = (skill / "agents/openai.yaml").read_text(encoding="utf-8").splitlines()
    if not metadata or metadata[0] != "interface:" or any(
        line and not line.startswith("  ") for line in metadata[1:]
    ):
        raise ValidationError("Codex metadata must contain only its interface mapping")
    interface = scalar_fields([line[2:] for line in metadata[1:]])
    if set(interface) != {"display_name", "short_description", "default_prompt"}:
        raise ValidationError("Codex interface fields are incomplete or unsupported")
    if not 25 <= len(interface["short_description"]) <= 64:
        raise ValidationError("Codex short_description must contain 25–64 characters")
    if "$security-audit" not in interface["default_prompt"]:
        raise ValidationError("Codex default_prompt must mention $security-audit")

    image = ET.parse(root / "assets/security-audit-workflow.svg").getroot()
    ns = "{http://www.w3.org/2000/svg}"
    if image.tag != ns + "svg" or not image.get("viewBox"):
        raise ValidationError("Infographic must be a scalable SVG")
    if image.find(ns + "title") is None or image.find(ns + "desc") is None:
        raise ValidationError("Infographic needs an accessible title and description")
    if any(element.tag in {ns + "script", ns + "foreignObject"} for element in image.iter()):
        raise ValidationError("Infographic must be static and self-contained")
    for element in image.iter():
        for attribute, value in element.attrib.items():
            if attribute.lower().startswith("on"):
                raise ValidationError("Infographic must not contain event handlers")
            if attribute.rsplit("}", 1)[-1] == "href" and not value.startswith("#"):
                raise ValidationError("Infographic must not load external resources")

    docs = [path for path in root.rglob("*.md") if not {".git", "dist"}.intersection(path.relative_to(root).parts)]
    for path in docs:
        content = path.read_text(encoding="utf-8")
        if re.search(r"/Users/[^/\s]+/|[A-Z]:\\Users\\", content):
            raise ValidationError(f"Local user path in public documentation: {path.relative_to(root)}")
        for target in re.findall(r"!?\[[^\]]*\]\(([^)\s]+)\)", content):
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            destination = (path.parent / unquote(parsed.path)).resolve()
            if not destination.is_relative_to(root) or not destination.exists():
                raise ValidationError(f"Broken local link in {path.relative_to(root)}: {target}")

    return [
        "Portable skill metadata and license",
        "Codex display metadata",
        "Static, accessible SVG infographic",
        f"Local links in {len(docs)} Markdown files",
    ]


def main() -> int:
    try:
        checks = validate(Path(__file__).resolve().parents[1])
    except (OSError, ValidationError, ET.ParseError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        return 1
    for check in checks:
        print(f"OK: {check}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
