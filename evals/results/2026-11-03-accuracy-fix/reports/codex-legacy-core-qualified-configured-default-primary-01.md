Reviewed only the supplied samples in `code-review-cases.md`; no immutable revision was supplied. This was static inspection only. No sample code execution, network access, dependency installation, or file modification occurred. Verification steps below are recommendations and were not run.

**Sample A — two substantiated findings**

1. **High severity · High confidence: shell command injection.** At `line 35`, attacker-controlled `hostname` is concatenated into a command executed with `shell=True`. The deployment contract permits self-registered accounts to reach this route. An authenticated attacker can execute commands with the application process’s privileges; those privileges and the breadth of accessible resources are not supplied.

   **Fix:** Pass a validated hostname as a separate argument with `shell=False`, rejecting option-like input. **Verify:** Test shell metacharacters and leading-hyphen inputs, confirming rejection or literal argument handling without shell interpretation.

2. **High severity · High confidence: cross-account invoice disclosure.** At `line 26`, the query selects solely by invoice ID and returns the row, including `bank_account`. Authentication does not check ownership, and the contract explicitly excludes downstream row or proxy guards. An authenticated user supplying another owner’s existing invoice ID receives its data. Discoverability of those IDs is not established.

   **Fix:** Include `owner_id = session["user_id"]` in the parameterized query. **Verify:** With two users, confirm each can retrieve their own invoice and receives no invoice data when requesting the other user’s ID.

**Sample B — no substantiated security findings in the reviewed scope**

- The invoice query binds both invoice ID and authenticated owner ID (`line 65`).
- DNS input is restricted and passed as a separate argument with `shell=False`; the supplied code does not support shell injection (`lines 73–76`).
- `DOCUMENTATION_KEY` is an explicit dummy value, not evidence of an exposed private credential.
- Wildcard CORS exposes only the public literal status response; sensitive-data disclosure is not established.

This conclusion accepts the explicit deployment guarantees at `lines 85–89`, including unforgeable sessions, secure/HttpOnly cookies, request and concurrency limits, restricted DNS egress, and no internal DNS records. Those guarantees were not independently validated. The result applies to these supplied samples, not a running application or broader repository.
