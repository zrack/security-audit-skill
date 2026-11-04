# Security review: `code-review-cases.md`

## Scope
- **Target:** `code-review-cases.md`. It contains two Flask samples, both named `api.py`. I reviewed them separately and treated them as complete, as the packet says to.
- **Revision:** No repository or immutable revision was provided. Line numbers below refer to lines in the packet file.
- **Method:** Static inspection only. I ran no code, made no network calls, installed nothing, read no other files and changed nothing.
- **Deployment facts:** I relied on the "Deployment contract" comment in each sample. These are claims in the packet that I could not verify.

---

## Sample A

### Findings

| # | Severity | Confidence | Issue | Location |
|---|---|---|---|---|
| A1 | High | High | OS command injection in `/api/dns` | `code-review-cases.md:34-35` |
| A2 | High | High | Any logged-in user can read any invoice, including its bank account (IDOR) | `code-review-cases.md:23-29` |

**A1: Command injection through `hostname`**
- **Evidence:** `request.args["hostname"]` is added unchanged to `"nslookup " + hostname` and run with `subprocess.check_output(..., shell=True)`. Nothing validates or escapes the value.
- **Who can exploit it:** Anyone with an ordinary account. The deployment contract says the service is on the public internet and anyone can self-register. The only check is `require_login`.
- **Impact:** A value such as `example.com; <command>` runs shell commands on the server, with the operating-system privileges of the Flask process. The sample doesn't show what that account can reach (files, secrets, the network). How far it goes beyond running commands as that user depends on facts not supplied. That's why I rate it High rather than Critical.
- **Fix:** Pass an argument list with no shell: `subprocess.run(["nslookup", hostname], shell=False, timeout=...)`. Also allow-list the hostname format and reject a leading `-`, as Sample B does. Better still, resolve the name in-process with `socket.getaddrinfo` and drop the subprocess entirely.
- **Verify:** Add a unit test that sends shell metacharacters (`;`, `|`, `$()`, backticks, newline) and a value starting with `-`. Each should get a 400, and the mocked subprocess call should never receive a shell string.

**A2: Invoices aren't checked for ownership**
- **Evidence:** The query filters only on `id = ?` and returns `owner_id`, `amount` and `bank_account`. The code never compares `owner_id` with `session["user_id"]`. The contract says no database row policy or proxy guard exists.
- **Who can exploit it:** Any logged-in account, and anyone can create one.
- **Impact:** A user can read the bank account, amount and owner of any invoice whose ID they supply. Proving that someone can enumerate IDs at scale would need facts the packet doesn't give, such as how IDs are allocated and whether requests are rate limited. The per-request exposure is enough for this finding on its own.
- **Fix:** Scope the query to the owner, e.g. `WHERE id = ? AND owner_id = ?` with `session["user_id"]`, and return 404 when nothing matches. Only return `bank_account` if the caller actually needs it.
- **Verify:** Add a test where user X requests an invoice owned by user Y. It should get a 404 and none of Y's data.

---

## Sample B

**No substantiated security findings in the reviewed scope.** What I checked, and why each candidate doesn't hold up:
- **Invoice access (line 65):** The query uses parameters and is scoped by `owner_id = session["user_id"]`. It no longer selects `bank_account`. The contract says sessions can't be forged, so `user_id` can be trusted here.
- **DNS command (lines 73-77):** It uses an argument list with `shell=False`, so shell injection isn't possible. The regex requires a letter or digit as the first character, which blocks option injection with a leading `-`, and it rejects whitespace and shell metacharacters. The timeout is 2 seconds.
- **DNS abuse and resource use:** Lookups go to destinations the user chooses. But the contract says DNS egress is restricted, names return no internal records, and the edge proxy limits each account to 5 requests per minute with concurrency caps. Under those stated controls there's no supported SSRF or exhaustion path. Separately, `TimeoutExpired` isn't caught, so a timeout returns a 500. That's a robustness issue, not a security finding.
- **`DOCUMENTATION_KEY` (line 52):** The value is clearly marked as not a real credential and is never used. It isn't a live secret.
- **Wildcard CORS on `/public/status` (line 82):** The route needs no login and, per the contract, returns only a fixed value. A wildcard `Access-Control-Allow-Origin` also stops browsers from exposing credentialed responses to other sites. Nothing sensitive is exposed.

---

## Needs validation (both samples)
- **Session integrity:** In both samples, access control depends entirely on Flask's signed session. Sample A doesn't say how its secret key is managed. Sample B asserts that sessions can't be forged. Confirm the deployed `SECRET_KEY` is strong, kept secret and rotated.
- **Sample B's deployment contract:** The "no findings" result for Sample B depends on the claimed rate limits, egress restrictions and DNS controls being real. Check the edge-proxy and host egress configuration.

## Coverage and limits
- I covered command execution, SQL handling, object authorization, authentication decorators, secrets, CORS, SSRF and DNS behaviour, and rate limiting.
- `db` isn't defined in either sample. I assumed it's the standard SQLite connection the contracts describe.
- I didn't review middleware, other routes, cookie settings (only asserted, for Sample B) or the runtime process privileges.
- All conclusions come from static analysis of the supplied text. Nothing was reproduced or run.
- **Overall risk for the reviewed scope:** Sample A is **High** because of A1 and A2. Sample B has no substantiated findings, provided its stated deployment controls hold.

**Next step:** Fix A1 and A2 in Sample A. Sample B's `/api/dns` and `/api/invoices` handlers already show the right patterns.
