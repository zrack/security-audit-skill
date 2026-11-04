# Security review: `review-packet.md`, samples F–K

## Scope

- **Target:** `review-packet.md`, which holds six separate synthetic excerpts, each with its own contract. There's no repository or revision; the target is the file as supplied.
- **Method:** static inspection only. I read that one file and nothing else. I didn't run any code, make network requests, install anything, or change any files.
- **Assumptions:** the helpers and contracts behave exactly as the packet states (line 3). Each sample is judged only against its own contract, plus any contract it explicitly inherits.

## Summary

| Sample | Result | Severity | Confidence |
| --- | --- | --- | --- |
| F `/fetch` | Server-side request forgery (SSRF) exposes the internal report service | High | High |
| G `/weather` | No substantiated security findings | — | — |
| H `/preview` | Reflected XSS in the same origin as the account API | High | High |
| I `/preview` | No substantiated security findings | — | — |
| J `/upload` | Path traversal lets a user write files outside the upload folder, including account-service config | High | High |
| K `/upload` | No substantiated security findings | — | — |

---

## Sample F: SSRF to the internal report service (High, High confidence)

**Location:** `review-packet.md:11-13`. The `url` argument goes straight into `http.get(destination, ...)`.

**What the code does:** any logged-in user picks the destination, and the server returns the response body (up to 64 KiB). The contract says the client "performs no destination filtering" and that the application host can reach `10.40.0.15:8080`. That internal service's `/exports/current` route returns "confidential tenant account reports to any caller on that internal network, without another credential."

**Consequence:** any self-registered account can request `/fetch?url=http://10.40.0.15:8080/exports/current` and get back those confidential reports, up to 64 KiB per response. The contract says "no external route otherwise exposes these reports," so this route is the only way in from the internet.

**Controls considered:**
- `require_login` doesn't help, because anyone can self-register.
- `follow_redirects=False` doesn't help, because the attacker names the internal address directly.
- Strict TLS checking and the absence of a proxy don't restrict where requests can go.
- The 64 KiB limit caps each response but doesn't stop the disclosure.
- The process has no host-administrator privilege, but that isn't needed for this read.

**What is not established:** the packet supplies no other internal services. Whether the export includes data from tenants other than the attacker's isn't spelled out either. The consequence above is limited to the named export.

**Fix:**
- Remove the arbitrary-URL capability, or restrict it to an allowlist of schemes, hosts and ports.
- Resolve the hostname and reject private, loopback, link-local and metadata addresses, then connect to the address you checked so DNS rebinding can't swap it.
- As defense in depth, require a credential on `/exports/current`.

**Verification:** add a test that `/fetch` rejects `http://10.40.0.15:8080/...`, other private-range addresses, and hostnames that resolve to private addresses. Do this with a mocked client; don't contact the internal service.

---

## Sample G: `/weather`

**No substantiated security findings in the reviewed scope.**

- The station value must match `[A-Z]{4}` exactly and is sent only as a URL-encoded query parameter.
- The scheme, host and path are fixed, and the contract says accounts can't change the URL, options, DNS or headers.
- Redirects are off, TLS is verified, and the service returns only public data.
- The attacker can't influence the destination, and the response contains nothing sensitive.

**Limits:** I relied on the contract for the client's encoding of `params` and on the trustworthiness of the upstream service.

---

## Sample H: reflected XSS in the account origin (High, High confidence)

**Location:** `review-packet.md:43`. `request.args["message"]` is returned unescaped as `text/html`.

**What the code does:** the `message` parameter becomes the HTML page, so an attacker can put a script in it. The contract says the browser renders it as HTML and that no CSP, sandbox or upstream escaping applies. The route requires no login.

**Consequence:** an attacker sends a crafted `/preview` link to a signed-in victim. The injected script runs in the account interface's origin. Because it's same-origin, it can call the JSON API with the victim's session cookies and read the victim's confidential account details, then send them elsewhere.

**Controls considered:**
- `HttpOnly` stops the script from reading the cookie value. It doesn't stop the script from sending requests that carry the cookie.
- `Secure` and "sessions themselves cannot be forged" are irrelevant, because the attacker rides the real session rather than forging one.

**Prerequisites:** the victim must open the link while signed in.

**What is not established:** the source says "No claim about administrator users or host privileges is supplied." The supported impact is reading the victim's account details through the stated API. Any effect on administrators or state-changing actions would need more evidence.

**Fix:**
- HTML-escape the output (as Sample I does), or serve it as `text/plain` with `X-Content-Type-Options: nosniff`.
- Add a restrictive CSP.
- Consider serving previews from a separate sandbox origin.

**Verification:** check that `/preview?message=<script>…</script>` returns escaped text and a CSP header, and that a script payload doesn't run in a browser test.

---

## Sample I: escaped `/preview`

**No substantiated security findings in the reviewed scope.**

- `html.escape(..., quote=True)` encodes `& < > " '`, and the output sits only between `<p>` tags, so no markup can be injected.
- The contract says nothing decodes or re-inserts the body afterwards.
- `default-src 'none'` would block scripts even if escaping failed.
- `frame-ancestors 'none'` blocks framing.

**Limits:** "Other account handlers are outside the supplied scope," so this result covers only this output path.

---

## Sample J: path traversal and arbitrary file write (High, High confidence)

**Location:** `review-packet.md:70-71`. `ROOT / item.filename` is passed straight to `item.save`.

**What the code does:** the contract says the framework keeps attacker-supplied absolute paths and `..` components, and that `save` writes to the exact path and overwrites existing files. With `pathlib`, `ROOT / "/srv/account-service/config/<file>"` discards `ROOT` entirely, and `../account-service/config/<file>` also escapes it. So any self-registered user can create or overwrite files anywhere the app user can write: `/srv/uploads` and `/srv/account-service/config`.

**Consequence:**
- A user can replace account-service configuration. According to the contract, this "can disable account-service authentication on its next ordinary restart."
- The change takes effect on the next restart. Who can trigger that restart needs validation; the contract says no "immediate restart control is established."
- Inside `/srv/uploads`, the code allows overwriting any file at a path the attacker names. The packet doesn't establish which files exist there or who owns them.

**Controls considered:**
- The 16 KiB body limit restricts how large a written file can be, not where it goes.
- Uploads are never executed or rendered, which rules out code execution through the upload itself.
- No root access, executable directory or symlink attacker is established, so the write reach is exactly the two directories named.

**Severity rationale:** a low-privilege user can disable another service's authentication control. Activation is an ordinary restart rather than something rare. I rate it High rather than Critical because activation timing isn't under the attacker's control (as far as the packet shows) and the write reach is limited to two directories.

**Fix:**
- Ignore the client filename and store each upload under a server-generated name (for example, a UUID).
- If names must be kept, use the Sample K pattern: an allowlist regex, `resolve()` plus `is_relative_to(ROOT)`, and exclusive create (`"xb"`).
- Separately, the application user shouldn't have write access to `/srv/account-service/config`.

**Verification:** check that filenames `/srv/account-service/config/x`, `../account-service/config/x` and `a/../../x` are each rejected or confined to `ROOT`, and that existing files aren't overwritten. Test in a temporary directory.

---

## Sample K: hardened `/upload`

**No substantiated security findings in the reviewed scope.**

- The regex `[A-Za-z0-9_-]{1,48}\.txt` rules out `/`, `..` and absolute paths.
- `resolve()` plus `is_relative_to(ROOT)` (available on Python 3.9+, and the contract states 3.10+) adds a containment check.
- `open("xb")` fails if the file already exists, so nothing can be overwritten.
- The contract rules out replacing directories and creating symlinks or hard links, which covers the usual ways to race the containment check.
- Files aren't executed, rendered, listed or downloadable, so stored content isn't exposed.

**Needs validation:** storage exhaustion. Each upload is 16 KiB, but the packet doesn't say whether there's a per-user count or quota limit, or how much disk is available. To check, confirm whether the edge or the app limits the number of uploads per account.

---

## Review coverage and limits

- **Covered:** destination control and SSRF (F, G), output encoding and CSP (H, I), path containment and overwrite behavior (J, K). Authentication was assessed as the contracts describe it. I didn't inspect the `require_login` implementation.
- **Not run:** no runtime reproduction, browser test, network request or filesystem test. Every conclusion comes from static reading against the supplied contracts.
- **Overall risk:** unrated (not enough context). These are isolated excerpts, not an application.
- **Next action:** fix F, H and J. For J, also confirm who can restart the account service and remove the application user's write access to its config folder.
