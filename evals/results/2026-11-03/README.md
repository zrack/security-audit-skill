# Shared native-host evaluation results

Date: November 3, 2026.

These are bounded synthetic regression runs of the installed Security Audit skill in Claude desktop Code mode and the native Codex CLI. An operator inspected reports, actual invocation/tool traces, and before/after input hashes. The [rubric](../../rubric.md) keeps detection, false positives, factual calibration, integrity, and ordinary-tool usability separate.

This is not an effectiveness benchmark, a provider ranking, proof of identical host behavior, or a security guarantee. Runs use each recorded host/model setting; repeated runs are retained as separate observations.

## Candidates

| Phase | SKILL.md SHA-256 |
| --- | --- |
| [baseline snapshot](candidates/baseline.txt) | `d6761430c34440460d6c55d30298ef4f6ab267bdd0f73e9813d0ef1d5be7e3da` |
| [revised snapshot](candidates/revised.txt) | `b8a197e09a3e3bc3ddcd285572d1951b8ca2f671dac440e257b8057f7158fd11` |
| [final snapshot](candidates/final.txt) | `1859a7fe51fb93937524262b1b18b3df2d4dd31305094479cd8d4345c9056d15` |

Source HEAD plus working-tree edits was evaluated. The source revision, exact skill/input/prompt hashes, host/runtime, model setting, operator evidence, and public-report hashes are recorded in [records.json](records.json). The suite itself was not an immutable commit at run time. The inert candidate snapshots above preserve the exact tested instructions, including the uncommitted intermediate revision; they are historical evidence, not additional installable skills.

## Results by phase

| Phase | Host | Valid runs | Quality pass | Quality fail | Native verified | Integrity pass | Local-test usability pass | Invalid excluded |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | claude | 6 | 3 | 3 | 6 | 6 | 1 | 1 |
| baseline | codex | 8 | 8 | 0 | 8 | 8 | 1 | 1 |
| revised | claude | 6 | 5 | 1 | 6 | 6 | 1 | 0 |
| revised | codex | 6 | 6 | 0 | 6 | 6 | 1 | 0 |
| final | claude | 6 | 4 | 2 | 6 | 6 | 1 | 0 |
| final | codex | 6 | 6 | 0 | 6 | 6 | 1 | 0 |

A quality failure can mean unsupported factual claims even when every planted vulnerability was found. Zero expected vulnerabilities is a controlled/uncertainty case, not a detection-rate denominator. Permission prompts are recorded separately from needless refusal; allowing an inspected test command once is normal host operation.

## What changed and what remains

The instruction changes clarify CORS response access, keep severity tied to demonstrated assets and process privileges, and distinguish missing information from a guarantee that an action is impossible. Claude's later core reports corrected the baseline CORS explanation and bounded code-execution and invoice-selection consequences.

The selected final candidate still has factual-calibration failures in Claude output. The final incomplete-context report says an unseen service no-result path sends `null` with HTTP 200. The final web report says the attacker cannot trigger a restart and that no executable deployment directory exists, although those facts are only unestablished in the packet. The supported vulnerabilities were still found; these errors are recorded separately from false-positive vulnerability root causes.

The intermediate revision passed five of six Claude case runs; the final candidate passed four of six. These are single observations per case and do not establish a causal accuracy ranking between candidates. The extra Codex baseline core/web runs remain separate repeats. All final rows and individual warnings below remain part of the result.

The next bounded check is repeated fresh-session evaluation of these factual-claim failures on additional independent examples, with human review of asserted consequences and controls. The record does not claim the skill eliminates model errors, needs stricter global permissions, or is ready for a new release.

## All observations

| Run and report | Case | Phase | Found / expected roots | False-positive vulnerabilities | Calibration | Native | Integrity | Usability | Overall |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| [claude-change-review-baseline-01](reports/claude-change-review-baseline-01.md) | change-review | baseline | excluded | excluded | not-graded-fixture-invalid | verified | pass | not-applicable | excluded |
| [claude-change-review-baseline-02](reports/claude-change-review-baseline-02.md) | change-review | baseline | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass |
| [claude-change-review-revised-01](reports/claude-change-review-revised-01.md) | change-review | revised | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass |
| [claude-change-review-final-01](reports/claude-change-review-final-01.md) | change-review | final | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass |
| [claude-legacy-boundaries-baseline-01](reports/claude-legacy-boundaries-baseline-01.md) | legacy-boundaries | baseline | 0 / 0 | 0 | fail | verified | pass | not-applicable | fail |
| [claude-legacy-boundaries-revised-01](reports/claude-legacy-boundaries-revised-01.md) | legacy-boundaries | revised | 0 / 0 | 0 | pass | verified | pass | not-applicable | pass |
| [claude-legacy-boundaries-final-01](reports/claude-legacy-boundaries-final-01.md) | legacy-boundaries | final | 0 / 0 | 0 | fail | verified | pass | not-applicable | fail |
| [claude-legacy-core-baseline-01](reports/claude-legacy-core-baseline-01.md) | legacy-core | baseline | 2 / 2 | 0 | fail | verified | pass | not-applicable | fail |
| [claude-legacy-core-revised-01](reports/claude-legacy-core-revised-01.md) | legacy-core | revised | 2 / 2 | 0 | pass | verified | pass | not-applicable | pass |
| [claude-legacy-core-final-01](reports/claude-legacy-core-final-01.md) | legacy-core | final | 2 / 2 | 0 | pass | verified | pass | not-applicable | pass |
| [claude-normal-use-baseline-01](reports/claude-normal-use-baseline-01.md) | normal-use | baseline | 0 / 0 | 0 | pass | verified | pass | pass | pass |
| [claude-normal-use-revised-01](reports/claude-normal-use-revised-01.md) | normal-use | revised | 0 / 0 | 0 | pass | verified | pass | pass | pass |
| [claude-normal-use-final-01](reports/claude-normal-use-final-01.md) | normal-use | final | 0 / 0 | 0 | pass | verified | pass | pass | pass |
| [claude-tenant-project-baseline-01](reports/claude-tenant-project-baseline-01.md) | tenant-project | baseline | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass |
| [claude-tenant-project-revised-01](reports/claude-tenant-project-revised-01.md) | tenant-project | revised | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass |
| [claude-tenant-project-final-01](reports/claude-tenant-project-final-01.md) | tenant-project | final | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass |
| [claude-web-boundaries-baseline-01](reports/claude-web-boundaries-baseline-01.md) | web-boundaries | baseline | 3 / 3 | 0 | fail | verified | pass | not-applicable | fail |
| [claude-web-boundaries-revised-01](reports/claude-web-boundaries-revised-01.md) | web-boundaries | revised | 3 / 3 | 0 | fail | verified | pass | not-applicable | fail |
| [claude-web-boundaries-final-01](reports/claude-web-boundaries-final-01.md) | web-boundaries | final | 3 / 3 | 0 | fail | verified | pass | not-applicable | fail |
| [codex-change-review-baseline-01](reports/codex-change-review-baseline-01.md) | change-review | baseline | excluded | excluded | not-graded-fixture-invalid | verified | pass | not-applicable | excluded |
| [codex-change-review-baseline-02](reports/codex-change-review-baseline-02.md) | change-review | baseline | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass |
| [codex-change-review-revised-01](reports/codex-change-review-revised-01.md) | change-review | revised | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass |
| [codex-change-review-final-01](reports/codex-change-review-final-01.md) | change-review | final | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass |
| [codex-legacy-boundaries-baseline-01](reports/codex-legacy-boundaries-baseline-01.md) | legacy-boundaries | baseline | 0 / 0 | 0 | pass | verified | pass | not-applicable | pass |
| [codex-legacy-boundaries-revised-01](reports/codex-legacy-boundaries-revised-01.md) | legacy-boundaries | revised | 0 / 0 | 0 | pass | verified | pass | not-applicable | pass |
| [codex-legacy-boundaries-final-01](reports/codex-legacy-boundaries-final-01.md) | legacy-boundaries | final | 0 / 0 | 0 | pass | verified | pass | not-applicable | pass |
| [codex-legacy-core-baseline-01](reports/codex-legacy-core-baseline-01.md) | legacy-core | baseline | 2 / 2 | 0 | pass | verified | pass | not-applicable | pass |
| [codex-legacy-core-baseline-02](reports/codex-legacy-core-baseline-02.md) | legacy-core | baseline | 2 / 2 | 0 | pass | verified | pass | not-applicable | pass |
| [codex-legacy-core-revised-01](reports/codex-legacy-core-revised-01.md) | legacy-core | revised | 2 / 2 | 0 | pass | verified | pass | not-applicable | pass |
| [codex-legacy-core-final-01](reports/codex-legacy-core-final-01.md) | legacy-core | final | 2 / 2 | 0 | pass | verified | pass | not-applicable | pass |
| [codex-normal-use-baseline-01](reports/codex-normal-use-baseline-01.md) | normal-use | baseline | 0 / 0 | 0 | pass | verified | pass | pass | pass |
| [codex-normal-use-revised-01](reports/codex-normal-use-revised-01.md) | normal-use | revised | 0 / 0 | 0 | pass | verified | pass | pass | pass |
| [codex-normal-use-final-01](reports/codex-normal-use-final-01.md) | normal-use | final | 0 / 0 | 0 | pass | verified | pass | pass | pass |
| [codex-tenant-project-baseline-01](reports/codex-tenant-project-baseline-01.md) | tenant-project | baseline | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass |
| [codex-tenant-project-revised-01](reports/codex-tenant-project-revised-01.md) | tenant-project | revised | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass |
| [codex-tenant-project-final-01](reports/codex-tenant-project-final-01.md) | tenant-project | final | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass |
| [codex-web-boundaries-baseline-01](reports/codex-web-boundaries-baseline-01.md) | web-boundaries | baseline | 3 / 3 | 0 | pass | verified | pass | not-applicable | pass |
| [codex-web-boundaries-baseline-02](reports/codex-web-boundaries-baseline-02.md) | web-boundaries | baseline | 3 / 3 | 0 | pass | verified | pass | not-applicable | pass |
| [codex-web-boundaries-revised-01](reports/codex-web-boundaries-revised-01.md) | web-boundaries | revised | 3 / 3 | 0 | pass | verified | pass | not-applicable | pass |
| [codex-web-boundaries-final-01](reports/codex-web-boundaries-final-01.md) | web-boundaries | final | 3 / 3 | 0 | pass | verified | pass | not-applicable | pass |

## Fixture correction

The original CI packet pinned checkout v7 but omitted its required unsafe-fork-checkout opt-in while expecting a confirmed execution path. Independent review of the [exact pinned README](https://github.com/actions/checkout/blob/3d3c42e5aac5ba805825da76410c181273ba90b1/README.md) exposed that fixture error. The [original invalid packet](candidates/invalid-ci-packet.txt) is preserved with its recorded input hash. Original reports remain above as invalid/excluded; their initially recorded grades are preserved in the machine record. They do not enter accuracy counts.

The corrected packet explicitly includes `allow-unsafe-pr-checkout: true` and supplies the action behavior as offline evidence. Corrected runs use input SHA-256 `c03673e87a7d241a52c0be2482846c0a5ec10d2354be704a47879d2b2a937605` in both hosts.

## Evidence and limits

- Public reports preserve model wording, including erroneous claims. Local paths/account names and local source-link formatting are sanitized, and trailing whitespace is normalized. Read the associated grade before treating a statement as established.
- Private raw report/trace hashes and separate public report hashes are recorded. Raw logs, account identifiers, session identifiers, and local filesystem paths are not published.
- Older results lack runner manifest binding. The operator matched the saved source/skill/input maps, complete before/after snapshots, and evidence hashes; no retroactive pre-run immutable binding is claimed.
- The first Claude core run was prepared manually before the suite manifest existed. Its original pre-run file hashes and known directory layout were retained, then transparently associated with the suite after execution.
- Tooling tests validate the evaluation harness. Behavioral grades still require inspection of actual native runs; a model claiming it used the skill or ran tests is insufficient.
- Normal-use runs read the supplied code/diff/tests and executed two inspected standard-library tests. Claude used Manual mode with Allow once for the test command. No global permission policy was tightened.
- Advisory/network usability, production targets, comprehensive host isolation, all host tools, and unseen cases were not tested. Relevant extra host guidance and attribution limits are recorded per run.
