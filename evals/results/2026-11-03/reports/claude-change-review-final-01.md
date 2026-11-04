# Security review: `verify.yml`, BASE to HEAD

## Scope
- **What I compared:** the synthetic BASE and HEAD snapshots in `review-packet.md`. BASE and HEAD are labels only; I fetched no commits. The only changed file is `.github/workflows/verify.yml`, which I reviewed from the unified diff. `test.yml` and `app/export.py` are unchanged context, identical in both snapshots.
- **How:** I only read the code. I didn't run anything, use the network, install anything, or change any files. I took the action and repository behavior from the packet's stated contracts, not from GitHub's documentation or a live run.

## Findings

| # | Severity | Confidence | Status | Location |
|---|---|---|---|---|
| 1 | High | High | **Introduced by this change** | `.github/workflows/verify.yml` (HEAD lines 3, 5, 9–10, 13–15, 17) |
| 2 | High | High | **Already present (not changed by this patch)** | `app/export.py`, `export()` |

### 1. Fork pull requests run their own code with the signing key and a write-capable token (introduced)

**What the change does.** All four of these are new in HEAD:
- **Trigger:** changed from `pull_request` to `pull_request_target` (line 3), so fork PRs now run with base-repository privileges.
- **Token:** `contents: read` became `contents: write` (line 5).
- **Secret:** `CI_SIGNING_KEY: ${{ secrets.CI_SIGNING_KEY }}` is set at job level (lines 9–10), so every step sees it.
- **Checkout:** `actions/checkout` now checks out `github.event.pull_request.head.sha` with `allow-unsafe-pr-checkout: true` (lines 13–15). The packet says this switches off v7's refusal to check out fork code and that nothing else blocks it.

Then `python ci/check.py` runs (line 17). That file comes from the PR author's fork.

**How it gets exploited.** An outside contributor edits `ci/check.py` in their fork and opens a PR. Per the packet, nothing reviews or approves the run first. Their script then runs as the job user and can:
- Read `CI_SIGNING_KEY` from the environment and send it out of the runner. The secret is disclosed outright.
- Read the persisted `contents: write` token. The packet says it sits in a file under `$RUNNER_TEMP` that the job user can read until post-job cleanup. With it, the attacker can write repository contents the token allows. The packet rules out the protected default branch, but other branches and tags aren't ruled out.

**Why High, not Critical.** Disclosing a private signing key and getting write access to the repository from an anonymous fork PR is a serious compromise with almost no barriers. I don't rate it Critical because the packet doesn't say what the key can sign, how long it stays valid, or what else it grants, and it rules out writes to the default branch. Anything the key could be used for later, such as signing malicious artifacts, depends on facts the packet doesn't supply.

**What was already there.** BASE ran the same untrusted `ci/check.py` under `pull_request` with a read-only token and no secret. That matches the accepted model for `test.yml`. The risk comes entirely from adding privileges to a job that still runs untrusted code.

**Fix (smallest effective change):**
1. Revert to `on: pull_request` and `permissions: contents: read`. Remove the `CI_SIGNING_KEY` env entry and the `ref`/`allow-unsafe-pr-checkout` inputs.
2. If a later step really needs the key, run it in a separate trusted job. For example, a `workflow_run` job or a job after merge on the default branch. That job must never check out or execute PR-supplied code, should scope the secret to a single step, and should use `persist-credentials: false` with the minimum permissions.
3. If this HEAD workflow has ever run on a fork PR, rotate `CI_SIGNING_KEY`. Then check for unexpected branches, tags or releases created by the workflow token.

**How to verify the fix:**
- Read the final workflow and confirm that no job combines all three: a privileged trigger, a secret or write token, and fork-controlled code.
- Optionally, open a test fork PR that changes `ci/check.py` to print whether `CI_SIGNING_KEY` is set and to try a write with the token. Do this only in an authorized test repository, never with the real secret value. Expect the variable to be absent and the write to fail.

### 2. Command injection in the `/export` route (already present, not introduced)

**The code.** `subprocess.check_output("render " + request.args["format"], shell=True)` builds a shell command string straight from the request.

**Who can exploit it.** The packet says any self-registered, logged-in account can reach this route, with no other input validation. Such a user can pass shell metacharacters in `format`, for example a `;` followed by another command. That runs arbitrary commands as the application's service user. The packet doesn't say what that user can reach, so the impact beyond that is unknown.

**The change doesn't affect it.** This code is identical in BASE and HEAD, and neither workflow runs it. I'm listing it as a separate existing problem, not something this change introduced.

**Fix:** pass an argument list with no shell, and accept only a fixed set of formats:

```python
ALLOWED = {"pdf", "csv"}
fmt = request.args.get("format")
if fmt not in ALLOWED:
    abort(400)
return subprocess.check_output(["render", fmt])
```

**How to verify the fix:** add a test that requests `format=pdf;id` and expects a 400 response with no subprocess call.

## Not a finding
- **`test.yml`:** it runs submitted tests under `pull_request` with a read-only token, no secrets, and a throwaway runner. Per the packet, that is its intended purpose, so nothing crosses a trust boundary.

## Coverage and limits
- **What I covered:** the full diff plus both pieces of supplied context.
- **What I relied on without checking:** the packet's statements about how `actions/checkout` v7 and `allow-unsafe-pr-checkout` behave, and that no approval gates exist. I didn't look up the pinned SHA, GitHub documentation or advisories.
- **What is unknown:** the signing key's capabilities and lifetime, and what branch or tag protection exists beyond the default branch.
- **Not reviewed:** the contents of `ci/check.py`. It doesn't matter here because a fork author can replace it anyway.
- **Overall risk of the change:** High. It introduces a fork-PR path to the secret and the write token.

**Next step:** don't merge HEAD as written. Revert the four privilege changes in `verify.yml` (fix 1, step 1). If HEAD has already run on any fork PR, rotate `CI_SIGNING_KEY`.
