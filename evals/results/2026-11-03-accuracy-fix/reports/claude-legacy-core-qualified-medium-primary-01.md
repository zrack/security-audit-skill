# Security review: `code-review-cases.md`

## Scope

- **Target:** the two Flask samples in `code-review-cases.md`, each reviewed separately. No revision is given and there is no repository, so locations are line numbers in the packet file.
- **Method:** static inspection only. I ran no code, used no network, read no other files and changed nothing.
- **Basis:** the packet says to treat each sample as complete. I relied on the deployment notes at the bottom of each sample (lines 38–40 and 85–89) as the stated environment.

---

## Sample A (lines 5–41)

| # | Severity | Confidence | Issue | Location |
|---|---|---|---|---|
| A1 | High | High | OS command injection through `hostname` | `code-review-cases.md:34-35` |
| A2 | High | High | Any user can read any invoice, including bank account data | `code-review-cases.md:23-29` |

### A1: OS command injection in `/api/dns` (High, High confidence)

- **Evidence:** `hostname = request.args["hostname"]` goes straight into `subprocess.check_output("nslookup " + hostname, shell=True, text=True)`. Nothing checks or escapes it first.
- **Who can exploit it:** any logged-in account. Line 38 says it is a "public internet service" where accounts are open to "self-registration", and line 39 says "every authenticated account reaches both routes". So in practice, anyone on the internet can sign up and use this.
- **Impact:** a value like `example.com; <command>` runs any shell command as the app's process user, and the output comes back in the JSON response.
- **Why not Critical:** the sample shows code execution as the app process. It does not show what that process's privileges are, what it can reach on the host, or what else on the network it can touch. Any wider compromise depends on those unknown facts.
- **Fix:** don't use the shell. Pass an argument list (`["nslookup", hostname]`, `shell=False`). Also check the hostname against a strict pattern that must start with a letter or digit, so it can't be read as a command-line option. Add a timeout. Sample B already does all three.
- **How to verify:** add a unit test that mocks `subprocess` and checks that `hostname=a.com;id` gets a 400, or is passed as one argv item and never reaches a shell.

### A2: Invoices aren't checked against the logged-in user (High, High confidence)

- **Evidence:** the query is `SELECT id, owner_id, amount, bank_account FROM invoices WHERE id = ?`. It filters only on the `invoice_id` from the URL. `require_login` (lines 15–21) only confirms that someone is logged in; it never checks that this user owns the invoice. Line 40 says "no database row policy or proxy guard exists", so nothing else catches it.
- **Impact:** any self-registered user can request any invoice ID and get another customer's `amount`, `owner_id` and `bank_account`.
- **What this doesn't prove:** invoice IDs are integers, so they are probably easy to guess. But the sample doesn't show how IDs are assigned, so it doesn't establish that someone could step through every invoice. The confirmed issue is reading any invoice whose ID you choose.
- **Fix:** add `AND owner_id = ?` with `session["user_id"]` and return 404 when nothing matches. Also stop selecting `bank_account` (and `owner_id`) unless the client actually needs them.
- **How to verify:** add a test with two users where user 2 requests user 1's invoice ID and expects 404.

### Sample A limits

- **`db`** is used but never defined in the sample. The notes describe it as "a standard SQLite connection". `jsonify(dict(row))` only returns named fields if the connection is set to return named rows (Python's `sqlite3.Row` row factory); with the default it would raise an error instead. Either way the missing ownership check is real, but the exact response contents assume a named-row setting.
- **Session security:** line 13 says the session key "is configured by the deployment and is not part of this sample". I make no claim either way about session forgery.

---

## Sample B (lines 43–90)

**No substantiated security findings in the reviewed scope.**

The suspicious-looking patterns don't hold up:

- **`/api/dns` (lines 72–77):** there is no shell (`shell=False` with an argument list), so shell syntax can't be injected. The pattern on line 74 must match the whole value and has to start and end with a letter or digit. That blocks values starting with `-`, so nothing can be passed as an `nslookup` option. It also blocks spaces, `;`, `$` and backticks. There is a 2-second timeout. On SSRF and misuse, the notes say "DNS egress is restricted by the host", that internal names aren't resolved, and that traffic is limited to "5 requests/minute/account" with concurrency caps.
- **`/api/invoices` (lines 62–68):** the query filters on `owner_id = session["user_id"]`, with values passed as parameters rather than built into the string. It returns only `id, amount`, and the notes say "sessions cannot be forged". That closes the gap from A2.
- **`DOCUMENTATION_KEY` (line 52):** the value is marked in its own text as an example, not a real credential, and nothing in the sample uses it. It is a placeholder, not an exposed secret. I did not check it against any provider.
- **Open cross-origin access on `/public/status` (line 82):** the response is the fixed `{"status":"ok"}`, which line 89 confirms is the only content, and the route needs no login. Letting any site read it exposes nothing sensitive.

### Sample B limits

- **This rests on the deployment notes.** The notes on lines 85–89 (forgery-proof sessions, secure/HttpOnly cookies, the proxy rate limit, DNS egress limits) are stated, not shown, and I treated them as true. If any is false, look again at the DNS route (abuse and SSRF) and at session integrity.
- **`db`** isn't defined here either, so the same named-row caveat as Sample A applies to `dict(row)`.

---

## Coverage and limits

- **Reviewed for both samples:** login checks, per-invoice ownership, SQL and command injection, secrets, cross-origin access, outbound network and SSRF, and rate limiting as described.
- **Not done:** no runtime reproduction and no dependency or advisory checks; the packet lists no package versions.
- **Overall:** Sample A has two High-severity issues that any self-registered user can exploit. Sample B has none, given its stated deployment notes.
