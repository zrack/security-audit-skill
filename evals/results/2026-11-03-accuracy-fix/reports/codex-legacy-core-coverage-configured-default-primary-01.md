Reviewed only `code-review-cases.md`, using static inspection. No immutable revision was supplied.

**Sample A — two substantiated findings**

1. **High severity · High confidence — OS command injection.** At `line 35`, attacker-controlled `hostname` is concatenated into a command executed with `shell=True`. The deployment contract allows self-registration and gives every authenticated account access. Shell metacharacters can therefore execute arbitrary commands with the application process’s privileges. Those privileges and accessible assets are unspecified; broader compromise is not established.

   **Fix:** Use an argument list with `shell=False`, validate the hostname, and apply a timeout, following Sample B’s pattern. **Suggested verification:** Confirm shell syntax is rejected and accepted input remains one subprocess argument.

2. **High severity · High confidence — missing invoice ownership authorization.** At `lines 26–29`, the query selects solely by invoice ID and returns the row, including `bank_account`. Any authenticated account supplying an existing other owner’s invoice ID receives that invoice’s data. The contract explicitly excludes database row policies and proxy guards. Parameterization prevents SQL injection but does not enforce ownership. Invoice-ID discovery or enumeration is not demonstrated.

   **Fix:** Bind `owner_id = session["user_id"]` alongside the invoice ID, as Sample B does, and return only necessary fields. **Suggested verification:** Confirm an owner can retrieve their invoice and another account requesting that same ID receives no invoice data.

**Sample B — no substantiated security findings in the reviewed scope**

The supplied evidence supports the following conclusions:

- The invoice query binds both invoice ID and authenticated owner ID.
- DNS input is validated and passed as a separate argument with `shell=False`; a timeout, edge limits, concurrency caps, and DNS restrictions are explicitly supplied.
- `DOCUMENTATION_KEY` is an explicit dummy value, not evidence of an exposed private credential.
- Wildcard CORS on the literal public status response does not establish sensitive-data exposure.
- Session forgery and internal DNS disclosure would contradict the supplied deployment guarantees.

**Validation limits:** No sample code was executed, network accessed, dependencies installed, unrelated files inspected, or files modified. Deployment contracts were accepted as supplied, not independently verified. The suggested verification checks were not performed; conclusions apply only to these samples.
