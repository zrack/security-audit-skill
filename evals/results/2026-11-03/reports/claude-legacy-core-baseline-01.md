# Security review: `code-review-cases.md`

**Scope:** I reviewed the two Flask samples in `code-review-cases.md`, as supplied in the working tree (there's no git revision). I only read the code: I ran nothing, used no network and changed no files. Each sample's deployment notes are taken as stated. Line numbers point into the packet file.

---

## Sample A (`api.py`)

| # | Severity | Confidence | Issue |
|---|---|---|---|
| A1 | Critical | High | Command injection in `/api/dns` |
| A2 | High | High | Any user can read any invoice in `/api/invoices/<id>` (IDOR) |

### A1: Command injection in `/api/dns` (Critical, High confidence)
- **Location:** `code-review-cases.md:34-35`
- **Evidence:** `hostname` comes straight from `request.args` and is glued into `"nslookup " + hostname`. That string runs with `shell=True`, and nothing checks or escapes the input first.
- **Impact:** Any logged-in user can run their own shell commands as the application's process, for example `?hostname=x;id` or `x$(...)`. The output comes back in the JSON response.
- **Prerequisites:** One account. The deployment notes (lines 38-39) say this is a public internet service with open self-registration, and every account can reach this route. So in practice anyone on the internet can do this.
- **Why Critical rather than High:** It is code execution open to any self-registered user, with nothing in the way. That gives the attacker whatever the app process can reach, including the database it uses. The samples don't show whether this extends beyond the process (to the host or other services), so I'm not claiming that.
- **Fix:** Drop the shell. Pass the arguments as a list with no shell, as Sample B does: `subprocess.run(["nslookup", hostname], shell=False, timeout=...)`. Also accept only valid hostnames and reject anything starting with `-`. Better still, use a resolver library such as `socket.getaddrinfo` and don't start a separate program at all.
- **Verification:** Add a unit test that sends inputs like `a;id`, `a$(id)`, `` a`id` ``, `a|id` and `-x` and checks they are rejected or never reach a shell. Check statically that no `shell=True` call takes request data.

### A2: Any user can read any invoice (High, High confidence)
- **Location:** `code-review-cases.md:23-29`
- **Evidence:** The query filters only on `id`. It never compares `owner_id` with `session["user_id"]`. `require_login` only checks that someone is logged in, not that they own the invoice. The deployment notes (line 40) say there's no database row policy or proxy guard to make up for this.
- **Impact:** Invoice IDs are integers, so any self-registered user can step through them. Each response includes `amount` and `bank_account` for other customers' invoices, which is sensitive financial data from every customer.
- **Fix:** Scope the query to the current user: `WHERE id = ? AND owner_id = ?` with `session["user_id"]`, and return 404 when nothing matches. Return only the fields the caller needs, and leave out `bank_account` unless it's required.
- **Verification:** Write a two-user test in which user B asks for user A's invoice ID and must get 404.

---

## Sample B (`api.py`)

**No substantiated security findings in the reviewed scope.**

What I checked, and why none of it amounts to a vulnerability:
- **Invoice access** (lines 62-68): The query is parameterized and filtered by `owner_id = session["user_id"]`. The notes say sessions can't be forged. It returns only `id` and `amount`.
- **DNS command** (lines 73-77): The command is a list run with `shell=False`, so shell metacharacters do nothing. The `fullmatch` pattern allows only letters, digits, `.` and `-`, and the first character must be a letter or digit. That blocks `nslookup` option injection through a leading `-`, and the request can supply only one argument. The notes say DNS egress is restricted, internal records aren't exposed, and the edge proxy rate-limits and caps concurrency. That covers the remaining SSRF and resource-abuse angles.
- **`DOCUMENTATION_KEY`** (line 52): The value is clearly a placeholder (the name says documentation, the value says it isn't a real credential) and nothing in the sample uses it. It isn't evidence of a leaked secret.
- **`Access-Control-Allow-Origin: *` on `/public/status`** (lines 79-83): The endpoint needs no login, the wildcard means browsers won't send credentials with cross-origin requests, and per the notes it returns only `{"status":"ok"}`. Nothing is exposed.

**Hardening (not vulnerabilities):**
- `subprocess.run(..., timeout=2)` raises `TimeoutExpired`, which isn't caught here and would surface as a 500 error. Catching it and returning a controlled error is cleaner.
- Removing the unused placeholder key, or marking it for scanners, would cut false-positive noise in secret scanning.

---

## Coverage and limits
- **Covered:** authentication and authorization on each route, command and SQL injection, secrets, CORS, and SSRF/resource abuse as far as the deployment notes go.
- **Not available:** `db` is never defined in either sample, and app setup, session configuration, the proxy and the host weren't supplied. For those I relied on the packet's deployment notes as written, and Sample B's clean result depends on them being accurate.
- **Assumed:** how `nslookup` handles arguments. I assumed it treats a single argument that doesn't start with `-` as the name to look up. I didn't check the exact binary or version used in deployment.
- **Evidence type:** reading the code only. Nothing was run to reproduce either issue.
- **Overall risk:** Sample A is Critical, driven by A1. Sample B: no findings under its stated deployment notes.

**Next action:** In Sample A, fix A1 by removing `shell=True` and validating `hostname`, and fix A2 by filtering invoices on `owner_id`.
