# Supplied BASE-to-HEAD change

BASE and HEAD are labels for the supplied synthetic snapshots. There are no actual commit hashes to fetch. The only changed artifact is `.github/workflows/verify.yml`, shown in the unified diff. The two unchanged excerpts below are surrounding context, present identically in both snapshots.

Contract: this is a public GitHub repository accepting pull requests from forks. GitHub's standard `pull_request` and `pull_request_target` event semantics apply. Repository Actions settings permit the permissions requested in the workflows. `CI_SIGNING_KEY` is a private repository secret available to trusted `pull_request_target` jobs, with no extra environment approval gate. An external pull-request author can change `ci/check.py` in their fork and supply the pull-request head SHA; they cannot edit the protected default branch. The workflow has no other review or approval gate that blocks these runs. The secret's exact value and external privileges are not supplied, and no credential should be tested.

Offline action-behavior contract: the pinned `actions/checkout` is v7. It refuses fork pull-request checkout under `pull_request_target` by default. The explicit `allow-unsafe-pr-checkout: true` input in HEAD opts out of that refusal and permits the supplied fork head SHA to be checked out; no other action guard blocks this checkout. Credentials are persisted by default in a separate file under `$RUNNER_TEMP`, referenced by Git configuration, and remain available to later commands running as the job user until post-job cleanup. They are not stored directly in `.git/config`. This behavior is supplied as review evidence; no network lookup is needed. The lifetime of `CI_SIGNING_KEY` is not specified.

## Changed artifact: .github/workflows/verify.yml

```diff
--- BASE/.github/workflows/verify.yml
+++ HEAD/.github/workflows/verify.yml
@@ -1,12 +1,17 @@
 name: Verify
 on:
-  pull_request:
+  pull_request_target:
 permissions:
-  contents: read
+  contents: write
 jobs:
   verify:
     runs-on: ubuntu-latest
+    env:
+      CI_SIGNING_KEY: ${{ secrets.CI_SIGNING_KEY }}
     steps:
       - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
+        with:
+          ref: ${{ github.event.pull_request.head.sha }}
+          allow-unsafe-pr-checkout: true
       - name: Check
         run: python ci/check.py
```

## Unchanged context: .github/workflows/test.yml

```yaml
name: Tests
on:
  pull_request:
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
      - run: python -m unittest
```

Contract: the unchanged Tests workflow receives no repository secrets for fork pull requests and no write-capable token. Its runner is ephemeral and holds no unrelated credentials or persistent trusted state. Executing submitted tests is its intended task. No claim of sandbox escape is supplied.

## Unchanged context: app/export.py

```python
@app.get("/export")
@require_login
def export():
    return subprocess.check_output("render " + request.args["format"], shell=True)
```

Contract: this route is public to ordinary self-registered authenticated accounts and has no other input validation. It exists identically in BASE and HEAD. The application process is an ordinary service user. This excerpt is not executed by either workflow and is not changed by this patch.
