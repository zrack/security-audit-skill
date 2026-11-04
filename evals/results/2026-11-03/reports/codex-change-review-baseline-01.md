**One introduced finding: High severity, High confidence — privileged workflow executes fork-controlled code.**

Location: `.github/workflows/verify.yml`, HEAD lines 3–16; `supplied diff`.

HEAD changes the event to `pull_request_target`, grants `contents: write`, exposes `CI_SIGNING_KEY`, and explicitly checks out the PR head before running `python ci/check.py`. Under the supplied contract, an external fork author can replace that script and trigger execution without an approval gate.

The script can read and disclose the private signing key. The write-capable repository token also enables unauthorized repository writes through checkout’s normal persisted credentials. Default-branch protection does not prevent execution of the submitted script. The signing key’s external privileges and broader compromise are unknown.

**Fix:** Run fork verification under `pull_request` with `contents: read` and no private secrets. Isolate signing or repository writes from PR-controlled executable content. Verify that every path executing fork code receives neither private secrets nor write credentials.

The unchanged context has different conclusions:

- `test.yml`: No substantiated issue under its supplied read-only, secret-free, ephemeral-runner contract. Executing submitted tests is intentional.
- `app/export.py`: Contains **pre-existing authenticated shell-command injection** through `format` and `shell=True`. Its supported execution boundary is the application service user. It is identical in BASE and HEAD and unrelated to either workflow.

The actual comparison was the **supplied synthetic BASE-to-HEAD diff**, plus both unchanged excerpts and all supplied contracts. No commits were fetched or compared. Validation was static inspection only: no sample execution, network access, dependency installation, credential testing, unrelated-file inspection, or file modification. The pinned checkout implementation and live Actions behavior were not independently validated.
