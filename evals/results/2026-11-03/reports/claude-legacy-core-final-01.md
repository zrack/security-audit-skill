I read only `code-review-cases.md` and reviewed it by static inspection, with nothing executed or changed.

## Scope
- **Target:** the two Flask samples (both named `api.py`) in `code-review-cases.md`. There's no revision or repository behind them; the packet treats them as complete.
- **Method:** I read the code by hand and checked it against the deployment notes in the packet. No tools were run and nothing was executed or reproduced.
- **What I assumed:** the deployment notes in the packet are true. Neither sample defines `db`, so I took it to be the standard SQLite connection the notes describe.

---

## Sample A: two findings

| # | Severity | Confidence | Location | Issue |
|---|---|---|---|---|
| A1 | High | High | `invoice()`, packet lines 23–29 | Any logged-in user can read any invoice, including its bank account |
| A2 | High | High | `dns()`, packet lines 31–36 | Command injection through `hostname` |

### A1: Any logged-in user can read any invoice (High)
- **Evidence:** `require_login` only checks that `session["user_id"]` exists. The query is `WHERE id = ?` and never compares `owner_id` with the session user. The route returns every selected column, including `owner_id`, `amount` and `bank_account`.
- **Who can do it:** anyone, because accounts are self-registered and the packet says no row policy or proxy guard exists. The `<int:...>` route converter lets an attacker pick any invoice ID.
- **Impact:** an attacker can read another customer's amount and bank account for any invoice ID they choose. IDs are only shown to be selectable. The sample doesn't show whether they're sequential or guessable, so mass harvesting isn't established.
- **Fix:** add `AND owner_id = ?` with `session["user_id"]` to the query, and return 404 when no row matches. Drop `bank_account` and `owner_id` from the response unless the client actually needs them.
- **Verify:** with two test accounts, request one user's invoice while logged in as the other and expect a 404.

### A2: Command injection in `/api/dns` (High)
- **Evidence:** `request.args["hostname"]` is joined straight into `"nslookup " + hostname` and run with `shell=True`. There's no validation, so shell metacharacters such as `;`, `|`, `$()` and backticks run as extra commands.
- **Who can do it:** any authenticated, self-registered user.
- **Impact:** the attacker can run any OS command as the Flask process user.
- **Why High and not Critical:** the sample doesn't show that user's privileges, what files or secrets it can reach, or what network access it has. Running commands doesn't by itself prove access to every application resource. If the process can read secrets such as the session key or database credentials, the impact could be broader; that needs checking.
- **Fix:** pass a list of arguments with `shell=False`, add a strict allowlist check on the hostname, and set a timeout. Sample B does exactly this. Also consider whether ordinary accounts need this endpoint at all.
- **Verify:** add a test where a payload like `example.com;id` gets a 400 response and starts no extra process. Mocking `subprocess` and checking its arguments covers this.

---

## Sample B: no substantiated security findings

These controls hold up against the supplied code and deployment notes:
- **Invoice access:** the query filters on `owner_id = session["user_id"]` and returns only `id` and `amount`, so another user's invoice gives a 404. `require_login` makes sure `session["user_id"]` exists before the handler reads it.
- **DNS lookup:** the arguments are passed as a list with `shell=False`, so no shell interprets the input. The `fullmatch` allowlist only accepts letters, digits, `.` and `-`, must start and end with a letter or digit, and caps the length at 253. That means the value can't begin with `-` and be read as an nslookup option. A 2-second timeout is set.
- **SSRF and abuse:** the packet says DNS egress is restricted by the host and resolved names return no internal records. It also says the proxy limits each account to 5 requests a minute with concurrency caps. With those controls in place, I found no supported path to internal reconnaissance or resource exhaustion.
- **`DOCUMENTATION_KEY` (line 52):** the value is clearly labelled as not a real credential, which makes it a placeholder rather than an exposed secret. That rests on the label alone; I didn't check it with any provider.
- **Wildcard CORS on `/public/status`:** a wildcard origin stops browsers exposing a credentialed response to other sites. The route also needs no login and, per the packet, returns only a fixed `status="ok"`, so nothing sensitive leaks.

---

## Limits
- This is static analysis only. Neither A1 nor A2 was reproduced at runtime.
- The verdict on Sample B rests on the packet's deployment notes being true. I can't independently confirm the session-key handling, cookie flags, egress restriction, DNS behaviour or proxy rate limits from what was supplied.
- The `db` setup, other routes and middleware outside the samples weren't available, and no dependency or advisory checks were done.
- **Overall risk:** Sample A has two High findings that any self-registered user can exploit. Sample B has none in the reviewed scope; that's the result of this review, not a guarantee.

**Next step:** fix A1 and A2 in Sample A by applying the owner check and the argument-list subprocess call that Sample B already uses, then run the two tests described above.
