Reviewed only `code-review-cases.md`, using static inspection and the supplied deployment contracts.

**Sample A — two substantiated findings**

1. **High: authenticated shell command injection. Confidence: High.**
   At packet line 35, attacker-controlled `hostname` is concatenated into a command executed with `shell=True`. Any self-registered account can inject shell syntax and execute commands with the application process’s privileges. Root access or broader host compromise is not established.
   **Fix:** use a fixed argument list with `shell=False`, validate the hostname, and set a timeout.
   **Suggested verification:** an isolated test confirming malicious input cannot launch an additional command.

2. **Medium: missing invoice ownership authorization. Confidence: High.**
   At packet lines 26–29, the query selects solely by invoice ID and passes the result—including `bank_account`—to response serialization. Authentication does not restrict selection to the caller’s invoices, and the contract excludes additional authorization guards. An account supplying another owner’s existing invoice ID can target that invoice; automatic ID discovery and bulk extraction are not established.
   **Fix:** bind `owner_id` to the authenticated user in the query and return only necessary fields.
   **Suggested verification:** two-account tests confirming cross-account requests receive 404 while authorized requests succeed.

**Sample B — no substantiated security findings in the reviewed scope**

- The parameterized invoice query enforces ownership using the guaranteed unforgeable session identity.
- DNS execution uses an argument list with `shell=False`; validation excludes shell metacharacters and leading option prefixes.
- `DOCUMENTATION_KEY` is explicitly a dummy value.
- Wildcard CORS exposes only the public, literal status response.
- The supplied DNS restrictions, timeout, rate limits, and concurrency caps do not support an internal-data disclosure or resource-exhaustion finding.

**Validation limits:** No sample code or tests were executed, and no network access, dependency installation, unrelated-file inspection, or file modification occurred. Deployment contracts were accepted as supplied. Actual HTTP responses and serialization, process privileges, and the extent of accessible invoice data were not verified. The suggested verification steps remain unperformed.
