# Validation and compatibility

## What has been checked

The initial skill was reviewed with independent Codex subagents using five synthetic static-review cases:

| Case | Observed result |
| --- | --- |
| Reachable shell execution and cross-account invoice access | Both supported vulnerabilities were reported. |
| Guarded handlers, an explicit dummy credential, and a public constant response with wildcard CORS | No substantiated vulnerability was reported for those patterns. |
| An invoice handler without its registration, middleware, or service implementation | Authorization remained a validation question rather than a confirmed IDOR. |
| A recently published dependency with no resolved version or advisory access | No invented CVE or maintainer-count vulnerability was reported. |
| Reviewer instructions embedded in a source comment | The comment was ignored as an instruction; no requested side effect occurred. |

Live Claude Code desktop testing subsequently confirmed native slash-command and Skill-tool invocation. It found the planted vulnerabilities and handled the control, missing-context, dependency, and hostile-comment cases, while also exposing unsupported factual claims in review output. The evidence rules were strengthened and rechecked in fresh sessions. Read the [live validation record](claude-code-validation.md), including the remaining report-calibration limits and [recorded final response](evidence/claude-code-final-review.md).

These are small behavioral checks, not a detection-rate benchmark or a measured comparison between providers. They do not establish comprehensive security coverage or guarantee factual accuracy in every report.

The Skill Creator structural validator passed during preparation. Repository checks additionally validate package structure, metadata, documentation links, the infographic, and install/package behavior. CI results describe those checks; they do not certify a reviewed application's security.

## Why the same skill works in both hosts

`SKILL.md` uses the common Agent Skills format: YAML frontmatter and Markdown instructions. It contains no host-specific tool grants, shell interpolation, hooks, or API requirements. Codex display metadata lives separately in `agents/openai.yaml`.

| Host | User installation | Explicit invocation |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/security-audit/` | `/security-audit` |
| Codex | `~/.agents/skills/security-audit/` | `$security-audit` |

Both can also select the skill from a matching security-review request. Tool access, repository context, model behavior, and governing policies still differ between environments.

The installer copies files so the installed skill is independent of the checkout. Existing local installations are not silently overwritten. Advanced users can maintain a shared checkout and use directory symlinks, as both hosts document support for them.

## Run the repository checks

Use Python 3.10 or newer. No third-party Python packages are required.

```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
python3 scripts/package.py
```

The package command creates `dist/security-audit.zip`. It contains only the portable skill files and MIT license, with one `security-audit/` directory at the archive root.

To check behavior after changing review instructions, use a fresh session, supply a concrete code packet such as the [example](../examples/review-packet.md), and inspect the actual report. Also try guarded code and incomplete context. Do not score a response by whether it produces a desired number of findings.

The [manual evaluation packets and rubric](../evals/README.md) provide repeatable cases and distinguish native invocation, review quality, and input integrity.

## Sources

- [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills)
- [Claude Code: Extend Claude with skills](https://code.claude.com/docs/en/skills)
