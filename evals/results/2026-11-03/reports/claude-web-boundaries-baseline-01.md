# Security review: `review-packet.md`

**Scope:** I reviewed six synthetic samples (F–K), each against its own contract. The file has no revision; I read its current state. I only read the code: I ran nothing, used no network, and changed no files. I took the helper behavior in each contract as given.

| Sample | Result | Severity | Confidence |
|---|---|---|---|
| F `/fetch` | SSRF exposes internal tenant reports | High | High |
| G `/weather` | No substantiated findings | — | — |
| H `/preview` | Reflected XSS can read the victim's account data | High | High |
| I `/preview` | No substantiated findings | — | — |
| J `/upload` | Path traversal lets uploads overwrite files | High | High |
| K `/upload` | No substantiated findings | — | — |

---

## Sample F: Server-side request forgery (SSRF), High

- **Location:** `review-packet.md:11–13`. The value of `request.args["url"]` goes straight into `http.get(destination, …)`, and the response body is returned to the caller.
- **Path:** Any self-registered user can send `/fetch?url=http://10.40.0.15:8080/exports/current`. The app host can reach that internal service, and the service returns confidential tenant account reports without asking for a credential. The app then sends that content back to the attacker.
- **Controls checked:**
  - `@require_login` only requires that the user has signed in. Anyone can register, so it doesn't restrict this.
  - `follow_redirects=False` doesn't help, because the attacker names the internal URL directly.
  - TLS verification doesn't apply to a plain-HTTP internal URL.
  - The 64 KiB limit cuts large reports short but doesn't stop the leak.
  - No destination filtering is done.
- **What's supported:** A low-privilege outside user can read confidential reports for multiple tenants. These reports aren't reachable from outside any other way. Nothing in the contract supports host compromise or privilege beyond the fetch process.
- **Fix:**
  - Remove the free-form `url` parameter. If the endpoint must stay, allow only specific HTTP/HTTPS hosts.
  - Resolve DNS, reject private, loopback, link-local and metadata addresses, and connect to the IP you validated so DNS rebinding can't swap it.
  - As defense in depth, block the app's outbound access to `10.40.0.0/x` and make the report service require authentication.
- **How to verify:** Add tests that `url=http://10.40.0.15:8080/...`, private/loopback literals, and hostnames that resolve to private addresses all get a 4xx response and never reach the HTTP client.

## Sample G: No substantiated findings

The destination is a fixed HTTPS URL. The only input is `station`, which must fully match `[A-Z]{4}` and is sent as an encoded query parameter. The user can't change the host, path, headers or redirect handling. Per the contract, the upstream service returns only public data and doesn't fetch anything based on the input, so there's no SSRF and no data exposure.

## Sample H: Reflected cross-site scripting (XSS), High

- **Location:** `review-packet.md:43`. The raw `request.args["message"]` is returned as `text/html`.
- **Path:**
  1. An attacker sends a signed-in victim a link like `/preview?message=<script>…</script>`.
  2. The script runs in the account interface's origin.
  3. It can make same-origin requests to the JSON API, which carry the victim's cookies, read the victim's confidential account details, and send them to an outside server. There's no CSP to stop that.
- **Controls checked:**
  - The HttpOnly cookie flag stops the script from reading the cookie, but doesn't stop it making requests as the victim.
  - Sessions can't be forged, but the attack doesn't need a forged session.
  - No CSP, sandbox or escaping applies.
- **Prerequisite:** The victim has to open the link while signed in.
- **What's supported:** The attacker can read the victim's confidential account data. The contract says nothing about admin users or state-changing endpoints, so I make no claim about account takeover or admin compromise.
- **Fix:**
  - HTML-escape the message (as Sample I does) or serve it as `text/plain` with `X-Content-Type-Options: nosniff`.
  - Add a restrictive CSP.
  - Consider serving previews from a separate sandboxed origin.
- **How to verify:** A test that sends `message=<script>x</script>` should get back escaped text (`&lt;script&gt;`) and a CSP header.

## Sample I: No substantiated findings

The message is passed through `html.escape(..., quote=True)` and placed in an element's text, which neutralizes `<`, `>`, `&`, `"` and `'`. The contract says nothing re-decodes it later. Even if markup did get in, `default-src 'none'` blocks scripts and outgoing connections, and `frame-ancestors 'none'` blocks framing.

One optional hardening note: the response could declare `charset=utf-8` and send `nosniff` explicitly. Under the stated contract this doesn't change the result.

## Sample J: Path traversal leading to arbitrary file overwrite, High

- **Location:** `review-packet.md:70–71`. `destination = ROOT / item.filename` is followed by `item.save(destination)`.
- **Path:** The framework keeps the attacker's filename as sent. Either of these escapes `/srv/uploads`:
  - An absolute name such as `/srv/account-service/config/<file>`. With `pathlib`, an absolute right-hand side replaces `ROOT` entirely.
  - A relative name such as `../account-service/config/<file>`.

  `save` overwrites whatever is at that path, and the app user can write to that config directory.
- **What the code demonstrates:** Any self-registered user can overwrite account-service configuration files. They can also overwrite other users' files in `/srv/uploads`. The 16 KiB limit is enough for a config file.
- **Conditional follow-on:** Authentication on the account service is disabled at its next ordinary restart. The attacker can't trigger that restart, so the impact is delayed but expected. There's no code execution, root access, or deployment of executable code.
- **Why High:** It's an unauthenticated-equivalent change to security-critical configuration. The only barrier is a routine restart, which isn't a real defense.
- **Fix:**
  - Ignore the client's filename. Generate a server-side name (such as a UUID), or apply Sample K's controls: a strict allowlist, `resolve()` plus `is_relative_to(ROOT)`, and exclusive create.
  - Separately, remove the upload service's write access to `/srv/account-service/config` by running it as a different user.
  - Review the account-service config for unexpected changes.
- **How to verify:** Tests that upload filenames like `../x`, `/srv/account-service/config/x` and `a/../../x` should get 400 and create no file outside `ROOT`. Also check that the app user can't write to the config directory.

## Sample K: No substantiated findings

- The filename allowlist `[A-Za-z0-9_-]{1,48}\.txt` with `fullmatch` permits no path separators and no `..`.
- `resolve()` plus `is_relative_to(ROOT)` adds a second containment check.
- The `"xb"` mode (exclusive create) refuses to overwrite existing files.
- Per the contract, attackers can't create symlinks or hard links and can't replace the parent directories.
- Files are never executed, rendered or served back.

One optional hardening note: there's no per-user quota, but the contract gives no disk-capacity impact, so I'm not reporting it.

---

**Coverage and limits:**
- I only read the code. I reproduced nothing and probed nothing; the internal address in F was never contacted.
- Conclusions rely on each contract's descriptions of helpers, the framework and the deployment (for example `http.get` limits, `save` semantics, and `require_login` behavior).
- Controls outside these excerpts were not visible, such as other middleware, edge filtering, and CSRF or other account endpoints.
- Overall risk is **Unrated: insufficient context**, because this was a review of isolated synthetic samples, not an application.
