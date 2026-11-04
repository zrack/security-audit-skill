# Security review: `code-review-cases.md`

**Scope:** `code-review-cases.md` holds two Flask samples, both named `api.py`. The file isn't under version control, so there's no revision to cite. I took the packet's word that each sample is complete and that its deployment-contract comments are true. I only read the code: nothing was run, nothing was fetched from the network, no files were changed, and I didn't open any other file. Line numbers below are lines in `code-review-cases.md`.

---

## Sample A

| # | Severity | Confidence | Issue | Location |
|---|---|---|---|---|
| A1 | High | High | Any logged-in user can read any invoice (missing ownership check, also called IDOR) | `invoice()`, lines 23–29 |
| A2 | High | High | Any logged-in user can run shell commands (command injection) | `dns()`, lines 31–36 |

### A1: Any logged-in user can read any invoice
- **What the code shows:** `require_login` only checks that `session["user_id"]` is set. The query filters on `WHERE id = ?` and nothing else; it never compares `owner_id` to the session user. The route then returns the whole row, including `owner_id`, `amount` and `bank_account`, through `jsonify(dict(row))`.
- **Who can exploit it:** The contract says anyone can self-register, and "Every authenticated account reaches both routes". It also says "No database row policy or proxy guard exists". So any registered user can request `/api/invoices/<id>` with an ID of their choosing and read another customer's bank account details.
- **Limit:** The samples don't show how IDs are assigned, for example whether they're sequential. So the code proves that any chosen invoice can be read; whether an attacker can list or enumerate all invoices is not established.
- **Fix:** Add `AND owner_id = ?` with `session["user_id"]` to the query, and return 404 when no row comes back (this is what Sample B does). Also stop returning `bank_account` unless the client actually needs it.
- **Verify:** Write a test where user A requests user B's invoice ID and gets 404 with no data, and user A requesting their own invoice still succeeds.

### A2: Command injection in `/api/dns`
- **What the code shows:** `request.args["hostname"]` is appended to `"nslookup "` and run with `shell=True` (line 35). A value such as `x; <command>` makes the shell run the extra command, and the route returns its output in the response.
- **Who can exploit it:** Any self-registered account on a public internet service, per the contract. There's no validation and no proxy guard.
- **Consequence:** The attacker can run arbitrary commands as the user the service process runs as. The samples don't say what that process can access, such as the database file, credentials on the host, or the network. I've rated this High rather than Critical because how far the damage reaches depends on those unknowns.
- **Fix:** Use `subprocess.run(["nslookup", hostname], shell=False, timeout=...)`. Also check the hostname against a strict pattern that can't start with `-`, so it can't be read as an option (this is what Sample B does).
- **Verify:** Write a unit test that sends `hostname=example.com;id` and checks that it's rejected or treated as a single argument. Also check the code for any remaining `shell=True` calls.

**Not a finding:** The session key isn't part of the sample. The packet says "The session key is configured by the deployment and is not part of this sample", so I made no finding about how sessions are signed.

---

## Sample B

**No substantiated security findings in the reviewed scope.**

These are the parts that could look risky, and what the supplied evidence shows for each:
- **Invoice access (line 66):** The query is parameterised and filtered by `owner_id = session["user_id"]`. It returns only `id` and `amount`, and returns 404 when another user's invoice is requested. The contract says sessions can't be forged.
- **DNS lookup (lines 75–78):**
  - The command is built as an argument list with `shell=False`, so the shell never sees the input.
  - The `fullmatch` pattern only allows letters, digits, `.` and `-`, and the first and last characters must be letters or digits. So the input can't be read as an option (no leading `-`), and nslookup receives exactly one argument.
  - There's a 2-second timeout. The contract also sets a rate limit of 5 requests per minute per account with concurrency caps, says DNS egress is restricted, and says no internal records resolve.
- **`DOCUMENTATION_KEY` (line 53):** The value is explicitly a dummy ("not-a-real-credential") and is never used, so it isn't treated as an exposed secret.
- **Wildcard CORS on `/public/status` (lines 80–84):** The route needs no login and, per the contract, returns only the literal `{"status":"ok"}`. The `*` header lets other websites read that response, but there's nothing sensitive in it to expose.

---

## Validation limits
- **Analysis method:** Static analysis only. Nothing was reproduced locally or tested against a running service.
- **Contract taken as true:** I didn't independently check the deployment contract, including the edge rate limit, DNS egress restriction, cookie flags and session-key handling.
- **Open questions for A2:** What OS user does the service run as, and what files, credentials and network access does that user have? The answers set how far a compromise reaches.
- **Overall risk:** Sample A is High for the scope reviewed. Sample B has no findings within the supplied scope, but that isn't a guarantee that the wider application is secure.
