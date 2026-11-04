# Security review: `verify.yml` change (BASE → HEAD)

## Scope
- **What was compared:** the synthetic BASE and HEAD snapshots in `review-packet.md`. They are labels, not real commits, so there was nothing to fetch and no hashes exist.
- **Changed file:** `.github/workflows/verify.yml`, the only file in the diff. Line numbers below are HEAD-file lines worked out from the `+1,16` hunk.
- **Unchanged context:** `.github/workflows/test.yml` and `app/export.py`. The packet says both are identical in BASE and HEAD.
- **Method:** I read the code and the packet's stated assumptions. I didn't run any code, use the network, install anything, test any credential or change any file.

## Findings

### 1. Critical: the workflow runs fork pull-request code while it holds a private secret and a write token (introduced by this change)
**Confidence:** High
**Location:** `.github/workflows/verify.yml`, lines 3, 5, 9–10, 13–14 and 16 (HEAD)

**Evidence:** In BASE these pieces were safe. Together in HEAD they let an outside contributor run their own code with the repository's privileges:
- **Line 3:** the trigger changes from `pull_request` to `pull_request_target`. Under GitHub's rules, `pull_request_target` runs in the base repository's context, with its secrets and a token that can write, even when the pull request comes from a fork.
- **Line 5:** the token's permission goes from `contents: read` to `contents: write`.
- **Lines 9–10:** `CI_SIGNING_KEY` is put into the job's environment, so every step can read it, including the step that runs the contributor's code.
- **Lines 13–14:** the checkout uses `ref: ${{ github.event.pull_request.head.sha }}`. That checks out the pull-request author's code instead of the trusted base branch.
- **Line 16:** `python ci/check.py` then runs that checked-out file. The packet says an outside author can change `ci/check.py` in their fork.
- `actions/checkout` keeps the job token in `.git/config` by default, because `persist-credentials` is not turned off here. So the token can also be read from disk.

**How an attack works:** No approval is needed, and the packet says no other gate blocks these runs. Anyone with a GitHub account can open a fork pull request whose `ci/check.py`:
- reads `CI_SIGNING_KEY` and sends it out, or
- uses the write-capable token while the job runs.

**Supported impact:**
- **Proven:** the private signing key is disclosed to an untrusted party.
- **Proven:** an attacker can run code with a `contents: write` token for the repository.
- **Conditional:** what the key unlocks after it leaks is not stated in the packet. Branch protection may stop the token from pushing to the default branch. It does not, on the evidence given, stop writes to other branches, tags or releases.

**Why Critical rather than High:** the attacker needs nothing but a GitHub account, there is no approval step, and the attack gives both a long-lived secret and repository write access.

**Fix (smallest effective):**
1. Revert to `on: pull_request` with `permissions: contents: read`, and remove the `CI_SIGNING_KEY` env entry. That is exactly BASE.
2. If signing really needs the secret, split the work:
   - an untrusted `pull_request` job that runs `check.py` with no secrets, and
   - a separate trusted job, for example one triggered by `workflow_run` or by a push to the protected branch, that never checks out or runs pull-request code.
3. In any job triggered by `pull_request_target`:
   - never check out `head.sha` or `head.ref`;
   - set `persist-credentials: false`;
   - give the secret only to the single step that needs it.
4. If HEAD was ever merged or triggered, rotate `CI_SIGNING_KEY` and review the repository for unexpected branches, tags or releases. Moving the secret elsewhere doesn't undo a leak that already happened.

**How to check the fix:**
- Re-read the workflow and confirm there is no `pull_request_target` combined with a pull-request-head checkout, and no secret or write permission in any job that runs pull-request code.
- Optionally, run a workflow linter such as actionlint or zizmor, which flag this pattern.
- In a test fork, open a pull request whose `check.py` only prints whether `CI_SIGNING_KEY` is set (not its value). Confirm it is unset and that the token is read-only.

## Issue that was already there (not introduced by this change)

### 2. High: command injection in `/export` (`app/export.py`)
**Confidence:** High

**Evidence:**
- `subprocess.check_output("render " + request.args["format"], shell=True)` passes the `format` value straight into a shell command.
- Any self-registered logged-in account can reach this route, and the packet says there is no other input validation.
- So a value like `x; <command>` runs a shell command as the application's service user. The supported boundary is that service user, not the whole machine.

This code is identical in BASE and HEAD, and neither workflow runs it, so the change neither causes nor worsens it.

**Fix:**
- Accept `format` only from a fixed allowlist.
- Call `subprocess.run(["render", fmt], check=True, capture_output=True)` with no `shell=True`.

**How to check the fix:** test that a `format` value containing `;` or `$(...)` is rejected.

## Not a finding
`test.yml` runs submitted tests under `pull_request` with `contents: read` and no secrets, on a short-lived runner. That is its stated purpose, and nothing in the packet shows it crossing a trust boundary.

## Coverage and limits
- **Coverage:** I only reviewed the three supplied excerpts. Anything not in the packet (repository Actions settings, branch protection details, other workflows, the contents of `ci/check.py`) I took from the packet's descriptions rather than checking myself.
- **No runtime check:** everything here comes from reading the code plus GitHub's documented event behaviour. Nothing was confirmed by running it.
- **Not checked:** the privileges of `CI_SIGNING_KEY` and the pinned `actions/checkout` commit. I didn't look up advisories for that commit.
- **Overall risk:** Critical for the reviewed change. I'm not rating the wider application.

**Next action:** don't merge HEAD as written. Restore the BASE trigger and permissions, or use the split-job design above.
