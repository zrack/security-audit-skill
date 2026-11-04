Found **one introduced security issue** in the supplied synthetic BASE → HEAD change.

**High severity · High confidence — Fork-controlled code executes with repository secrets and write credentials.**
Location: `.github/workflows/verify.yml`, synthetic HEAD lines 3–17 (`supplied diff`).

HEAD changes verification to `pull_request_target`, grants `contents: write`, exposes `CI_SIGNING_KEY`, and checks out the attacker-controlled fork SHA before executing `python ci/check.py`. A fork author can therefore supply Python code that accesses the private key and repository write credentials without changing the protected default branch.

The supplied checkout-v7 contract establishes that `allow-unsafe-pr-checkout: true` disables its protective refusal. Persisted credentials are accessible to subsequent commands through Git configuration referencing a file under `$RUNNER_TEMP`; they are **not stored directly in `.git/config`**. Post-job cleanup occurs after the attacker-controlled script runs.

Restore verification to `pull_request` with read-only permissions and no signing secret. Restrict privileged signing to trusted code. Statically verify that no fork-controlled executable content reaches a job holding secrets or write credentials.

The supplied unchanged context has two distinct outcomes:

- `app/export.py` contains **pre-existing shell command injection**: an ordinary authenticated account controls text concatenated into a `shell=True` command, enabling commands as the application service user. This exists in both snapshots and is not introduced by this patch.
- `test.yml` has no substantiated security finding under the supplied contract: executing submitted tests is intentional, with no repository secrets, write token, unrelated credentials, or persistent trusted state.

I compared only the supplied workflow diff and read both unchanged excerpts and all accompanying contracts. BASE and HEAD were treated as synthetic labels; no commits were fetched or compared. Validation was static only: no sample execution, network access, dependency installation, credential testing, or file modifications. Checkout behavior was accepted from the supplied contract. The signing key’s lifetime and external privileges, and any ability to bypass branch protections, remain unestablished.
