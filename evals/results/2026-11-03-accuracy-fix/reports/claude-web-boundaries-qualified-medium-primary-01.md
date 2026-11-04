# Security review: review-packet.md

**Scope:** I reviewed only `review-packet.md`, which holds six independent synthetic samples (F–K), each judged against its own contract. I only read the code. I did not run any sample, use the network, install anything, or change files. There is no revision or repository to pin the review to: the evidence is the packet text plus its contracts, and the helpers are taken to behave exactly as the contracts say.

| Sample | Result | Severity | Confidence |
|---|---|---|---|
| F `/fetch` | Server-side request forgery (SSRF) exposes the internal reports | High | High |
| G `/weather` | No substantiated findings | — | — |
| H `/preview` | Reflected cross-site scripting (XSS) reads the victim's account data | High | High |
| I `/preview` | No substantiated findings | — | — |
| J `/upload` | Path traversal lets users overwrite files | High | High |
| K `/upload` | No substantiated findings | — | — |

---

## Sample F: SSRF to the internal report service (High, High confidence)

**Evidence:** `destination = request.args["url"]` goes straight into `http.get(destination, ...)`, and `result.content` is sent back to the caller (packet lines 11–13). The contract says the client "performs no destination filtering," the route is open to "ordinary self-registered accounts," and the app host can reach `10.40.0.15:8080`. On that service, `/exports/current` "returns confidential tenant account reports to any caller on that internal network, without another credential."

**Supported consequence:** Anyone who self-registers can request `/fetch?url=http://10.40.0.15:8080/exports/current` and get those reports back through an outside route. The contract says no outside route otherwise exposes them. This is a confidentiality breach across a network trust boundary.

**Controls and limits on the impact:**
- `require_login` stops anonymous callers, but self-registration makes that a weak barrier.
- The 64 KiB response limit caps each response. Whether one response holds a complete report, or how much of one, is not established.
- Not following redirects doesn't help, because the attacker can name the internal address directly.
- The process "has no host-administrator privilege," so I make no claim about compromising the host.
- I am not claiming access to other internal destinations, or to every tenant's data, beyond what the contract describes.

**Fix:** Replace the free-form URL with a server-side allowlist of permitted destinations. If arbitrary outside fetches are truly needed, resolve the hostname, reject private, loopback, link-local and metadata address ranges, and connect to the address that was checked, so that DNS rebinding can't swap it. Separately, add authentication to the internal `/exports/current` route and restrict the fetch process's outbound network access, so the internal service no longer trusts any caller on its network.

**Verification:** A test that requests `/fetch` with `url=http://10.40.0.15:8080/exports/current`, and with private or loopback addresses including ones reached through a hostname, should get a rejection and no outbound request.

---

## Sample G: `/weather` (no substantiated findings)

The station value has to match `[A-Z]{4}` exactly, and it is sent as an encoded query parameter (`params=`). The URL is fixed and points to a trusted operator. The contract says accounts "cannot modify this URL, HTTP options, DNS configuration, or request headers." TLS is verified, redirects aren't followed, and the upstream returns only public data. A user can't choose where the request goes or add anything to it, so there is no SSRF or injection path. Edge rate limiting and the 64 KiB cap limit abuse as an amplifier.

---

## Sample H: reflected XSS on the account interface's origin (High, High confidence)

**Evidence:** `request.args["message"]` is returned unescaped as `text/html` (packet line 43). The contract says any user may send a preview link to someone else, the browser renders the response as HTML, and "No CSP, iframe sandbox, or upstream escaping is applied." The route "shares its origin with a signed-in account interface whose JSON API returns the current user's confidential account details."

**Supported consequence:** The attacker writes a script into `message` and sends the link. When a signed-in victim opens it, the script runs on the application's own origin. Because the request is same-origin, it can call the JSON API with the victim's session cookies attached, read the victim's confidential account details, and send them to the attacker, since no CSP limits outbound connections.

**Controls and limits on the impact:**
- `HttpOnly` stops the script from reading the cookie itself. It does not stop the browser from attaching that cookie to the script's same-origin API requests.
- `Secure`, and the fact that sessions can't be forged, do not stop this.
- The victim has to open the link while signed in.
- "No claim about administrator users or host privileges is supplied," so I rate this as exposure of the victim's own account data. I am not claiming administrator takeover.
- The contract describes no state-changing API, so I don't claim unauthorized actions.

**Fix:** HTML-escape `message` for the element context it lands in, as Sample I does. Add a restrictive CSP as defense in depth. Better still, serve user-controlled previews from a separate sandbox origin, or as `text/plain`.

**Verification:** Request `/preview?message=<script>…</script>` and `message=<img src=x onerror=…>`. Confirm the markup comes back as escaped text, the CSP header is present, and no script runs.

---

## Sample I: `/preview` (no substantiated findings)

`html.escape(..., quote=True)` encodes `& < > " '`, and the output goes only into element text inside `<p>…</p>`, so the message can't break out into markup. The contract says the body arrives exactly as shown and "no script later decodes or re-inserts it." Separately, `default-src 'none'` would block script execution and outbound connections even if escaping failed, `base-uri 'none'` prevents base-tag hijacking, and `frame-ancestors 'none'` prevents framing. Other account handlers are explicitly outside the supplied scope.

---

## Sample J: path traversal lets users overwrite files (High, High confidence)

**Evidence:** `destination = ROOT / item.filename`, then `item.save(destination)` (packet lines 70–71). The contract says the framework "preserves the attacker-supplied filename, including absolute paths and `..` components," and that `save` writes to the exact path and overwrites existing files. In `pathlib`, joining an absolute right-hand path throws away `ROOT` entirely. So both `/srv/account-service/config/<file>` and `../account-service/config/<file>` end up outside the upload root.

**Supported consequence (proven):** Any self-registered user can overwrite files in `/srv/account-service/config` with up to 16 KiB of content they choose. They can also overwrite other users' files in `/srv/uploads`. Writes anywhere else fail because of the application user's permissions.

**Conditional follow-on effect:** Overwriting that config "can disable account-service authentication on its next ordinary restart." The contract also says "No … immediate restart control is established." So bypassing authentication depends on a restart that the attacker doesn't control. I rate this High because the attacker has unauthorized write access to configuration that controls authentication, not because the bypass happens immediately.

The contract establishes no root privilege, executable directory, or symlink attacker, and uploads are never executed or rendered. I make no claim of code execution.

**Fix:**
- Never use the client's filename as the path. Generate a server-side name (for example a UUID) and keep the original name only as metadata.
- If a supplied name has to be kept, apply a strict filename allowlist, resolve the path, check containment, and open with exclusive create, as Sample K does.
- Remove the upload process's write permission on `/srv/account-service/config`. Then review that directory's config files for tampering before the next restart.

**Verification:** Upload files named `/srv/account-service/config/test`, `../account-service/config/test` and an existing upload's name. All three should be rejected, and nothing outside `/srv/uploads` should change.

---

## Sample K: `/upload` (no substantiated findings)

The filename has to match `[A-Za-z0-9_-]{1,48}\.txt` exactly, so it can't contain `/`, `..` or an absolute path. The resolved path is also checked with `is_relative_to(ROOT)`, which is available in Python 3.10 and later. Opening with `"xb"` refuses to overwrite an existing file, and the contract says that case gets a handled conflict response. A trusted administrator owns the root and its parent directories, and users can't create symlinks, hard links or directories. That rules out swapping a link in between the check and the write. Size is capped at 16 KiB at the edge, and files are never executed, rendered, listed or offered for download.

---

## Coverage and limits

- **What I checked:** for each sample, whether attacker input reaches the sensitive action, what the contract says about each control, and what consequence the code and contract actually support.
- **Relied on, not checked:** I took the contracts' descriptions of the helpers as given: the HTTP client's limits and TLS checks, `require_login`, the multipart framework, `save`, the edge limits, and the session or cookie behaviour. I didn't look at their real implementations.
- **Not done:** no live reproduction, network probing or dependency review, as you asked.
- **Overall risk:** **Unrated: insufficient context.** The samples are synthetic excerpts, so these results don't rate any real application.
