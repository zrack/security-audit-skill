# Security review: `code-review-cases.md`

**Scope:** I read only the two Flask samples in `code-review-cases.md`. The packet says they are the complete samples. There is no revision or repository, so the line numbers below point into the packet file. I used static inspection only. I didn't run any code, use the network, install dependencies or change files. I took the deployment notes in each sample as true; they set the threat model.

---

## Sample A (`api.py`, packet lines 7–41)

| # | Severity | Confidence | Finding | Location |
|---|---|---|---|---|
| A1 | High | High | OS command injection in `/api/dns` | `code-review-cases.md:34-35` |
| A2 | High | High | Any logged-in user can read any invoice, including the bank account field | `code-review-cases.md:23-29` |

### A1: Command injection through `hostname`
- **Evidence:** `hostname` comes straight from `request.args["hostname"]`. It's added to the string `"nslookup " + hostname` and run with `subprocess.check_output(..., shell=True)`. Nothing checks or escapes it, so shell characters like `;`, `|`, `$( )` and backticks get interpreted. The command output goes back in the response, so the attacker can read the results directly.
- **Prerequisites:** a logged-in session only. The deployment note says it's a public internet service, anyone can register, and every account can use this route.
- **Impact:** the attacker can run any shell command with the app process's privileges. The sample doesn't show what that account can reach or what else runs on the host. So I rated this High rather than Critical. If the process turns out to have broad access, such as secrets, the database file or privileged credentials, Critical may be justified.
- **Fix:** don't use the shell. Pass an argument list, `subprocess.run(["nslookup", hostname], shell=False, timeout=...)`. Check `hostname` against a strict hostname pattern that also blocks a leading `-`. Sample B does both.
- **Verify:** add a unit test that mocks `subprocess` and checks that a value like `example.com;id` gets a 400 or is passed as a single argument, never to a shell.

### A2: Missing ownership check on invoices
- **Evidence:** the query filters only by `id = ?`. It's parameterized, so this isn't SQL injection. It selects `owner_id, amount, bank_account` and returns the whole row. `require_login` only checks that `session["user_id"]` exists; it never compares it to `owner_id`. The deployment note confirms there's no database row policy or proxy check.
- **Prerequisites:** a self-registered account and an invoice ID.
- **Impact:** a user can read amounts and bank account data on invoices they don't own. This proves access to any invoice whose ID the attacker supplies. Whether they can harvest invoices in bulk depends on how IDs are assigned and on rate limits, and neither is stated.
- **Fix:** add `AND owner_id = ?` bound to `session["user_id"]`, or apply an equivalent authorization rule. Return 404 for both "not found" and "not yours". Return only the fields the caller needs; `bank_account` probably shouldn't be included by default.
- **Verify:** add a test where user X requests user Y's invoice and gets 404, and the response body contains no `bank_account`.

---

## Sample B (`api.py`, packet lines 45–90)

**No substantiated security findings in the reviewed scope.** Each candidate and why it doesn't hold up:

- **`/api/invoices` (line 65):** the query is parameterized and limited to `owner_id = session["user_id"]`. Per the deployment note, sessions can't be forged. It returns only `id` and `amount`.
- **`/api/dns` (lines 73–77):**
  - No shell is involved: the call uses an argument list with `shell=False`, so shell characters have no effect.
  - The pattern check with `re.fullmatch` requires the first character to be a letter or digit. That blocks `nslookup` option injection through a leading `-`. Spaces, `;` and other characters outside `[A-Za-z0-9.-]` are rejected.
  - `timeout=2` plus the stated limit of 5 requests per minute per account and the concurrency caps address resource abuse.
  - Server-side lookups of internal hosts are covered by the deployment note: DNS egress is restricted and internal records aren't returned.
- **`DOCUMENTATION_KEY` (line 52):** the name and the value itself mark it as a placeholder that isn't a real credential, and nothing uses it. It's not an exposed secret on this evidence.
- **Wildcard CORS on `/public/status` (lines 79–83):** the route needs no login and returns only a fixed literal. A wildcard `Access-Control-Allow-Origin` doesn't let other sites read credentialed responses, and there's no sensitive data here to read anyway.

**Optional hardening (not a vulnerability):** `/api/dns` returns the raw `nslookup` output. That normally includes the server's configured DNS resolver address, which may be an internal IP. If that matters, return only the resolved addresses.

---

## Coverage and limits

- **Evidence is static only.** Nothing was run, so none of these results were checked at runtime. I worked out the pattern's behaviour by reading it, not by testing it, and I didn't check how the specific `nslookup` build handles arguments.
- **Deployment notes are taken as given.** I relied on the stated self-registration, edge rate limits, DNS egress restrictions, cookie settings and session integrity without checking any of them. If any is false, the Sample B conclusions need another look. This matters most for egress and rate limiting.
- **Not shown in the samples:** where `db` is defined, the session secret setup, error handling, logging and other routes. I left those out rather than assuming they're there or missing.
- **Overall risk:** Sample A is High risk for the code reviewed. Sample B has no findings within the supplied evidence, which isn't a guarantee for the wider application.

**Next step:** fix A1 and A2 in Sample A. Sample B already shows the pattern for both fixes.
