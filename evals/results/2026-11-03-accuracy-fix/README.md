# Accuracy-fix native-host evaluation

Date: November 3, 2026.

This follow-up preserves all recorded attempts while leaving the [original 40 observations](../2026-11-03/README.md) unchanged. Reports and grades are manually reviewed; the export utility only checks consistency and evidence hashes.

Primary shared-suite coverage is separate from targeted checks, repeats, and the supplemental transfer packet. A partial candidate is not a six-case pass. The first counterexample web case is a predeclared primary slot with a web-first screening order, retained regardless of outcome. Per-session effort diagnostics have separate configuration cohorts and are not merged with default-setting observations.

## Candidates

| Candidate | Exact tested instructions | SHA-256 |
| --- | --- | --- |
| worked-examples | [inert snapshot](candidates/worked-examples.txt) | `617dfa2ce7eb695b90b49c3077fd7daaabe659db6b5958504b987ff00641106b` |
| qualified | [inert snapshot](candidates/qualified.txt) | `c052b6e5b9b95e52dba052587949074051b8f72e60d40535d0ec557e50d250f3` |
| counterexample | [inert snapshot](candidates/counterexample.txt) | `87929b60254e77377172fe579b100a12296256bb70095ce0e10333dfe4f09f46` |
| peer-review | [inert snapshot](candidates/peer-review.txt) | `939e68a881e08046f4a19e6337c6fd6be7f35e3c79603457c9e7ef17ea61a7c8` |
| source-map | [inert snapshot](candidates/source-map.txt) | `2c7c321c03a643356f03552f9b9fd51107827d1027eae6981af8f012544c5ea7` |
| positive-report | [inert snapshot](candidates/positive-report.txt) | `16483ef35ca1f150a02dff2442683ae4cc543a64a1cfd58629dcff0ec30fa031` |
| coverage | [inert snapshot](candidates/coverage.txt) | `0f3aaadbbd9a7b15536cc3be2a427f248df1264c1b368ab949ea4026a66fc81b` |
| report-scope | [inert snapshot](candidates/report-scope.txt) | `1b5c9b62748d4331f9b82fe20390290c50a826e7234687bd8f41a3dfd908d48c` |

Selected: report-scope (1b5c9b6), with the recorded Claude Medium and Codex configured-default cohorts. Each host passed all six primary cases, both predeclared fresh repeats, and its separate transfer check. These bounded passes do not imply perfect factual accuracy; warnings and earlier failed attempts remain visible.

Snapshots preserve historical tested bytes; they are not additional installable skills.

## What changed

The selected instructions sharpen evidence calibration and keep security-only reports focused on security issues, while preserving broader reviews when requested. Unknown helper, lifecycle, and deployment behavior remains qualified; demonstrated attacker capabilities still support concrete findings. Experimental peer-review and source-map instructions were removed. Model and effort diagnostics remain historical observations, not installation requirements. The final skill adds no agent calls, tool gates, permission restrictions, or dependencies.

Passing this security-review rubric does not make every sentence correct. Selected reports retain nonblocking warnings about restart frequency, conditional assets and loose upper bounds, an int-subclass generalization without a supplied attacker-object path in normal use, and overbroad proposed CI verification. Per-report warnings and claim adjudications remain in records.json. Earlier failures, including the preceding coverage candidate’s failed boundary repeat, are preserved and are not added to the selected candidate’s denominators.

## Coverage and quality

| Candidate | Host | Configuration cohort | Run kind | Shared coverage | Complete shared suite | Recorded | Quality pass | Quality fail | Ungraded | Native verified | Integrity pass | Local-test usability pass |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| worked-examples | claude | medium | primary | 6 of 6 | true | 6 | 4 | 2 | 0 | 6 | 6 | 1 |
| worked-examples | codex | configured-default | primary | 6 of 6 | true | 6 | 6 | 0 | 0 | 6 | 6 | 1 |
| qualified | claude | medium | primary | 6 of 6 | true | 6 | 5 | 1 | 0 | 6 | 6 | 1 |
| qualified | codex | configured-default | primary | 6 of 6 | true | 6 | 6 | 0 | 0 | 6 | 6 | 1 |
| qualified | codex | configured-default | transfer | separate check | not applicable | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| counterexample | claude | high-effort-diagnostic | primary | 1 of 6 | false | 1 | 0 | 1 | 0 | 1 | 1 | 0 |
| counterexample | claude | medium | primary | 1 of 6 | false | 1 | 0 | 1 | 0 | 1 | 1 | 0 |
| peer-review | claude | medium | primary | 1 of 6 | false | 1 | 0 | 1 | 0 | 1 | 1 | 0 |
| source-map | claude | medium | primary | 1 of 6 | false | 1 | 0 | 1 | 0 | 1 | 1 | 0 |
| source-map | claude | opus5-medium-diagnostic | primary | 1 of 6 | false | 1 | 0 | 1 | 0 | 1 | 1 | 0 |
| positive-report | claude | medium | primary | 1 of 6 | false | 1 | 0 | 1 | 0 | 1 | 1 | 0 |
| coverage | claude | medium | primary | 6 of 6 | true | 6 | 6 | 0 | 0 | 6 | 6 | 1 |
| coverage | claude | medium | repeat | separate check | not applicable | 2 | 1 | 1 | 0 | 2 | 2 | 0 |
| coverage | claude | medium | transfer | separate check | not applicable | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| coverage | codex | configured-default | primary | 6 of 6 | true | 6 | 6 | 0 | 0 | 6 | 6 | 1 |
| coverage | codex | configured-default | transfer | separate check | not applicable | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| report-scope | claude | medium | primary | 6 of 6 | true | 6 | 6 | 0 | 0 | 6 | 6 | 1 |
| report-scope | claude | medium | repeat | separate check | not applicable | 2 | 2 | 0 | 0 | 2 | 2 | 0 |
| report-scope | claude | medium | transfer | separate check | not applicable | 1 | 1 | 0 | 0 | 1 | 1 | 0 |
| report-scope | codex | configured-default | primary | 6 of 6 | true | 6 | 6 | 0 | 0 | 6 | 6 | 1 |
| report-scope | codex | configured-default | repeat | separate check | not applicable | 2 | 2 | 0 | 0 | 2 | 2 | 0 |
| report-scope | codex | configured-default | transfer | separate check | not applicable | 1 | 1 | 0 | 0 | 1 | 1 | 0 |

Configuration cohorts are explicit observation groups, not model equivalence claims. Requested model/effort selections and actual trace-observed model/effort evidence remain separate in each machine record. A change in model or effort is not attributed to instructions alone.
- `medium`: Opus 5.5 Medium in the recorded Claude runs; actual API identity and effort evidence are retained per row.
- `high-effort-diagnostic`: Same counterexample instructions, per-session Opus 5.5 High diagnostic; never merged with Medium.
- `opus5-medium-diagnostic`: Opus 5 Medium requested per session with unchanged source-map instructions; actual API identity is recorded independently, and this cohort is never merged with Opus 5.5.
- `configured-default`: Codex configured default; observed configuration and server-resolution limitations are retained per row.

A quality failure can be an unsupported factual assertion even when the supported vulnerability was found. Controlled cases and unresolved candidates do not create a vulnerability-detection denominator. Repeated successes are not added to primary coverage.

## All recorded observations

| Run and report | Candidate | Configuration cohort | Kind | Case | Roots found / expected | False-positive vulnerabilities | Calibration | Native | Integrity | Usability | Quality | Overall |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| [claude-web-boundaries-counterexample-high-effort-diagnostic-primary-01](reports/claude-web-boundaries-counterexample-high-effort-diagnostic-primary-01.md) | counterexample | high-effort-diagnostic | primary | web-boundaries | 3 / 3 | 0 | fail | verified | pass | not-applicable | fail | fail |
| [claude-web-boundaries-counterexample-medium-primary-01](reports/claude-web-boundaries-counterexample-medium-primary-01.md) | counterexample | medium | primary | web-boundaries | 3 / 3 | 0 | fail | verified | pass | not-applicable | fail | fail |
| [claude-change-review-coverage-medium-primary-01](reports/claude-change-review-coverage-medium-primary-01.md) | coverage | medium | primary | change-review | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-legacy-boundaries-coverage-medium-primary-01](reports/claude-legacy-boundaries-coverage-medium-primary-01.md) | coverage | medium | primary | legacy-boundaries | 0 / 0 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-legacy-core-coverage-medium-primary-01](reports/claude-legacy-core-coverage-medium-primary-01.md) | coverage | medium | primary | legacy-core | 2 / 2 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-normal-use-coverage-medium-primary-01](reports/claude-normal-use-coverage-medium-primary-01.md) | coverage | medium | primary | normal-use | 0 / 0 | 0 | pass | verified | pass | pass | pass | pass |
| [claude-tenant-project-coverage-medium-primary-01](reports/claude-tenant-project-coverage-medium-primary-01.md) | coverage | medium | primary | tenant-project | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-web-boundaries-coverage-medium-primary-01](reports/claude-web-boundaries-coverage-medium-primary-01.md) | coverage | medium | primary | web-boundaries | 3 / 3 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-legacy-boundaries-coverage-medium-repeat-01](reports/claude-legacy-boundaries-coverage-medium-repeat-01.md) | coverage | medium | repeat | legacy-boundaries | 0 / 0 | 0 | fail | verified | pass | not-applicable | fail | fail |
| [claude-web-boundaries-coverage-medium-repeat-01](reports/claude-web-boundaries-coverage-medium-repeat-01.md) | coverage | medium | repeat | web-boundaries | 3 / 3 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-claim-transfer-coverage-medium-transfer-01](reports/claude-claim-transfer-coverage-medium-transfer-01.md) | coverage | medium | transfer | claim-transfer | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-change-review-coverage-configured-default-primary-01](reports/codex-change-review-coverage-configured-default-primary-01.md) | coverage | configured-default | primary | change-review | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-legacy-boundaries-coverage-configured-default-primary-01](reports/codex-legacy-boundaries-coverage-configured-default-primary-01.md) | coverage | configured-default | primary | legacy-boundaries | 0 / 0 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-legacy-core-coverage-configured-default-primary-01](reports/codex-legacy-core-coverage-configured-default-primary-01.md) | coverage | configured-default | primary | legacy-core | 2 / 2 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-normal-use-coverage-configured-default-primary-01](reports/codex-normal-use-coverage-configured-default-primary-01.md) | coverage | configured-default | primary | normal-use | 0 / 0 | 0 | pass | verified | pass | pass | pass | pass |
| [codex-tenant-project-coverage-configured-default-primary-01](reports/codex-tenant-project-coverage-configured-default-primary-01.md) | coverage | configured-default | primary | tenant-project | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-web-boundaries-coverage-configured-default-primary-01](reports/codex-web-boundaries-coverage-configured-default-primary-01.md) | coverage | configured-default | primary | web-boundaries | 3 / 3 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-claim-transfer-coverage-configured-default-transfer-01](reports/codex-claim-transfer-coverage-configured-default-transfer-01.md) | coverage | configured-default | transfer | claim-transfer | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-web-boundaries-peer-review-medium-primary-01](reports/claude-web-boundaries-peer-review-medium-primary-01.md) | peer-review | medium | primary | web-boundaries | 3 / 3 | 0 | fail | verified | pass | not-applicable | fail | fail |
| [claude-web-boundaries-positive-report-medium-primary-01](reports/claude-web-boundaries-positive-report-medium-primary-01.md) | positive-report | medium | primary | web-boundaries | 3 / 3 | 0 | fail | verified | pass | not-applicable | fail | fail |
| [claude-change-review-qualified-medium-primary-01](reports/claude-change-review-qualified-medium-primary-01.md) | qualified | medium | primary | change-review | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-legacy-boundaries-qualified-medium-primary-01](reports/claude-legacy-boundaries-qualified-medium-primary-01.md) | qualified | medium | primary | legacy-boundaries | 0 / 0 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-legacy-core-qualified-medium-primary-01](reports/claude-legacy-core-qualified-medium-primary-01.md) | qualified | medium | primary | legacy-core | 2 / 2 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-normal-use-qualified-medium-primary-01](reports/claude-normal-use-qualified-medium-primary-01.md) | qualified | medium | primary | normal-use | 0 / 0 | 0 | pass | verified | pass | pass | pass | pass |
| [claude-tenant-project-qualified-medium-primary-01](reports/claude-tenant-project-qualified-medium-primary-01.md) | qualified | medium | primary | tenant-project | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-web-boundaries-qualified-medium-primary-01](reports/claude-web-boundaries-qualified-medium-primary-01.md) | qualified | medium | primary | web-boundaries | 3 / 3 | 0 | fail | verified | pass | not-applicable | fail | fail |
| [codex-change-review-qualified-configured-default-primary-01](reports/codex-change-review-qualified-configured-default-primary-01.md) | qualified | configured-default | primary | change-review | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-legacy-boundaries-qualified-configured-default-primary-01](reports/codex-legacy-boundaries-qualified-configured-default-primary-01.md) | qualified | configured-default | primary | legacy-boundaries | 0 / 0 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-legacy-core-qualified-configured-default-primary-01](reports/codex-legacy-core-qualified-configured-default-primary-01.md) | qualified | configured-default | primary | legacy-core | 2 / 2 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-normal-use-qualified-configured-default-primary-01](reports/codex-normal-use-qualified-configured-default-primary-01.md) | qualified | configured-default | primary | normal-use | 0 / 0 | 0 | pass | verified | pass | pass | pass | pass |
| [codex-tenant-project-qualified-configured-default-primary-01](reports/codex-tenant-project-qualified-configured-default-primary-01.md) | qualified | configured-default | primary | tenant-project | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-web-boundaries-qualified-configured-default-primary-01](reports/codex-web-boundaries-qualified-configured-default-primary-01.md) | qualified | configured-default | primary | web-boundaries | 3 / 3 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-claim-transfer-qualified-configured-default-transfer-01](reports/codex-claim-transfer-qualified-configured-default-transfer-01.md) | qualified | configured-default | transfer | claim-transfer | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-change-review-report-scope-medium-primary-01](reports/claude-change-review-report-scope-medium-primary-01.md) | report-scope | medium | primary | change-review | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-legacy-boundaries-report-scope-medium-primary-01](reports/claude-legacy-boundaries-report-scope-medium-primary-01.md) | report-scope | medium | primary | legacy-boundaries | 0 / 0 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-legacy-core-report-scope-medium-primary-01](reports/claude-legacy-core-report-scope-medium-primary-01.md) | report-scope | medium | primary | legacy-core | 2 / 2 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-normal-use-report-scope-medium-primary-01](reports/claude-normal-use-report-scope-medium-primary-01.md) | report-scope | medium | primary | normal-use | 0 / 0 | 0 | pass | verified | pass | pass | pass | pass |
| [claude-tenant-project-report-scope-medium-primary-01](reports/claude-tenant-project-report-scope-medium-primary-01.md) | report-scope | medium | primary | tenant-project | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-web-boundaries-report-scope-medium-primary-01](reports/claude-web-boundaries-report-scope-medium-primary-01.md) | report-scope | medium | primary | web-boundaries | 3 / 3 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-legacy-boundaries-report-scope-medium-repeat-01](reports/claude-legacy-boundaries-report-scope-medium-repeat-01.md) | report-scope | medium | repeat | legacy-boundaries | 0 / 0 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-web-boundaries-report-scope-medium-repeat-01](reports/claude-web-boundaries-report-scope-medium-repeat-01.md) | report-scope | medium | repeat | web-boundaries | 3 / 3 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-claim-transfer-report-scope-medium-transfer-01](reports/claude-claim-transfer-report-scope-medium-transfer-01.md) | report-scope | medium | transfer | claim-transfer | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-change-review-report-scope-configured-default-primary-01](reports/codex-change-review-report-scope-configured-default-primary-01.md) | report-scope | configured-default | primary | change-review | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-legacy-boundaries-report-scope-configured-default-primary-01](reports/codex-legacy-boundaries-report-scope-configured-default-primary-01.md) | report-scope | configured-default | primary | legacy-boundaries | 0 / 0 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-legacy-core-report-scope-configured-default-primary-01](reports/codex-legacy-core-report-scope-configured-default-primary-01.md) | report-scope | configured-default | primary | legacy-core | 2 / 2 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-normal-use-report-scope-configured-default-primary-01](reports/codex-normal-use-report-scope-configured-default-primary-01.md) | report-scope | configured-default | primary | normal-use | 0 / 0 | 0 | pass | verified | pass | pass | pass | pass |
| [codex-tenant-project-report-scope-configured-default-primary-01](reports/codex-tenant-project-report-scope-configured-default-primary-01.md) | report-scope | configured-default | primary | tenant-project | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-web-boundaries-report-scope-configured-default-primary-01](reports/codex-web-boundaries-report-scope-configured-default-primary-01.md) | report-scope | configured-default | primary | web-boundaries | 3 / 3 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-legacy-boundaries-report-scope-configured-default-repeat-01](reports/codex-legacy-boundaries-report-scope-configured-default-repeat-01.md) | report-scope | configured-default | repeat | legacy-boundaries | 0 / 0 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-web-boundaries-report-scope-configured-default-repeat-01](reports/codex-web-boundaries-report-scope-configured-default-repeat-01.md) | report-scope | configured-default | repeat | web-boundaries | 3 / 3 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-claim-transfer-report-scope-configured-default-transfer-01](reports/codex-claim-transfer-report-scope-configured-default-transfer-01.md) | report-scope | configured-default | transfer | claim-transfer | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-web-boundaries-source-map-medium-primary-01](reports/claude-web-boundaries-source-map-medium-primary-01.md) | source-map | medium | primary | web-boundaries | 3 / 3 | 0 | fail | verified | pass | not-applicable | fail | fail |
| [claude-web-boundaries-source-map-opus5-medium-diagnostic-primary-01](reports/claude-web-boundaries-source-map-opus5-medium-diagnostic-primary-01.md) | source-map | opus5-medium-diagnostic | primary | web-boundaries | 3 / 3 | 0 | fail | verified | pass | not-applicable | fail | fail |
| [claude-change-review-worked-examples-medium-primary-01](reports/claude-change-review-worked-examples-medium-primary-01.md) | worked-examples | medium | primary | change-review | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-legacy-boundaries-worked-examples-medium-primary-01](reports/claude-legacy-boundaries-worked-examples-medium-primary-01.md) | worked-examples | medium | primary | legacy-boundaries | 0 / 0 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-legacy-core-worked-examples-medium-primary-01](reports/claude-legacy-core-worked-examples-medium-primary-01.md) | worked-examples | medium | primary | legacy-core | 2 / 2 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [claude-normal-use-worked-examples-medium-primary-01](reports/claude-normal-use-worked-examples-medium-primary-01.md) | worked-examples | medium | primary | normal-use | 0 / 0 | 0 | pass | verified | pass | pass | pass | pass |
| [claude-tenant-project-worked-examples-medium-primary-01](reports/claude-tenant-project-worked-examples-medium-primary-01.md) | worked-examples | medium | primary | tenant-project | 1 / 1 | 0 | fail | verified | pass | not-applicable | fail | fail |
| [claude-web-boundaries-worked-examples-medium-primary-01](reports/claude-web-boundaries-worked-examples-medium-primary-01.md) | worked-examples | medium | primary | web-boundaries | 3 / 3 | 0 | fail | verified | pass | not-applicable | fail | fail |
| [codex-change-review-worked-examples-configured-default-primary-01](reports/codex-change-review-worked-examples-configured-default-primary-01.md) | worked-examples | configured-default | primary | change-review | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-legacy-boundaries-worked-examples-configured-default-primary-01](reports/codex-legacy-boundaries-worked-examples-configured-default-primary-01.md) | worked-examples | configured-default | primary | legacy-boundaries | 0 / 0 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-legacy-core-worked-examples-configured-default-primary-01](reports/codex-legacy-core-worked-examples-configured-default-primary-01.md) | worked-examples | configured-default | primary | legacy-core | 2 / 2 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-normal-use-worked-examples-configured-default-primary-01](reports/codex-normal-use-worked-examples-configured-default-primary-01.md) | worked-examples | configured-default | primary | normal-use | 0 / 0 | 0 | pass | verified | pass | pass | pass | pass |
| [codex-tenant-project-worked-examples-configured-default-primary-01](reports/codex-tenant-project-worked-examples-configured-default-primary-01.md) | worked-examples | configured-default | primary | tenant-project | 1 / 1 | 0 | pass | verified | pass | not-applicable | pass | pass |
| [codex-web-boundaries-worked-examples-configured-default-primary-01](reports/codex-web-boundaries-worked-examples-configured-default-primary-01.md) | worked-examples | configured-default | primary | web-boundaries | 3 / 3 | 0 | pass | verified | pass | not-applicable | pass | pass |

## Prospective input-context clarification

The original core packet did not specify SQLite row_factory. Earlier bank-response interpretation assumed mapping-like rows; a missing-row-factory caveat is valid. The revised contract prospectively states sqlite3.Row. Earlier observations and grades are retained unchanged and must not be described as an identical-input comparison with revised-core runs.

The [original core packet](input-legacy-core-original.txt) and [mapping-row contract version](input-legacy-core-mapping-rows.txt) preserve both exact inputs. Each row records its input hash; the second version is used only in future observed rows that actually received it. [Python documentation](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.row_factory) describes the row factory behavior. This clarification leaves the earlier campaign files unchanged.

## Evidence and limits

- [Machine-readable records](records.json) retain individual failures, warnings, input/prompt/skill maps, source context, and raw-evidence hashes. No accuracy grade is inferred from response keywords.
- Public reports retain model wording and erroneous claims. Only private identifiers/paths, local-link formatting, and trailing whitespace are sanitized. Raw host traces are not public.
- The [supplemental input](input-heldout.txt) is separate from the six shared case slots. It checks an opaque helper, a reachable policy activation path, and explicit administrator controls. Its expected answer was excluded from reviewer inputs.
- Actual host/runtime, model/effort, permissions, co-exposed guidance, and observed approval behavior are recorded per run. No claim of isolated skill-only causality is made.
- When a native peer was actually invoked, public records include only inspected child evidence hashes and tool/model/effort/scope summaries. Child logs and local paths remain private. Skill prose alone does not establish peer invocation or successful factual correction.
- Source metadata marked unavailable stays unavailable. Content hashes identify tested bytes; they do not invent an immutable source commit or sign evidence against an operator who can rewrite files.
- These are bounded synthetic observations, not an effectiveness benchmark, provider ranking, comprehensive host-isolation audit, or guarantee of factual accuracy.
