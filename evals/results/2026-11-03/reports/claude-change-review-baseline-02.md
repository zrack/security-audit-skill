# Security review: `.github/workflows/verify.yml` (BASE → HEAD)

The change lets anyone who opens a pull request from a fork run their own code while holding the repository's private signing key and a token that can write to the repository. This is new in HEAD and rated **High**. Separately, `app/export.py` has a command injection that was already there before this change.

## Scope
- **What was compared:** the synthetic BASE and HEAD snapshots in `review-packet.md`. They are labels, not real commits, and no hashes exist. The only changed file is `.github/workflows/verify.yml`.
- **Context read but unchanged:** `.github/workflows/test.yml` and `app/export.py`, which are identical in BASE and HEAD.
- **Facts taken from the packet, not checked independently:** how `actions/checkout` v7 behaves, the repository settings, and what an outside contributor can do.
- **Method:** I only read the packet. I ran nothing, used no network, opened no other files and changed nothing.

## Findings

### 1. Fork pull request code runs with the signing key and a write token (new in HEAD)
**Severity:** High · **Confidence:** High · **Location:** `.github/workflows/verify.yml`, diff lines 18–33

**Evidence.** HEAD combines four changes that together make the job unsafe:
- The trigger moves from `pull_request` to `pull_request_target`. That event runs in the base repository's trusted context, where repository secrets are available.
- `permissions` changes from `contents: read` to `contents: write`.
- The job's environment now includes `CI_SIGNING_KEY: ${{ secrets.CI_SIGNING_KEY }}`.
- The checkout step now uses `ref: ${{ github.event.pull_request.head.sha }}` with `allow-unsafe-pr-checkout: true`. That setting turns off the action's default refusal to check out fork code under this event.

The job then runs `python ci/check.py` from the checked-out fork commit.

**How an attacker uses it.** An outside contributor changes `ci/check.py` in their fork and opens a pull request. The packet says there is no approval gate and no environment protection. Their script then runs as the job user, and it can:
- read `CI_SIGNING_KEY` from the environment and send it out;
- read the write-capable token that checkout saves in a file under `$RUNNER_TEMP`. Per the packet, it stays available to later commands until post-job cleanup.

**Impact we can confirm.**
- The private repository secret is exposed to any GitHub user.
- The attacker can make contents-write changes to the repository for as long as the job's token is valid.
- Branch protection on the default branch still blocks writes there. The packet doesn't say what protects other branches, tags or releases.

**Why High and not Critical.** The packet doesn't say what the signing key can sign or how long it stays valid. Treat this as Critical if the key signs releases or artifacts that users trust.

**BASE comparison.** In BASE, fork pull requests ran without secrets and with a read-only token. This is a new problem, not an existing one.

**Fix (smallest effective change):** go back to `on: pull_request` with `permissions: contents: read`, and take `CI_SIGNING_KEY` out of the job. If a trusted step really needs the key:
- put it in a separate workflow that never checks out or runs pull request code (for example `workflow_run` acting only on reviewed outputs, or one triggered after merge);
- protect that workflow with an environment that requires reviewers;
- set `persist-credentials: false` on checkout.

If this HEAD was ever run against a fork pull request, rotate `CI_SIGNING_KEY` and audit repository writes made during those runs.

**How to verify the fix:** check the final workflow statically. No job triggered by `pull_request_target` should check out `github.event.pull_request.head.*` or run repository scripts, and no fork-triggered job should receive secrets or `contents: write`. Then open a test pull request from a fork whose `ci/check.py` only prints whether `CI_SIGNING_KEY` is set. It should report that it isn't.

### 2. Command injection in the `/export` route (was already there, not changed by this patch)
**Severity:** High · **Confidence:** High · **Location:** `app/export.py`, the `export()` handler

**Evidence.** The handler passes `"render " + request.args["format"]` to `subprocess.check_output(..., shell=True)`. Per the packet, any self-registered account can reach the route and there is no other input validation.

**Impact.** A request such as `format=x;id` runs arbitrary shell commands as the application's ordinary service user. This is limited to that user's privileges; nothing in the packet shows wider access to the host.

**Fix:** avoid the shell entirely. Check `format` against an allowlist of known values and call `subprocess.check_output(["render", fmt])` without `shell=True`.

**How to verify the fix:** add a test confirming that `format=pdf;id` is rejected and doesn't run `id`.

## Checked and not a finding
- **`.github/workflows/test.yml`:** it runs code submitted in pull requests, but under `pull_request`. Per the packet, it has no secrets and no write token for forks, and its runner is ephemeral. Running submitted tests is its intended job, so there is nothing to report.

## Coverage and limits
- I relied on the packet's descriptions of how `actions/checkout` v7 and GitHub's events behave. I didn't look up the pinned commit's source or any advisories.
- These facts were not available: what the signing key can do and how long it is valid, the protection rules on refs other than the default branch, and how the export route's environment is deployed. These limit how far the severity ratings can go.
- I didn't test any credential and didn't run any code.
- **Overall risk:** HEAD is not safe to merge as written; this rating covers only the files in the packet.
