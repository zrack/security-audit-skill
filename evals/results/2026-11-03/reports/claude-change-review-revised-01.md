# Security Audit: `.github/workflows/verify.yml` (BASE → HEAD)

## Scope
- **Comparison:** the supplied synthetic BASE snapshot against the supplied synthetic HEAD snapshot in `review-packet.md`. BASE and HEAD are labels; there are no commit hashes and nothing was fetched.
- **Changed artifact:** `.github/workflows/verify.yml`, the only file in the diff.
- **Unchanged context:** `.github/workflows/test.yml` and `app/export.py` (the `/export` route). Both are identical in BASE and HEAD.
- **Method:** static inspection only. I relied on the packet's stated contracts for GitHub event semantics, repository settings, and how `actions/checkout` v7 behaves. Nothing was executed, no network was used, and no files were changed.

## Findings

| # | Severity | Confidence | Status | Location |
|---|---|---|---|---|
| 1 | High | High | **Introduced by this change** | `.github/workflows/verify.yml` (triggers, permissions, job `env`, checkout `with`) |
| 2 | High | High | **Pre-existing, not changed by this patch** | `app/export.py`, `/export` handler |

### 1. Code from fork pull requests runs with `CI_SIGNING_KEY` and a write-capable token (introduced)

**Evidence.** Four changes in HEAD combine:
- `pull_request:` → `pull_request_target:` runs the job in the base repository's trusted context, and that context receives repository secrets.
- `contents: read` → `contents: write` makes the `GITHUB_TOKEN` write-capable.
- A job-level `env: CI_SIGNING_KEY: ${{ secrets.CI_SIGNING_KEY }}` places the private secret in the environment of every step, including the `Check` step.
- The checkout now uses `ref: ${{ github.event.pull_request.head.sha }}` with `allow-unsafe-pr-checkout: true`. Per the packet, this turns off checkout v7's default refusal and checks out the fork's head SHA.

The `Check` step then runs `python ci/check.py`. That file comes from the attacker's checked-out commit, not from the protected default branch.

**Attack path.** An external contributor edits `ci/check.py` in their fork and opens a pull request. The packet says no approval gate or environment gate applies, so the job runs the attacker's script as the job user. That script can:
- read `CI_SIGNING_KEY` from its environment and send it anywhere;
- read the `contents: write` `GITHUB_TOKEN`. Checkout keeps it in a credentials file under `$RUNNER_TEMP`, referenced from Git config, until the job's post-job cleanup.

**Counterexample checked.** `pull_request_target` takes the workflow definition from the base branch, so the attacker cannot change `verify.yml` itself, and the contract says they cannot edit the protected default branch. That doesn't block the attack. The trusted workflow runs attacker-controlled code anyway, and nothing in the job stops it from reaching the secret or the token. Before this change, `pull_request` with `contents: read` and no secrets was safe for this script.

**Supported impact.**
- The private signing secret is exposed to any external pull-request author.
- Until the job's post-job cleanup, the attacker can perform repository write operations with the job's token, but not on the protected default branch.

**Why High and not Critical.** The secret's external privileges and lifetime are not supplied. The token is limited to the job's lifetime, and the default branch is protected. Anything beyond that depends on missing facts and stays conditional: forging signed artifacts or releases, or tampering with unprotected branches or tags.

**Fix.** The smallest effective correction is to revert `verify.yml` to the BASE trust model:
- trigger on `pull_request`;
- set `contents: read`;
- remove the job-level `CI_SIGNING_KEY`;
- remove `ref:` and `allow-unsafe-pr-checkout: true`.

If signing is needed, move it to a separate trusted workflow, for example one triggered by `workflow_run` or `push` on the default branch. That workflow should never check out or run pull-request code. Give the secret only to the specific step that needs it, and use `persist-credentials: false` where a token isn't needed.

If the HEAD version was ever merged and active, treat `CI_SIGNING_KEY` as exposed. Rotate it, and review recent Actions runs and repository write events.

**Verification.**
- Re-inspect the workflow statically. No job triggered by `pull_request_target` should check out the pull-request head or run repository scripts, and no job that runs pull-request code should have secrets or write permissions.
- Optionally, run a controlled test in a test repository: a fork pull request whose script only reports whether the variable is non-empty, never its value.

### 2. Shell command injection in `/export` (pre-existing)

**Evidence.** `subprocess.check_output("render " + request.args["format"], shell=True)` concatenates the request parameter into a shell command. The packet says there is no other input validation.

**Prerequisites and impact.** The attacker needs any ordinary self-registered account, which is a low barrier. A value like `x; <command>` runs arbitrary shell commands as the application's service user. Whether that reaches further data or systems depends on that user's access, which the packet doesn't describe.

**Status.** This is identical in BASE and HEAD. Neither workflow runs it, and this patch doesn't affect it, so it is not a regression from this change. It's still a real issue worth fixing separately.

**Fix.** Call the command without a shell, `subprocess.check_output(["render", fmt])`, and check `fmt` against an allowlist of supported formats. Reject anything else with a 400.

**Verification.** Add a unit test showing that a `format` containing `;`, `|`, `$()` or a leading `-` is rejected and never reaches `subprocess`.

## Not findings
- **`test.yml`:** it runs submitted tests under `pull_request` with `contents: read`, no secrets, and an ephemeral runner. Running untrusted test code is its intended job, and no sandbox escape is claimed. No issue.

## Coverage and limits
- I reviewed only the supplied diff and the two context excerpts, and took the packet's contracts on `actions/checkout` v7 and repository settings as given. I did no advisory lookup and didn't confirm the action's behavior against upstream sources.
- Nothing was validated at runtime: no workflow run, no exploit attempt, and the credential was not tested.
- These are unknown: the secret's privileges and lifetime, whether HEAD was ever merged and active, branch and tag protections other than the default branch's, and the service user's privileges.
- **Overall risk for the reviewed scope:** this change introduces a High-severity regression that exposes a secret to external contributors. It should not be merged as written.
