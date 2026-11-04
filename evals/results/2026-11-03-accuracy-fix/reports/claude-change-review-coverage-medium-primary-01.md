# Security review: `verify.yml`, BASE to HEAD

## Scope
- **What I compared:** the supplied BASE and HEAD snapshots in `review-packet.md`. These are synthetic labels, so there were no commits or hashes to check. The only file that changed is `.github/workflows/verify.yml`.
- **Context files:** `.github/workflows/test.yml` and `app/export.py`. Both are identical in BASE and HEAD, so I read them only to separate new issues from old ones.
- **Method:** I only read the code. I ran nothing, used no network, installed nothing, did no advisory lookup, and edited no files. For how `actions/checkout` v7 behaves, I relied on the contract supplied in the packet.

## Findings introduced by this change

### 1. A fork pull request can run its own code with the signing key and a write token — **High**, confidence **High**

**Where:** `.github/workflows/verify.yml`. The trigger changed to `pull_request_target`, the permissions changed to `contents: write`, and the job now has `env: CI_SIGNING_KEY`. The checkout step now uses `ref: ${{ github.event.pull_request.head.sha }}` with `allow-unsafe-pr-checkout: true`, and is followed by `run: python ci/check.py`.

**How it works:**
1. `pull_request_target` runs in the trusted context of the base repository. According to the contract, that gives the job `CI_SIGNING_KEY` with no environment approval gate. The job also gets a `GITHUB_TOKEN` with `contents: write`, and the repository settings allow that.
2. The checkout step fetches the fork's head SHA. The new `allow-unsafe-pr-checkout: true` input switches off the guard that would otherwise refuse that checkout, and the contract says no other guard blocks it.
3. `python ci/check.py` then runs the version of that file from the fork. The packet says an external author can change it.
4. That code runs as the job user. It can read `CI_SIGNING_KEY` because the variable is set for the whole job. It can also read the write-capable token, which checkout saves by default in a file under `$RUNNER_TEMP`. That file is referenced by Git config and stays readable until post-job cleanup.

**Who can trigger it:** anyone who opens a pull request from a fork. The packet says it is a public repository that accepts fork PRs, and that "no other review or approval gate" blocks these runs.

**What this gives an attacker:**
- They can read and send out the private `CI_SIGNING_KEY`.
- They can use a token with repository `contents: write` for as long as the job runs.

Two consequences are not established by the packet:
- **What the key can sign:** the packet says the key's value and external privileges are "not supplied", and that its lifetime "is not specified".
- **Which branches or tags the token can write:** the packet says the external author cannot edit the protected default branch. Whether this job token can get around that protection depends on branch-protection rules the packet doesn't include.

I rated this High rather than Critical because how far the damage reaches depends on those two unknowns.

**In BASE:** the workflow used `pull_request` with `contents: read`, had no secret, and used the default checkout. Fork code ran without secrets or write access, just like `test.yml`. This whole problem is new in HEAD.

**Fix:**
- **Simplest:** revert to `pull_request` with `contents: read`, and drop the `CI_SIGNING_KEY` env, the `ref` override and `allow-unsafe-pr-checkout`.
- **If signing really has to happen for PRs:** split it into two workflows.
  - One runs the untrusted code under `pull_request`, with no secrets.
  - A separate privileged workflow (`workflow_run`, or `pull_request_target` without checking out PR code) treats the first one's outputs strictly as data. Give that job only the step-level permissions and secret it needs, and use `persist-credentials: false`.
- **If HEAD has ever run on any fork PR:** rotate `CI_SIGNING_KEY` and review recent pushes, tags and releases.

**How to check the fix:** confirm that no job triggered by `pull_request_target` checks out or runs code from the PR head. Confirm that `CI_SIGNING_KEY` and write permissions only appear in jobs that run trusted base-branch code.

## Pre-existing issue (not introduced)

### Shell command injection in `app/export.py` — **High**, confidence **High**

**Where:** the `export()` handler builds a shell command from a query parameter: `subprocess.check_output("render " + request.args["format"], shell=True)`. The packet says it exists "identically in BASE and HEAD", and neither workflow runs it.

**Who can exploit it:** any ordinary self-registered, logged-in account. The packet says the route has "no other input validation".

**Impact:** shell metacharacters in `format` let the caller run any command as the application's service user. The output also comes back in the HTTP response.

**Fix:**
- Use argument-list form without a shell, for example `subprocess.check_output(["render", fmt])`.
- Check `fmt` against an allowlist of supported formats.

**How to check the fix:** send a `format` value such as `pdf;id` and confirm it is rejected or passed to `render` as a single literal argument.

## Not a finding
- `test.yml` runs fork-submitted tests under `pull_request`. The contract says it gets no secrets and no write token, runs on an ephemeral runner, and that running submitted tests "is its intended task". This change doesn't touch it.

## Limits
- I didn't check that SHA `3d3c42e5…` really is `actions/checkout` v7, or how that action really behaves. I used the supplied contract.
- These are unknown, and they decide how serious finding 1 really is:
  - What `CI_SIGNING_KEY` can sign, and how long it stays valid.
  - Which branch-protection and tag-protection rules apply to `GITHUB_TOKEN` pushes.
  - Whether HEAD has already run in a real repository.
- I didn't look at the contents of `ci/check.py`. Since a fork author controls that file, its contents don't change finding 1.
- I didn't rate the overall risk of the application, because this review only covered a narrow slice of it.
