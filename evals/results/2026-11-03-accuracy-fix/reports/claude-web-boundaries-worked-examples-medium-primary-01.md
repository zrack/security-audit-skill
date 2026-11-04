# Security review: review-packet.md

Three of the six samples have security findings (F, H and J). The other three (G, I and K) have none under their stated contracts.

**Scope:** I reviewed only `review-packet.md`, which has six separate synthetic samples (F–K). There was no fixed revision, just the file as it stands now. I only read the code and contracts: I didn't run anything, use the network or change any files. Where a contract describes how a helper behaves, I took it as given.

## Summary

| Sample | Result | Severity | Confidence |
| --- | --- | --- | --- |
| F `/fetch` | Server-side request forgery (SSRF) that exposes the internal tenant reports | High | High |
| G `/weather` | No substantiated findings | — | — |
| H `/preview` | Reflected cross-site scripting (XSS) that can read the victim's account details | High | High |
| I `/preview` | No substantiated findings | — | — |
| J `/upload` | Path traversal letting an upload overwrite files, including the account-service config | High | High |
| K `/upload` | No substantiated findings | — | — |

---

## Sample F: `/fetch`, SSRF (High, confidence High)

**Location:** `review-packet.md`, lines 11–13 (`destination = request.args["url"]` → `http.get(destination, ...)` → the response body is returned).

**Evidence:** The caller controls the whole URL. The contract says the client does no destination filtering, and the app host can reach `10.40.0.15:8080`. That service's `/exports/current` route returns confidential tenant account reports to anyone on the internal network, with no other credential.

**Prerequisites:** Any self-registered account, which on an internet-facing route anyone can get. No victim needs to do anything.

**Supported consequence:** Requesting `/fetch?url=http://10.40.0.15:8080/exports/current` sends back the confidential tenant reports, up to the 64 KiB response limit. No other external route exposes those reports. This is serious exposure of confidential data across tenants.

**What doesn't help, and what isn't established:**
- Turning off redirects doesn't help, because the attacker can name the internal host directly.
- The 64 KiB limit caps how much comes back per request but doesn't stop the leak.
- The contract doesn't say whether other internal services are reachable, and the process has no host-administrator privilege. So nothing supports host compromise or reach beyond this report service.

**Fix:**
- Replace the free-form URL with a server-side allowlist of destinations, or remove the endpoint.
- If arbitrary public fetches really are needed:
  - Resolve the hostname first, reject private, loopback, link-local and metadata address ranges, and connect to the IP you checked so DNS rebinding can't swap it.
  - Keep redirects off, or re-check each hop.
- Separately, have the report service require its own credential rather than trusting anything on the network.

**Verification:** Add a test showing that internal-address URLs (`10.0.0.0/8`, loopback, link-local, IPv6 equivalents and hostnames that resolve to them) are rejected before any connection is made.

---

## Sample G: `/weather`, no substantiated findings

The destination is fixed and trusted, and the caller can't change the URL, HTTP options, headers or DNS. The only user input, `station`, must be exactly four uppercase letters (`re.fullmatch`) and is sent as an encoded query parameter. The contract says the upstream service returns only public data and makes no further fetches based on that value. So user input never selects where a request goes, and the response contains nothing sensitive.

---

## Sample H: `/preview`, reflected XSS (High, confidence High)

**Location:** line 43. `request.args["message"]` is returned as-is with `content_type="text/html"`.

**Evidence:** Nothing is escaped, and there's no CSP or sandbox. The route shares its origin with the signed-in account interface, and that interface's JSON API returns the current user's confidential account details.

**Prerequisites:** The attacker writes a `message` containing script and gets a signed-in victim to open the link. The contract allows any user to send preview links to others.

**Supported consequence:** The script runs in the victim's browser on the application's origin. Because it's a same-origin request, the browser attaches the victim's session cookie when the script calls the JSON API. The script can read the response, which holds the victim's confidential account details. With no CSP, it can then send that data to an attacker-controlled server.

**What doesn't help, and what isn't established:**
- HttpOnly cookies stop the script from reading the cookie value itself. They don't stop same-origin requests that carry the cookie.
- Sessions can't be forged, but that's irrelevant here because the victim's own session is used.
- The contract doesn't say whether the API can also make changes, or whether any users are administrators. So I'm not claiming state-changing actions or admin compromise.

**Fix:**
- HTML-escape the message (as Sample I does), or serve it as `text/plain` with `X-Content-Type-Options: nosniff`.
- Add a restrictive CSP as a second layer of defense.

**Verification:** A test showing that a message like `<script>…</script>` or `<img src=x onerror=…>` comes back as inert escaped text, and that the response includes the CSP header.

---

## Sample I: `/preview`, no substantiated findings

`html.escape(..., quote=True)` escapes `& < > " '`, and the output only ever appears as text inside a `<p>` element, so the input can't break out into markup. The contract says no script later decodes or re-inserts the body. Even if markup somehow got through, the CSP blocks scripts, network requests, `<base>` tampering and framing. All an attacker can do is choose the text shown on the page. That isn't a security failure here.

---

## Sample J: `/upload`, path traversal and arbitrary file overwrite (High, confidence High)

**Location:** lines 70–71 (`destination = ROOT / item.filename` → `item.save(destination)`).

**Evidence:** The filename is kept exactly as the attacker sent it, including absolute paths and `..` components. In `pathlib`, joining an absolute path replaces the base, so a filename of `/srv/account-service/config/<file>` writes there. A relative `../account-service/config/<file>` does the same. `save` writes to that exact path and overwrites existing files. The application user can write to `/srv/account-service/config`.

**Prerequisites:** Any self-registered account. The 16 KiB upload limit doesn't stop this, because config files are small.

**Supported consequences:**
- **Shown by the code:** Any user can overwrite or create files in `/srv/account-service/config`, and can overwrite other users' files in `/srv/uploads`. That is unauthorized change to security-relevant configuration.
- **Conditional:** Per the contract, the planted config disables account-service authentication at the next ordinary restart. The attacker can't trigger a restart, so the bypass only takes effect whenever one next happens. What becomes reachable once authentication is off isn't specified.
- **Not supported:** Nothing shows code execution, root access, or writes outside the two directories listed above.

I rated it High rather than Critical because the authentication bypass depends on a later restart, and how far it reaches after that isn't established.

**Fix:**
- Never use the client's filename as the path. Generate a server-side name, for example a random ID with a fixed extension, and store the original name separately if it's needed.
- If client names must be kept, use Sample K's pattern: a strict name pattern, a resolved-path containment check, and exclusive create.
- Run the upload service under an account that can't write to `/srv/account-service/config`.
- Check the integrity of the account-service config before it next restarts.

**Verification:** Tests showing that filenames that are absolute paths, contain `..` or contain separators are rejected, and that nothing is written outside `/srv/uploads`.

---

## Sample K: `/upload`, no substantiated findings

- **Filename:** The pattern `[A-Za-z0-9_-]{1,48}\.txt` allows no path separators, so absolute paths and `..` traversal are impossible.
- **Containment:** After resolving, the `is_relative_to(ROOT)` check confirms the file stays inside `/srv/uploads` (supported on Python 3.10, as the contract states).
- **Overwrites:** `open("xb")` refuses to overwrite an existing file.
- **Links and races:** The contract rules out symlinks, hard links, directory creation and swapped parent directories, so the gap between the check and the write can't be exploited.

Files are never executed, rendered or served. The contract doesn't state a per-user upload quota or disk capacity. Without those, I can't support a disk-exhaustion finding, and I'm not reporting one.

---

## Coverage and limits

- **How I checked:** Only by reading `review-packet.md` and its contracts. Nothing was run or tested live.
- **Taken on trust:** Helper behavior and `@require_login` as described in each contract. I didn't look at any other files.
- **No overall rating:** The samples are synthetic excerpts, not one application, so there's no overall application risk rating (unrated: insufficient context).

**Next step:** Fix F, H and J as described above, and add the verification tests listed for each.
