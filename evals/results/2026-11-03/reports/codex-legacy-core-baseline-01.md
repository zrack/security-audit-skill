Reviewed only `code-review-cases.md` using static inspection. No revision was supplied; locations below refer to packet lines.

**Sample A — two substantiated findings**

1. **High severity · High confidence — OS command injection.** At `lines 34–35`, attacker-controlled `hostname` is concatenated into a command executed with `shell=True`. Any self-registered account can reach this route and introduce shell commands running with the application process’s privileges. Elevated privileges or whole-machine compromise are not established.

   **Fix:** use an argument list with `shell=False` and hostname validation, as Sample B does. **Verification, not performed:** confirm shell syntax is rejected and accepted input remains one subprocess argument.

2. **High severity · High confidence — cross-account invoice disclosure.** At `lines 26–29`, the query selects invoices by ID without checking ownership, then returns fields including `bank_account`. An authenticated user who supplies another owner’s existing invoice ID can access that invoice. The supplied contract explicitly rules out an external authorization guard. SQL parameterization prevents injection but does not enforce ownership.

   **Fix:** bind `owner_id` to `session["user_id"]` in the query, as Sample B does. **Verification, not performed:** use two accounts to confirm owners can retrieve their invoices and other accounts receive 404.

**Sample B — no substantiated security findings in the reviewed scope**

The supplied evidence addresses the relevant risks:

- The invoice query binds both invoice ID and authenticated owner ID.
- DNS execution uses an argument list with `shell=False`; validation excludes shell syntax and leading option characters. A timeout and the stated deployment restrictions constrain execution.
- Wildcard CORS exposes only the literal public status response; sensitive-data disclosure is not demonstrated.
- `DOCUMENTATION_KEY` is explicitly a dummy value, not evidence of an exposed private credential.
- Session forgery and missing deployment controls cannot be asserted against the supplied contract.

These conclusions apply only to the supplied samples and deployment facts. No sample code, tests, or exploits were executed; no network or advisory checks, dependency installation, unrelated-file inspection, or file modifications occurred. Actual deployment enforcement, stored data, and runtime behavior remain independently unverified.
