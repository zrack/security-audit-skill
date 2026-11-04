The supplied change introduces **one High-severity security issue**. The export route contains a separate, pre-existing issue.

**Introduced — High severity, High confidence: fork-controlled code receives trusted credentials.** In `.github/workflows/verify.yml`, HEAD combines `pull_request_target`, `contents: write`, job-wide `CI_SIGNING_KEY`, checkout of the fork’s head SHA, and execution of its `ci/check.py`. The explicit `allow-unsafe-pr-checkout: true` bypasses checkout v7’s default refusal. (`Supplied diff`)

A fork author can therefore execute code that reads the signing secret and uses the write-capable checkout credential, with no blocking approval gate. Under the supplied contract, that credential remains accessible to job-user commands through a separate file under `$RUNNER_TEMP`, referenced by Git configuration, until post-job cleanup. Repository writes remain subject to applicable repository protections.

Fix: run fork checks under `pull_request` with `contents: read`, remove secret injection and the unsafe checkout override, and keep privileged operations on trusted code paths. Verify that every fork-controlled execution path lacks secrets and write-capable credentials. If affected runs have occurred, rotate the signing key and review their repository activity.

The key’s “external privileges are not supplied” and its lifetime “is not specified”; external compromise scope and lasting credential access are unresolved. (`Contract`)

**Pre-existing — High severity, High confidence: authenticated shell command injection.** `app/export.py` concatenates unvalidated `format` input into a command with `shell=True`. An ordinary self-registered account can supply shell syntax and execute commands as the application’s service user. This exists identically in BASE and HEAD and is not executed by either workflow. Fix by allowlisting formats and invoking `render` with an argument list and the shell disabled; verify both controls. (`Supplied excerpt and contract`)

The unchanged Tests workflow has **no substantiated security finding under the supplied guarantees**: submitted-test execution is intended, and the runner has no repository secrets, write-capable token, unrelated credentials, or persistent trusted state.

**Comparison and validation limits:** I reviewed the complete packet’s synthetic BASE-to-HEAD unified diff and both unchanged excerpts—not fetched commits or complete repository snapshots. Validation was static inspection only. Checkout v7 behavior and deployment conditions were accepted from the supplied contracts. No sample code, workflows, or tests were executed; no network access, dependency installation, credential testing, or file modifications occurred.
