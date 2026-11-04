Reviewed only `code-review-cases.md` using static inspection and the security-audit skill. Locations below are packet line numbers; no immutable revision was supplied.

**Sample A has two substantiated findings.**

1. **High severity, High confidence — OS command injection**
   **Location:** `dns()`, lines 31–36.
   `hostname` passes directly from request parameters into a command executed with `shell=True`. Any authenticated account, including a self-registered account, can supply shell syntax to execute commands with the application process’s permissions. Broader asset access or privileged system compromise is not established.

   **Fix:** Pass the executable and hostname as separate arguments with `shell=False`, validate the hostname, and impose a timeout.
   **Suggested verification, not performed:** In an isolated regression test, confirm shell metacharacters are rejected and valid hostnames reach the subprocess as one argument.

2. **Medium severity, High confidence — Missing invoice ownership authorization**
   **Location:** `invoice()`, lines 23–29.
   Login is required, but the parameterized query filters only by invoice ID. An authenticated caller supplying another owner’s existing invoice ID can retrieve its `id`, `owner_id`, `amount`, and `bank_account`. The deployment contract rules out an external ownership guard. This supports cross-account financial-data disclosure; enumeration, modification, and broader database access are not established.

   **Fix:** Add `AND owner_id = ?`, binding the authenticated session user, and return 404 when no authorized row matches.
   **Suggested verification, not performed:** With two users’ invoices, confirm each user can retrieve their own invoice and receives 404 for the other user’s invoice.

**Sample B: No substantiated security findings in the reviewed scope.**

The invoice query binds both invoice ID and session ownership. The DNS route uses an argument list with `shell=False`; its validation excludes shell syntax and leading option characters. The stated timeout, rate limits, concurrency caps, and DNS restrictions provide relevant additional controls.

`DOCUMENTATION_KEY` is explicitly a dummy value. Wildcard CORS on a response containing only the public literal status does not demonstrate sensitive-data exposure or credential theft.

All conclusions rely on the supplied code and deployment contracts. No sample code was executed, network accessed, dependencies installed, unrelated files inspected, or files modified. Runtime behavior, process privileges, and deployment controls were not independently verified.
