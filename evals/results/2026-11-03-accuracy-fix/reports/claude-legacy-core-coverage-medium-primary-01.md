# Security review: `code-review-cases.md` (Samples A and B)

**Scope:** I reviewed only `code-review-cases.md`, which contains two Flask `api.py` samples and the deployment contract written under each one. There is no repository or revision, so locations are line numbers in the packet. I read the code statically and nothing else: no code was run, no network was used, and no other files were opened or changed.

---

## Sample A

| # | Severity | Confidence | Issue | Location |
|---|---|---|---|---|
| A1 | High | High | OS command injection in `/api/dns` | packet L34–35 |
| A2 | High | High | Missing object authorization on `/api/invoices/<id>` (IDOR) exposes `bank_account` | packet L23–29 |

### A1. Command injection through `hostname` (High, High confidence)
- **What the code shows:** `hostname = request.args["hostname"]` is joined onto `"nslookup " + hostname` and passed to `subprocess.check_output(..., shell=True)`. Nothing validates or escapes it, so shell metacharacters such as `;`, `|`, `$()` and backticks run as extra commands. The command's output goes back in the JSON response.
- **Who can reach it:** The only control is `require_login`. The contract says the service is on the public internet, accounts come "by self-registration", and "Every authenticated account reaches both routes." So anyone who signs up can run commands on the server as the Flask process user and read the results.
- **Severity reasoning:** Running arbitrary commands is a serious compromise, so this is High. I did not rate it Critical because the packet says nothing about the process's privileges, filesystem, credentials or network reach. Those decide how far the damage goes.
- **Fix:** Drop `shell=True` and pass an argument list, `["nslookup", hostname]`. Validate `hostname` against a strict hostname pattern that cannot start with `-`, and add a timeout. Sample B shows this pattern. Better still, resolve names in-process (for example with `socket.getaddrinfo`) so no subprocess is needed.
- **How to check the fix:** Write a unit test that mocks `subprocess` and asserts that `hostname=example.com;id` gets a 400 and is never passed to a shell. Also confirm that `shell=True` no longer appears anywhere.

### A2. Any logged-in user can read any invoice (High, High confidence)
- **What the code shows:** The query filters only by `id = ?`. The handler never compares `owner_id` with `session["user_id"]` and returns the whole row: `id, owner_id, amount, bank_account`. The query is parameterized, so there is no SQL injection.
- **Who can reach it:** Any self-registered account can supply any integer `invoice_id` and get back another user's invoice, including the bank account. The contract rules out other controls: "No database row policy or proxy guard exists."
- **Severity reasoning:** Unauthorized cross-user access to financial data is High. The code proves that any invoice can be fetched by its ID. How many invoices an attacker could collect in practice depends on the ID distribution and request volume, which the packet does not cover.
- **Fix:** Add `AND owner_id = ?` with `session["user_id"]` to the query and return 404 when nothing matches. Only return the fields the caller needs; leave `bank_account` out unless it is required.
- **How to check the fix:** Write a two-user test in which user B requests user A's invoice ID and must get a 404 with no data.

---

## Sample B

**No substantiated security findings in this sample.** Each item that looked suspicious is covered by a control in the code or by the stated contract:

- **`/api/invoices`:** The query is scoped with `AND owner_id = ?` using `session["user_id"]`, only `id, amount` are returned, and the query is parameterized. The contract says "sessions cannot be forged."
- **`/api/dns`:** The command is an argument list with `shell=False`, and `re.fullmatch` limits `hostname` to letters, digits, `.` and `-`. The first character must be a letter or digit, so the value cannot be read as an `nslookup` option. There is a 2-second timeout. The contract adds that DNS egress is restricted by the host and that names resolve to "no internal records."
- **`DOCUMENTATION_KEY` (L53):** The value is labeled `not-a-real-credential` and nothing in the sample uses it. It is a placeholder, not an exposed secret.
- **`/public/status` with `Access-Control-Allow-Origin: *`:** It returns no credentials or allow-credentials header, and the contract says it contains "only the literal value above". Nothing sensitive can leak.
- **Resource abuse:** The contract states the edge proxy limits requests to 5 per minute per account with concurrency caps, and the subprocess has a timeout.

---

## Coverage and limits
- **Covered:** authentication and authorization, injection, secrets, CORS, outbound network/SSRF, and resource use, for both samples.
- **Not run:** I did not run any code, reproduce anything locally, or test the actual behavior of `nslookup` or Flask. Every conclusion comes from reading the code.
- **Relied on, not verified:** Neither sample defines `db`, so I took the packet's description of it as given. Sample B's conclusions depend on its deployment contract (session integrity, the egress restriction, the rate limits and the content of the status route). I treated those as given and did not verify them.
- **Overall risk for what I reviewed:** Sample A is high risk because of A1 and A2. Sample B has no substantiated issues within this scope, which is not a guarantee that it is secure.
