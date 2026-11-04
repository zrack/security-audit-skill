**One introduced finding: High severity, High confidence — fork-controlled code executes with a private secret and repository write credentials.**

HEAD `.github/workflows/verify.yml:3–17` switches to `pull_request_target`, grants `contents: write`, exposes `CI_SIGNING_KEY`, explicitly permits checkout of the fork’s head SHA, and executes its `ci/check.py`. A fork author can therefore read the secret and use the job’s write-capable credentials. The supplied contract establishes that no approval gate or remaining checkout guard blocks this path. See the `changed workflow`.

The pinned checkout v7’s default refusal is explicitly disabled. Its persisted credentials remain accessible to the job user through a separate `$RUNNER_TEMP` file referenced by Git configuration until cleanup; they are not stored directly in `.git/config`.

**Fix:** Restore fork verification to `pull_request`, read-only permissions, and secret-free execution. Remove the unsafe checkout override and keep privileged operations restricted to trusted code. Verify the revised event, checkout, permission, and secret paths together to ensure fork-controlled commands cannot receive privileged credentials.

The unchanged context has different conclusions:

- **`app/export.py`: pre-existing shell injection.** An ordinary self-registered account controls text concatenated into `shell=True`, permitting commands as the application service user. It exists identically in BASE and HEAD and is unrelated to workflow execution. See the `export excerpt and contract`.
- **Tests workflow:** No substantiated vulnerability under its supplied contract: executing submitted tests is intended, with no repository secrets, write-capable token, unrelated credentials, or persistent trusted state.

The actual comparison was the supplied synthetic BASE-to-HEAD diff plus both unchanged excerpts. No commits were fetched or full repository inspected. Validation was static only; no sample code, network requests, credential tests, installations, or file modifications occurred.

The packet says the signing key’s external privileges “are not supplied” and its lifetime “is not specified.” External signing impact, protected-branch bypass, and broader compromise remain unestablished.
