**One introduced finding: High severity, High confidence — fork-controlled code receives privileged credentials.**

In `.github/workflows/verify.yml` (reconstructed HEAD lines 3–17), HEAD switches to `pull_request_target`, grants `contents: write`, exposes `CI_SIGNING_KEY`, and checks out the attacker’s fork SHA before running `python ci/check.py`. The explicit `allow-unsafe-pr-checkout: true` bypasses checkout v7’s refusal. See the `supplied diff`.

A fork author can modify `ci/check.py` and have it execute as the job user with access to:

- `CI_SIGNING_KEY` through the job environment.
- The contents-write checkout credential persisted under `$RUNNER_TEMP` and referenced by Git configuration until post-job cleanup.

This introduces credential exposure across the fork-to-trusted-job boundary. Repository protections may constrain subsequent writes, but do not prevent credential access. The signing key’s external privileges and lifetime are unknown, so broader compromise is not established.

**Fix:** Restore fork verification to `pull_request` with `contents: read`, remove the signing-secret environment variable and unsafe checkout override, and reserve privileged operations for trusted code. Verify statically that no fork-controlled execution path receives either credential.

**Unchanged context**

- `app/export.py` contains a **pre-existing authenticated shell-command injection**: an ordinary self-registered user controls `format`, which reaches `shell=True` without validation. Commands execute as the application service user. It is identical in BASE and HEAD and unrelated to the workflow execution path.
- The unchanged Tests workflow has **no substantiated finding under the supplied contract**: running submitted tests is intended, and its ephemeral runner receives neither repository secrets nor a write-capable token.

**Comparison and limits:** I compared only the synthetic BASE-to-HEAD diff and read both unchanged excerpts in `review-packet.md`. No commits were fetched or resolved. Validation was static; checkout behavior was accepted from the supplied offline contract. No sample code, workflows, or tests were executed; no network, dependency installation, credential testing, unrelated-file inspection, or file modification was performed.
