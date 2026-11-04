# Security review: `verify.yml` change from BASE to HEAD

## Scope

- **What was compared:** the BASE and HEAD snapshots supplied in `review-packet.md`. These are synthetic labels, not real commits. No commit hashes were fetched or verified.
- **What changed:** only `.github/workflows/verify.yml`.
- **Unchanged context:** `.github/workflows/test.yml` and `app/export.py`, which the packet says are the same in both snapshots.
- **Method:** I only read the code. I ran nothing, made no network calls, installed nothing, opened no other files and changed no files.
- **What I relied on:** the packet's own descriptions of the repository and action settings. That includes the `actions/checkout` v7 behavior, which I did not check against the action's source or documentation.

## Findings introduced by this change

### 1. Fork pull requests can run their own code with the signing secret and a write-access token. Severity: High. Confidence: High.

**Where:** `.github/workflows/verify.yml`, changed lines 18, 21, 25–26 and 29–31 of the diff.

**How the attack works:** none of the HEAD changes is dangerous alone, but together they let an attacker run code with secrets.
1. The trigger moves from `pull_request` to `pull_request_target`. The job now runs with the base repository's trust: it gets repository secrets and the token permissions set in the workflow.
2. `permissions` changes from `contents: read` to `contents: write`. The job's `GITHUB_TOKEN` can now write repository contents.
3. A job-level `env` puts `CI_SIGNING_KEY` into the environment of every step.
4. The checkout now uses `ref: ${{ github.event.pull_request.head.sha }}` with `allow-unsafe-pr-checkout: true`. Per the packet, this turns off v7's default refusal and checks out the fork's code.
5. `run: python ci/check.py` then runs `ci/check.py` from that attacker-controlled checkout.

An external author edits `ci/check.py` in their fork and opens a pull request. Their script runs as the job user with:
- `CI_SIGNING_KEY` in its environment.
- The `contents: write` token, which checkout saves by default in a file under `$RUNNER_TEMP` that the job user can read until post-job cleanup.

The packet says there is no approval gate and no environment protection, so this needs nothing beyond opening a fork pull request.

**What this proves:** an untrusted outsider can run code that reads a private repository secret and uses a write-capable repository token. The script can send both out of the runner.

**What depends on facts not supplied:**
- **Signing key impact:** what an attacker could do with a stolen `CI_SIGNING_KEY` depends on what it signs and who trusts those signatures. Neither is supplied. If it signs released artifacts, this could become a supply-chain compromise.
- **Token reach:** the packet says the author can't edit the protected default branch, but not whether branch protection also blocks this token. Within `contents: write`, writes to unprotected branches, tags and releases are plausible, but I haven't confirmed which rules apply. The token only works until the job ends.

I rated this High, not Critical, because the full reach of both credentials isn't established.

**Before vs. after:** BASE used `pull_request`, `contents: read` and no secret. Running the fork's code there was expected and exposed no privileged credentials, the same as the unchanged Tests workflow. HEAD introduces this whole problem.

**Fix (simplest):** go back to the BASE design: `on: pull_request`, `contents: read`, remove the `CI_SIGNING_KEY` env, and remove `ref` and `allow-unsafe-pr-checkout`.

**If a privileged step really is needed:**
- Run the untrusted check under `pull_request` with no secrets.
- Do signing in a separate trusted workflow, such as one triggered by `workflow_run` or by a push to the default branch. It should never check out or run code from the pull request, and should treat anything from it only as data.
- Scope any secret to the single step that needs it, not the whole job.
- Set `persist-credentials: false` where no token is needed.
- Use a protected environment with required reviewers for `CI_SIGNING_KEY`.

**Response if HEAD ever ran:** if HEAD ran on any fork pull request, treat `CI_SIGNING_KEY` as exposed. Revoke and rotate it, and check the repository for unexpected branches, tags or releases created by `github-actions`.

**How to verify the fix:** check statically that no `pull_request_target` or other privileged workflow both checks out the pull request's head and runs code from it. Also check that `CI_SIGNING_KEY` appears only in trusted workflows that never run pull-request code.

## Already present in BASE (not introduced by this change)

- **`app/export.py`: command injection. Severity: High. Confidence: High.**
  - **The problem:** `subprocess.check_output("render " + request.args["format"], shell=True)` passes the `format` query parameter to a shell with no validation. Per the packet, any self-registered logged-in user can reach this route.
  - **Impact:** a value like `x; <command>` runs arbitrary commands as the service user. `@require_login` only checks that someone is logged in, which anyone can do by registering.
  - **Fix:** check `format` against an allowlist and call `subprocess.run(["render", fmt], shell=False, check=True)`.
  - **Verify:** a test where a `format` value containing `;` is rejected and never reaches a shell.
  - This is unrelated to the workflow change, which doesn't touch or run this code.
- **`test.yml`:** this is not a finding. It runs submitted tests under `pull_request` with read-only access, no secrets and a fresh runner, which is its intended job per the packet.

## Coverage and limits

- **Reviewed:** the full diff, both unchanged context excerpts and every contract statement in the packet.
- **Not verified:**
  - The checkout action's actual behavior at the pinned SHA, taken from the packet as given.
  - The repository's real branch-protection, ruleset and tag-protection settings.
  - What `CI_SIGNING_KEY` grants and how long it stays valid.
  - The contents of `ci/check.py`, which doesn't matter here because the attacker controls it.
- **Runtime:** I did not reproduce anything at runtime and tested no credentials.
- **Overall risk:** HEAD adds a High-severity issue in the reviewed scope. The next step is to not merge HEAD as written, or to restructure it as described above.
