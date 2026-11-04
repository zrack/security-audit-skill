# Validation and compatibility

## Shared native-host evaluation

The November 3, 2026 [shared results matrix](../evals/results/2026-11-03/README.md) records six cases in fresh native sessions for each host, baseline and revised instructions, and two additional Codex baseline repeats. It preserves report-quality failures and excludes two observations whose original CI fixture was incorrect. The [suite and procedure](../evals/README.md) separate invocation, detection, false positives, factual calibration, input integrity, and ordinary tool use.

| Final candidate observation | Claude desktop Code mode | Codex CLI |
| --- | --- | --- |
| Report-quality cases passed | 4 of 6 | 6 of 6 |
| Supported vulnerability root causes found | All 7 in the supplied suite | All 7 in the supplied suite |
| Confirmed vulnerability false positives | None observed | None observed |
| Native invocation and input integrity | Verified for all 6 cases | Verified for all 6 cases |
| Authorized local tests | 2 passed, after Manual Allow once | 2 passed, workspace-write/on-request |

Claude still made unsupported claims about unseen return behavior and upload/restart limits. Those failures remain unresolved in the final candidate; correct vulnerability detection does not establish a factually accurate report. Targeted changes corrected CORS reasoning and improved impact calibration without adding tool restrictions, host configuration changes, dependencies, or mandatory setup.

These results describe development skill digest `1859a7fe51fb93937524262b1b18b3df2d4dd31305094479cd8d4345c9056d15`, not the published v0.2.1 package. Exact inputs, source working-tree context, host surfaces, settings, redacted reports, and evidence digests are in the matrix. Existing host customizations remained present, so this is an observation of configured hosts rather than a controlled comparison of the skill alone. Advisory/network usability was not tested.

Repository validation, 69 tooling tests, real-suite fixture validation, and the three-file portable package check passed locally. CI also validates the actual case manifest and fixture paths without calling a host or provider. The optional Skill Creator validator could not be rerun because its PyYAML dependency was unavailable; no dependency was added. The repository's independent metadata and documentation validator passed.

## Earlier checks

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

The [shared evaluation suite and rubric](../evals/README.md) provide repeatable cases and distinguish native invocation, review quality, input integrity, and normal-use behavior. Evaluation tooling is optional and is excluded from the portable skill package.

## Sources

- [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills)
- [Claude Code: Extend Claude with skills](https://code.claude.com/docs/en/skills)
