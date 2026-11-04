# Security review: `verify.yml` BASE → HEAD

## Scope

- **Target:** the synthetic BASE-to-HEAD change in `review-packet.md`. BASE and HEAD are labels for supplied snapshots, not commits, so there are no hashes to compare or fetch.
- **Compared:** the unified diff of `.github/workflows/verify.yml`, which is the only changed file.
- **Context only (same in BASE and HEAD):** `.github/workflows/test.yml` and `app/export.py`, plus the contracts that come with them.
- **Method:** static reading of `review-packet.md` only. I didn't run anything, use the network, install anything, look up advisories, test credentials, open other files or change any files. For `actions/checkout` v7, I relied on the behaviour contract in the packet and did not check it against upstream.

## Findings

| # | Severity | Confidence | Introduced? | Location |
|---|---|---|---|---|
| 1 | High | High | **Yes, by this change** | `.github/workflows/verify.yml` (diff lines `pull_request_target`, `contents: write`, `env: CI_SIGNING_KEY`, `ref:` / `allow-unsafe-pr-checkout`) |
| 2 | High | High | No, already in BASE | `app/export.py`, `export()` |

### 1. Fork PR code runs with the signing secret and a write token (introduced)

**Evidence.** HEAD makes four changes that together create the problem:

1. The trigger changes from `pull_request` to `pull_request_target`. That means the job runs in the base repository's trusted context, where `CI_SIGNING_KEY` is available. The packet says there is "no extra environment approval gate" and "no other review or approval gate."
2. `permissions` changes from `contents: read` to `contents: write`.
3. `CI_SIGNING_KEY: ${{ secrets.CI_SIGNING_KEY }}` is set as a **job-level** `env`, so every step in the job gets it.
4. Checkout now uses `ref: ${{ github.event.pull_request.head.sha }}` with `allow-unsafe-pr-checkout: true`. The packet says this switches off v7's refusal to check out fork code and that "no other action guard blocks this checkout."

The next step runs `python ci/check.py`. The packet says an external PR author "can change `ci/check.py` in their fork," so the job runs code the attacker wrote.

**Impact.** An unauthenticated outsider who opens a PR from a fork gets to run code in the trusted job. That code can:

- **Read `CI_SIGNING_KEY` from its environment and send it out.** What the key can do outside CI, and how long it stays valid, is "not supplied" / "not specified." So the theft itself is established, but what an attacker can sign with it is not.
- **Use the `contents: write` `GITHUB_TOKEN`.** checkout persists it in a file under `$RUNNER_TEMP` that Git config points to, and later commands running as the job user can read it until post-job cleanup. It is **not** stored in `.git/config`. With it, the attacker can write repository contents within whatever that token is allowed to do. The packet says the PR author "cannot edit the protected default branch." It does not say whether branch protection also blocks this token, so I have not assumed the default branch can be modified.

**Timing.** Under standard `pull_request_target` semantics, GitHub uses the workflow file from the base branch. So this becomes exploitable once HEAD is merged into the default branch. After that, any fork PR can trigger it.

**Why High and not Critical.** The theft of a private secret and the use of a write-capable token by an outsider, with no approval step, are directly supported. Calling it Critical would depend on facts the packet leaves out: what the signing key is trusted for, how long it lives, and whether the token gets past branch protection.

**Fix (smallest effective change).**
- Go back to `on: pull_request` and `contents: read`, and remove the job-level `CI_SIGNING_KEY`, the `ref:` override and `allow-unsafe-pr-checkout: true`.
- If signing is genuinely needed, split it out. Run the untrusted checks under `pull_request` with no secrets. Do the signing in a separate trusted job (for example `workflow_run`, or one gated by an environment that needs approval) that never checks out or runs PR-controlled code. Give that job the secret at step level only, use `persist-credentials: false`, and keep permissions to the minimum.
- If HEAD was ever live on a default branch that took fork PRs, rotate `CI_SIGNING_KEY` and review the repository writes and runs from that period. Moving the secret somewhere else does not fix an exposure that already happened.

**Verification.** Check the workflow statically: no `pull_request_target` job checks out `github.event.pull_request.head.*` or runs repository scripts, and no job that runs PR code has secrets or write permissions. Optionally, open a PR from a test fork that edits `ci/check.py`. It should run without the secret and with a read-only token.

### 2. Command injection in `/export` (already in BASE, not introduced)

**Evidence.** `subprocess.check_output("render " + request.args["format"], shell=True)`. Per the packet, the route is reachable by "ordinary self-registered authenticated accounts," has "no other input validation," and runs as "an ordinary service user."

**Impact.** Any account that signs itself up can inject shell syntax through `format` (for example with `;` or `$(...)`) and run commands as the service user. That proves code execution under that user's privileges. It does not prove access to every application resource or data store; that depends on what the service user can reach, which the packet doesn't say. Severity is High.

This has nothing to do with the workflow change. Neither workflow runs this code and the patch doesn't touch it.

**Fix.** Drop `shell=True` and pass a list of arguments: `subprocess.check_output(["render", fmt])`. Also check `fmt` against an allowlist of supported formats.

**Verification.** Add a unit test that sends `format=pdf;id` (and a `$(...)` variant) and asserts the request is rejected and no shell is invoked.

## Not a finding

`.github/workflows/test.yml` runs PR-submitted tests under `pull_request`. Per its contract, it gets no secrets and no write-capable token on fork PRs, its runner is ephemeral, and running submitted tests is what it's for. No issue is supported. It is also the safe pattern that `verify.yml` dropped.

## Coverage and limits

- **Not verified:** `actions/checkout` v7 behaviour and the GitHub event semantics come only from the supplied contracts. The pinned SHA `3d3c42e…` and any advisories were not checked online.
- **Unknown:** what `CI_SIGNING_KEY` can do and how long it lasts, whether `GITHUB_TOKEN` writes get past branch protection, and the deployment exposure of `/export`. These affect how far the impact reaches, not whether each finding is real.
- **No runtime validation:** every conclusion comes from static analysis of the packet.
- **Overall risk:** the change introduces one High-severity issue (finding 1) and should not be merged as written. Finding 2 is a separate, existing High issue to fix on its own. I have not rated the application as a whole.

**Next step:** block or revert the HEAD `verify.yml` change before it reaches the default branch. Track the `/export` injection separately.
