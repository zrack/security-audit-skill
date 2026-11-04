I read the supplied packet `review-packet.md` and nothing else. I didn't run, fetch or change anything.

## Scope

- **Comparison:** BASE → HEAD of `.github/workflows/verify.yml`, using the unified diff in the packet. These are synthetic snapshots with no commit hashes, so I didn't look at or fetch any git history.
- **Unchanged context, same in BASE and HEAD:** `.github/workflows/test.yml` and `app/export.py`.
- **Method:** I read the code statically against the contracts in the packet. Those contracts cover GitHub event semantics, how the pinned checkout v7 behaves, and the attacker's capabilities. I took them as given and didn't check them against GitHub's documentation or the action's source.

## Findings

### 1. Introduced: fork pull requests run attacker code with a write token and the signing secret (High, confidence High)

**Location:** `.github/workflows/verify.yml`, the HEAD side of the diff (lines 18, 21, 25–26 and 29–31 of the packet).

**What the change does:**
- **Trigger:** `pull_request` becomes `pull_request_target`, so fork pull requests now run in the base repository's trusted context.
- **Token:** `permissions: contents: read` becomes `contents: write`, so the job's `GITHUB_TOKEN` can write repository contents.
- **Secret:** `CI_SIGNING_KEY: ${{ secrets.CI_SIGNING_KEY }}` is set as a job-level environment variable. The packet says the secret is available to these jobs "with no extra environment approval gate."
- **Checkout:** `ref: ${{ github.event.pull_request.head.sha }}` and `allow-unsafe-pr-checkout: true` check out the fork's head commit. The packet says this flag turns off v7's default refusal and that "no other action guard blocks this checkout."
- **Execution:** `run: python ci/check.py` then runs the fork's version of `ci/check.py`, which the packet says an external author can change.

**What an attacker gets:** any external user can open a fork pull request with a modified `ci/check.py`, and that code runs with:
- `CI_SIGNING_KEY` in its environment, so it can read and send out the private signing key;
- the write-scoped `GITHUB_TOKEN`, which checkout stores by default in a file under `$RUNNER_TEMP`. The packet says it stays "available to later commands running as the job user until post-job cleanup."

The packet also says "The workflow has no other review or approval gate that blocks these runs," so opening the pull request is the only thing the attacker needs to do.

**Limits on the consequence:**
- **Default branch:** the attacker "cannot edit the protected default branch," so I don't claim the token can push to it.
- **Other targets:** whether the token can reach other branches, tags or releases depends on protections the packet doesn't describe.
- **Signing key:** its value, what it can sign, and how long it stays valid are "not supplied" or "not specified." Exposure of the key is confirmed; what it lets the attacker do after that is still open.

**Fix (smallest effective change):** go back to `pull_request` with `contents: read`, and remove `CI_SIGNING_KEY` from this job. If `pull_request_target` really is needed:
- never check out or run the pull request's code in that job;
- drop `allow-unsafe-pr-checkout`;
- move any signing into a separate job that only runs on trusted refs, such as pushes to the protected branch, ideally behind an environment that requires approval;
- set `persist-credentials: false` on checkout and keep `permissions` to the minimum.

The secret was only ever present in the HEAD snapshot. If HEAD was ever merged and run, rotate `CI_SIGNING_KEY` and check recent workflow runs and signed artifacts.

**How to check the fix:** read the fixed workflow again and confirm that, in any job triggered by `pull_request_target` or holding secrets:
- no step checks out `github.event.pull_request.head.*`;
- no step runs code from the repository's working tree.

Then open a test pull request from a fork whose `ci/check.py` prints which environment variables exist (names only). It should show no secret and only a read-only token.

### 2. Already in BASE, not introduced: shell command injection in `/export` (High, confidence High)

**Location:** `app/export.py`, `export()`, which runs `subprocess.check_output("render " + request.args["format"], shell=True)`.

**What happens:** the `format` parameter goes into a shell command line without any validation. The packet says the route is open to "ordinary self-registered authenticated accounts" and has "no other input validation." So any user who signs up can run shell commands as the application's service user, for example with `format=x;id`. What that service user can reach beyond that is not established.

**Not caused by this change:** the packet says this code exists unchanged in BASE and HEAD, and neither workflow runs it.

**Fix:** pass arguments as a list without a shell, for example `subprocess.check_output(["render", fmt])`, and check `fmt` against an allowlist of supported formats.

**How to check the fix:** a unit test that sends `format=pdf;touch /tmp/x` should be rejected, and nothing should run.

## Not findings

**`.github/workflows/test.yml`** (unchanged): it runs code submitted in the pull request, but under `pull_request` with `contents: read`. The packet says it gets no secrets and no write-capable token on fork pull requests and runs on an ephemeral runner. Running submitted tests there is its intended job, so there's no security failure to report.

## Coverage and limits

- **Static only.** Nothing ran: no workflows, no Python, no network calls, no attempts to use credentials.
- **Taken from the packet without checking:** how `actions/checkout` at the pinned SHA behaves, and GitHub's event semantics.
- **Not reviewed:**
  - the contents of `ci/check.py`, which doesn't matter because the attacker controls it;
  - branch, tag and release protections other than the default branch;
  - the privileges and lifetime of `CI_SIGNING_KEY`;
  - the rest of the application around `/export`.
- **Overall risk for this change:** High, because it adds a direct path for any fork contributor to steal the secret and get a write-scoped token. I'm not rating the repository or the application as a whole.

**Next step:** don't merge HEAD's `verify.yml` as written. If it has already run on any fork pull request, rotate `CI_SIGNING_KEY`. Fix the `/export` injection separately, since it was already there before this change.
