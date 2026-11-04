# Security review: `review-packet.md` (synthetic web-boundaries packet)

**Scope:** Only `review-packet.md`, samples F–K, each checked against its own contract. This is a supplied file with no git revision. I only read it: I ran no sample code, made no network calls, and didn't change any files. Helpers behave as the contracts describe.

| Sample | Result | Severity | Confidence |
|---|---|---|---|
| F `/fetch` | SSRF exposes the internal report service | High | High |
| G `/weather` | No substantiated finding | — | — |
| H `/preview` | Reflected XSS lets an attacker read same-origin account data | High | High |
| I `/preview` | No substantiated finding | — | — |
| J `/upload` | Path traversal allows arbitrary overwrite of writable files | High | High (write); see prerequisites |
| K `/upload` | No substantiated finding | — | — |

---

## Sample F: SSRF on `/fetch` (High, confidence High)

**Evidence:** `destination = request.args["url"]` goes straight into `http.get(destination, ...)`, and the response body is returned to the caller. The contract says there is "no destination filtering", that the host can reach `10.40.0.15:8080`, and that `/exports/current` there returns confidential tenant account reports to any caller on that internal network.

**Supported consequence:** Anyone with a self-registered account can request `/fetch?url=http://10.40.0.15:8080/exports/current`. They get back the confidential reports, which no external route otherwise exposes. This crosses the boundary between the internet and the internal network, and it exposes sensitive data.

**Controls and limits on impact:**
- `require_login` stops only anonymous callers, and accounts are self-registered.
- `follow_redirects=False` doesn't matter, because the attacker names the internal URL directly.
- TLS verification doesn't apply to plain HTTP.
- Each response is capped at 64 KiB, so a larger report would be cut off. I'm not claiming the attacker gets the full dataset or every tenant's reports.
- The process has no admin privilege. Nothing here suggests code execution or access to other internal services.

**Fix:**
- Best option: replace the free-form URL with a server-side allowlist of destinations, chosen by an ID.
- If arbitrary URLs are truly needed: resolve the hostname, reject private, loopback, link-local and metadata address ranges, and connect to the IP you checked. That stops DNS rebinding (a hostname that passes the check and then resolves to an internal address). Keep redirects off, or re-check every hop.
- Defense in depth: put authentication on the internal export service, and use network egress rules so this host can't reach it.

**Verify:** Add tests that `10.40.0.15`, `127.0.0.1`, `[::1]`, `169.254.169.254`, decimal and hex forms of IPs, and a hostname that resolves to a private IP are all rejected before any connection is made.

## Sample G: `/weather`: no substantiated finding

The destination is fixed and trusted. `station` must match `[A-Z]{4}` exactly and is passed as an encoded query parameter. Redirects are off, TLS is verified, and the contract says users can't change the URL, options, DNS or headers. The upstream returns only public data and doesn't fetch anything based on the parameter. There's no path to SSRF or injection. Response size is capped and the edge applies rate limiting.

## Sample H: reflected XSS on `/preview` (High, confidence High)

**Evidence:** The raw `request.args["message"]` is returned as `text/html`. The contract says there is no CSP, no sandbox and no escaping, and that the route shares an origin with the signed-in account interface.

**Supported consequence:** An attacker sends a victim a link with script in `message`. If the victim opens it while signed in, the script runs in the app's origin. It can make same-origin requests to the JSON API, which carry the victim's cookies automatically. It can read the victim's confidential account details and send them anywhere.

**Controls and limits on impact:**
- `HttpOnly` stops the script from reading the cookie value. It does **not** stop same-origin authenticated requests.
- `Secure` and the fact that sessions can't be forged don't affect this path.
- The victim has to open the link while signed in.
- I'm not claiming admin takeover, host compromise, or any state-changing action. The contract establishes only that the API returns account details.

**Fix:** HTML-escape the message before output, as sample I does. Better still, return it as `text/plain` and add a restrictive CSP. Serving previews from a separate, sandboxed origin also helps.

**Verify:** A request with `message=<script>…</script>`, or an `<img onerror>` payload, should come back as inert escaped text, and the CSP header should be present.

## Sample I: `/preview` (escaped): no substantiated finding

`html.escape(..., quote=True)` encodes `& < > " '`, and the value lands only in element-content context inside `<p>`. The contract says nothing decodes it or inserts it again later. On top of that, `default-src 'none'` blocks scripts, `base-uri 'none'` stops base-tag hijacking, and `frame-ancestors 'none'` stops the page being framed. There's no route from attacker input to running script. I didn't review the other account handlers, which the packet says are out of scope.

## Sample J: path traversal on `/upload` (High; High confidence in the write itself)

**Evidence:** `destination = ROOT / item.filename` uses a filename the attacker controls, and the framework keeps absolute paths and `..` in it. In `pathlib`, joining an absolute path **throws away** `ROOT`, so `ROOT / "/srv/account-service/config/x"` becomes `/srv/account-service/config/x`. A name like `../account-service/config/x` gets to the same place. `save` writes to that exact path and overwrites whatever is there.

**What the code proves:** Any self-registered user can create or overwrite files, up to 16 KiB each, anywhere the app user can write. That means:
- `/srv/account-service/config`, which is security-sensitive configuration
- any file in `/srv/uploads`, including other users' uploads. Since `save` overwrites, even an ordinary filename that collides with an existing one replaces it, with no traversal needed.

**Conditional follow-on:** Overwriting the config can turn off account-service authentication on the next routine restart.
- Timing is not under the attacker's control. The contract establishes no "immediate restart control".
- Overwriting a particular config file means knowing or guessing its name. The packet doesn't say whether config names are known, or whether a newly created file has any effect.

I rate this **High, not Critical**. The write primitive is proven and the target is security-critical. But the auth bypass waits on an unscheduled restart and on knowing the filename. No root access, no code execution, and no other writable location is established. Uploads are never executed or rendered, so there's no web shell or stored-XSS angle.

**Fix:**
- Never use the client's filename as a path. Generate a server-side name (for example a UUID with a fixed extension) and store the original name only as metadata.
- If you must keep client names: strictly allowlist them, resolve the path and check `is_relative_to(ROOT)`, and open with `O_EXCL` (`"xb"`), as sample K does.
- Separately, remove the app user's write access to `/srv/account-service/config`. That permission isn't needed for uploads.
- If this ever ran in production, audit that config directory for tampering.

**Verify:** Uploads named `/srv/account-service/config/test`, `../account-service/config/test`, `a/../../x`, and a name that collides with an existing upload should all be rejected or harmlessly renamed. The config directory should be unchanged afterwards.

## Sample K: `/upload` (validated): no substantiated finding

- `re.fullmatch(r"[A-Za-z0-9_-]{1,48}\.txt")` rules out `/`, `..`, absolute paths, NUL bytes and other separators.
- `resolve()` plus `is_relative_to(ROOT)` (Python 3.10+) adds a containment check.
- `open("xb")` uses `O_CREAT|O_EXCL`, so it won't overwrite existing files and won't follow a symlink already sitting at the target.
- The trusted parent directories and the ban on users creating symlinks or links remove the remaining race and symlink cases.

**Hardening note (not a vulnerability):** All users share one filename namespace, so one user can claim a name and make another user's upload of the same name fail with a conflict. Files are never listed or served, so this can't leak data. It's at most a minor annoyance. The packet doesn't say whether upload count or total storage is limited per account. A storage-exhaustion concern would need that fact, plus evidence of real impact, before it counts as a finding.

---

## Coverage and limits

- **Coverage:** Static reading of the six excerpts against their contracts. Nothing was run and nothing was reproduced locally.
- **Not reviewed:** The internals of `require_login`, the HTTP client and the framework. I trusted the contracts for all of them.
- **Assumption:** Decorator ordering and routing work as written.
- **Overall risk:** This covers only these synthetic excerpts. There's no basis to rate any wider application.
