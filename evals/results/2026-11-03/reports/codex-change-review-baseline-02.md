Found **one introduced security issue: High severity, High confidence**.

**Fork-controlled code executes with a private secret and repository-write credentials.** In supplied HEAD `.github/workflows/verify.yml`, switching to `pull_request_target`, granting `contents: write`, exporting `CI_SIGNING_KEY`, and checking out the PR head makes the existing `python ci/check.py` execute attacker-controlled code with trusted-job privileges. See the `supplied change`.

A fork author can modify `ci/check.py` without changing the protected default branch. The explicit `allow-unsafe-pr-checkout: true` disables checkout v7’s relevant refusal. Their script can read `CI_SIGNING_KEY` and use the persisted write-capable credential. Per the supplied contract, that credential resides in a separate file under `$RUNNER_TEMP`, referenced by Git configuration, and remains accessible to the job user until cleanup.

This supports private-secret disclosure and repository-content writes within the token’s permissions. The evidence does not establish the signing key’s external privileges or lifetime, or bypass of protected-branch rules. BASE did not provide this combination of privileges to fork-controlled code.

**Fix:** Restore `pull_request` with `contents: read`, remove the secret from fork checks, and disable checkout credential persistence. Keep signing or other privileged operations in a trusted path that never executes fork-controlled code. Verify the revised workflow’s event, permissions, environment, checkout inputs, and execution paths against those requirements.

The unchanged context has two distinct outcomes:

- **`app/export.py`: pre-existing command injection.** Concatenating an ordinary authenticated user’s `format` parameter into `shell=True` permits command execution as the application’s service user. This exists in both snapshots and is unrelated to the workflow change. Replace shell construction with an argument list and validate allowed formats.
- **Tests workflow: no substantiated security finding under the supplied contract.** Executing submitted tests is its intended task; it receives neither repository secrets nor write credentials and has no persistent trusted state.

The actual comparison was the **supplied synthetic BASE-to-HEAD unified diff**, with both unchanged excerpts and all supplied contracts read. No commits were fetched, and snapshot completeness and action behavior were not independently verified. Review was static only: no sample execution, exploit testing, network access, dependency installation, credential testing, unrelated-file inspection, or file modification. This conclusion covers the supplied artifacts, not the entire application.
