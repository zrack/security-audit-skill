# Security review: `review-packet.md` (Samples F–K)

## Scope

- **What I reviewed:** only `review-packet.md`. It holds six synthetic Python/Flask-style excerpts, F through K, and each has its own contract. I treated those contracts as true, as the packet says to.
- **Version:** the workspace is not a git repository, so there is no fixed revision. I reviewed the file as it is on disk now.
- **Method:** I read the code only. I ran nothing, used no network, installed nothing, read no other files and changed nothing.
- **Result:** 3 findings (F, H, J). G, I and K have no substantiated findings.

| Sample | Result | Severity | Confidence |
|---|---|---|---|
| F `/fetch` | Server-side request forgery (SSRF) exposes the internal report service | High | High |
| G `/weather` | No substantiated finding | — | — |
| H `/preview` | Reflected cross-site scripting (XSS) on the account origin | High | High |
| I `/preview` | No substantiated finding | — | — |
| J `/upload` | Path traversal allows arbitrary file overwrite, including account-service config | High | High |
| K `/upload` | No substantiated finding | — | — |

---

## Sample F: SSRF to the internal report service (High, confidence High)

**Location:** Sample F, `fetch()`, at `destination = request.args["url"]` and `http.get(destination, ...)` (packet lines 11–13).

**What happens:** Any self-registered user can request `/fetch?url=http://10.40.0.15:8080/exports/current`.
- The client "performs no destination filtering."
- The application host can reach that address.
- The internal route returns confidential tenant account reports "to any caller on that internal network, without another credential."
- The handler sends the response body back to the user.

**Consequence:** Any self-registered internet user can read confidential tenant account reports. According to the contract, nothing else outside the network exposes them. Each request returns at most 64 KiB.

**Controls checked:**
- `@require_login` only establishes that the caller has an account. Anyone can sign up, so it is not a barrier.
- `follow_redirects=False` does not help, because the attacker names the internal URL directly.
- TLS verification and having no proxy do not affect a plain-HTTP internal target.
- The 64 KiB limit truncates what is returned. It does not stop the exposure.
- The fetch process has no host-administrator privilege, so I claim nothing beyond reading internal HTTP resources.

**Not established:**
- Whether the reports span several tenants or a whole tenant's data. The contract only says "confidential tenant account reports."
- Which other internal services are reachable. I only claim the stated report service.

**Fix:**
- Best: remove free-form URL fetching, or restrict it to an allowlist of hosts and schemes.
- If arbitrary public URLs are a real requirement: resolve the hostname, reject private, loopback, link-local and metadata ranges, and connect to the IP you checked so DNS rebinding cannot swap it.
- Separately, require authentication on `/exports/current` instead of trusting anything on the internal network.

**How to verify:** A unit or integration test against a stubbed client should show that `http://10.40.0.15:8080/...`, `http://127.0.0.1/...`, and a public hostname that resolves to a private IP are all rejected before any connection is made.

---

## Sample G: no substantiated finding

The destination host and path are fixed. The `station` value must match `[A-Z]{4}` and is sent as a query parameter. Users cannot change the URL, options, DNS or headers. Redirects are off and TLS is verified. The upstream returns only public data and makes no further fetches. I found no attacker-controlled destination, so there is no SSRF, and no sensitive data is exposed.

---

## Sample H: reflected XSS on the signed-in account origin (High, confidence High)

**Location:** Sample H, `preview()`, at `Response(request.args["message"], content_type="text/html")` (packet line 43).

**What happens:** An attacker puts a script in `message` (for example a `<script>` element) and sends the link to a signed-in victim. The response is rendered as HTML with no escaping, no Content-Security-Policy (CSP) and no sandbox. The script therefore runs in the same origin as the account interface.

**Consequence:** The script can call the same-origin JSON API. The browser attaches the victim's session cookie, so the script can read the victim's confidential account details. With no CSP, it can then send them to the attacker.

**Controls checked:**
- `HttpOnly` stops the script from reading the cookie value. It does not stop same-origin requests that carry the cookie, so it does not prevent this.
- `Secure` and the fact that sessions cannot be forged don't change this outcome.
- **Prerequisite:** the victim opens the link while signed in.

**Not established:**
- The contract makes "no claim about administrator users or host privileges."
- No state-changing endpoints are described.
- I rate only reading the victim's account data. Actions taken as the victim depend on endpoints that were not supplied.

**Fix:**
- Escape the output (`html.escape(..., quote=True)`), or serve it as `text/plain`.
- Add a restrictive CSP, as Sample I does.
- Consider serving user-controlled previews from a separate sandbox origin.

**How to verify:** A test should show that requesting `/preview?message=<script>x</script>` returns `&lt;script&gt;...` and a CSP header.

---

## Sample I: no substantiated finding

`html.escape(..., quote=True)` escapes `& < > " '`. The value goes only into a `<p>` text context. The contract says nothing decodes or re-inserts it later.

There is also a second layer: `default-src 'none'` blocks scripts even if markup got through, and `frame-ancestors 'none'` blocks framing. I found no injection path within the stated scope, which is the complete preview output path.

---

## Sample J: path traversal and arbitrary overwrite of account-service configuration (High, confidence High)

**Location:** Sample J, `upload()`, at `destination = ROOT / item.filename` and `item.save(destination)` (packet lines 70–71).

**What happens:** The framework keeps the attacker's filename exactly as sent. In Python, `ROOT / "/srv/account-service/config/<file>"` gives that absolute path, and `ROOT / "../account-service/config/<file>"` escapes the upload root. `save` writes to that exact path and overwrites any existing file.

**Consequence:**
- **Immediate:** any self-registered user can create or overwrite files, up to 16 KiB, in `/srv/account-service/config`. They can also overwrite other users' files in `/srv/uploads`. That is an integrity failure for another service's security configuration.
- **On the next restart:** per the contract, overwriting that config "can disable account-service authentication on its next ordinary restart."

**Who can trigger the restart?** This is not established. The contract says no "immediate restart control is established." The authentication bypass therefore takes effect on the next ordinary restart, and the attacker can't necessarily choose when that is. High severity rests on an unauthenticated-equivalent actor (anyone can sign up) being able to change authentication config whenever the service next restarts.

**Limits on impact:**
- The application can only write to the two named directories.
- There is no root privilege, executable directory or HTML rendering, so I do not claim code execution.

**Fix:**
- Ignore the client's filename. Generate a server-side name (for example a UUID) and store the original name only as metadata.
- Alternatively, validate the name against a strict allowlist, resolve the path and check `is_relative_to(ROOT)`, and open with `"xb"`, as Sample K does.
- Also, run the upload service as a user that has no write access to `/srv/account-service/config`.
- Because files may already have been tampered with, check the integrity of the existing config files.

**How to verify:**
- Tests should show that filenames `/srv/account-service/config/x`, `../account-service/config/x` and `a/../../x` are rejected, and that no file is created outside `/srv/uploads`.
- Confirm with filesystem permissions that the upload process cannot write to the config directory.

---

## Sample K: no substantiated finding

**Why the path is safe:**
- The regex allows only `[A-Za-z0-9_-]{1,48}` followed by `.txt`. That excludes `/`, `\`, absolute paths and `..` segments.
- The `resolve()` plus `is_relative_to(ROOT)` check is a second containment layer. Python 3.10+ is stated, and `is_relative_to` exists from 3.9.
- Mode `"xb"` refuses to overwrite existing files, and the conflict is handled.
- Users cannot create symlinks, hard links or directories, and trusted parents prevent the directory from being swapped underneath.
- Files are never executed, rendered, listed or served for download.

**Not assessed:** storage exhaustion from many 16 KiB uploads. The contract supplies no quota or abuse impact, so this is outside what the evidence supports.

---

## Coverage and limits

- **How the conclusions were reached:** every conclusion comes from reading the code against the supplied contracts. I ran nothing locally and made no runtime checks, as you asked.
- **What depends on the contracts:** the behaviour of helpers (`http.get`, `require_login`, `save`, the framework) is taken from the contracts and not checked against real libraries.
- **What was not inspected:** decorator internals, other account handlers, edge or infrastructure configuration, and anything outside `review-packet.md`.
- **Overall risk:** Unrated: insufficient context. Each finding is rated only within its own sample.

**Next step:** fix F, H and J as described above. For J, also find out who can trigger the account-service restart and check whether the existing config files have already been modified.
