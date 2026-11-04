One introduced finding: **High severity, High confidence**.

Compared the supplied synthetic **BASE → HEAD** diff for `.github/workflows/verify.yml`. BASE and HEAD are artifact labels, not fetched commits. Both unchanged excerpts were reviewed as context.

**1. Fork-controlled code executes with a repository secret and write credentials.**
Location: HEAD workflow lines 3–17, shown in the supplied `diff`.

HEAD changes the event to `pull_request_target`, grants `contents: write`, exposes `CI_SIGNING_KEY`, and checks out the fork’s head SHA before executing `python ci/check.py`. A fork author controls that script and therefore gains code execution with the secret in its environment.

The supplied checkout-v7 contract explicitly establishes reachability: `allow-unsafe-pr-checkout: true` disables the default refusal. The script can also access the persisted write-capable checkout credentials during the job. Those credentials reside in a separate `$RUNNER_TEMP` file referenced by Git configuration, rather than directly in `.git/config`.

This introduces exposure of the private key to attacker-controlled code and enables repository-content actions permitted by the token. External signing privileges, protected-branch bypass, and broader compromise are not established; they do not justify escalating this to Critical.

**Fix:** Run fork checks under `pull_request` with `contents: read`, no signing secret, and no unsafe checkout override. Keep privileged operations confined to trusted code. Disable credential persistence where unnecessary.

**Verification:** Statically trace checkout refs, executed scripts, inherited secrets, and effective token permissions to confirm that fork-controlled code cannot receive privileged credentials.

The unchanged context has different conclusions:

- **`app/export.py`: pre-existing command injection.** An ordinary authenticated user controls `format`, which is concatenated into a command executed with `shell=True`. This permits command execution as the service user, but exists identically in BASE and HEAD and has no supplied connection to either workflow. Replace shell concatenation with an argument list and validate allowed formats.
- **Tests workflow: no substantiated security finding under the supplied contract.** Executing submitted tests is intentional, with no repository secrets, write token, unrelated credentials, or persistent trusted state. No sandbox escape is established.

Validation was limited to static inspection of the supplied text and explicit contracts. No sample code, network access, dependency installation, credential testing, or file modification occurred. No runtime exploit or broader repository audit was performed. Correct the Verify workflow’s trust boundary before merging.
