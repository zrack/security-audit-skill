# Security review: `review-packet.md` (Samples F–K)

**Scope:** I read only `review-packet.md`, a synthetic packet with six separate excerpts. I judged each sample against its own contract. There is no immutable revision. I used static inspection only: I ran no code, made no network contact, installed nothing and changed no files. I took the helper behaviour described in the contracts as given.

## Summary

| Sample | Result | Severity | Confidence |
|---|---|---|---|
| F `/fetch` | SSRF that discloses confidential tenant reports | High | High |
| G `/weather` | No substantiated finding | — | — |
| H `/preview` | Reflected XSS that can read the victim's confidential account details | High | High |
| I `/preview` | No substantiated finding | — | — |
| J `/upload` | Path traversal lets a user overwrite files in the account-service config directory | High | High |
| K `/upload` | No substantiated finding | — | — |

---

## Sample F: SSRF to the internal report service — High, confidence High

**Location:** review-packet.md:11–13 (`destination = request.args["url"]` passed directly to `http.get`).

**What the code does:** Any self-registered, logged-in user picks the full request URL. The client "performs no destination filtering" (contract, line 16). The route returns the response body to the caller.

**Supported consequence:** The application host can reach `10.40.0.15:8080`. That service's `/exports/current` route "returns confidential tenant account reports to any caller on that internal network, without another credential." So a request to `/fetch?url=http://10.40.0.15:8080/exports/current` hands those reports to an ordinary self-registered account. The contract also says "No external route otherwise exposes these reports," so this route crosses a real trust boundary.

**Controls and limits from the contract:**
- `@require_login` does not help, because accounts are self-registered.
- Each response is capped at 64 KiB. That limits how much one request returns, not whether data is exposed.
- Redirects are not followed and there is no proxy.
- The process has "no host-administrator privilege."

I did not rate any other internal targets, because none are established.

**Fix:**
- Replace the free-form URL with a server-side allowlist of destinations.
- If arbitrary public fetches are truly needed: resolve the hostname, reject private, loopback, link-local and reserved addresses, and connect to the checked address so DNS rebinding can't swap it.
- As defence in depth, block the app host's egress to `10.40.0.0/16`, and require a credential on the report service.

**Verification:** Add a unit test with a stubbed resolver. `http://10.40.0.15:8080/...`, private-range literals, and hostnames that resolve to private addresses should all be rejected before `http.get` is called. Allowed destinations should still work.

---

## Sample G: `/weather` — no substantiated finding

The destination is fixed. `station` must fully match `[A-Z]{4}` and is sent as an encoded query parameter. Per the contract, accounts "cannot modify this URL, HTTP options, DNS configuration, or request headers." Redirects are off, TLS is verified, and the service returns only public data. The user controls no destination, so there is no SSRF. Edge rate limiting and the 64 KiB cap also bound misuse as an amplifier.

---

## Sample H: reflected XSS on the account origin — High, confidence High

**Location:** review-packet.md:43. `request.args["message"]` is returned unescaped as `text/html`.

**What the code does:** Attacker-chosen markup is rendered as HTML on the same origin as the signed-in account interface. Nothing blunts it: the contract says "No CSP, iframe sandbox, or upstream escaping is applied." The route needs no login, and the contract says anyone can craft the link and send it to someone else.

**Supported consequence:** A victim who opens the link while signed in runs the attacker's script in the account origin. Same-origin requests carry the victim's cookies, so the script can call the JSON API, read the victim's confidential account details, and send them elsewhere.

**Controls and limits:**
- The `HttpOnly` flag stops the script from reading the session cookie itself. It does not stop same-origin authenticated requests.
- The contract says sessions can't be forged.
- The attack needs a victim to open the link while signed in.

**Open questions:**
- Can the script also make state-changing requests? That depends on account endpoints not supplied here.
- The contract says "No claim about administrator users or host privileges is supplied," so the impact on privileged users is unknown.

**Fix:** HTML-escape `message` before inserting it into a fixed template, or return it as `text/plain` with `X-Content-Type-Options: nosniff`. Add a restrictive CSP such as `default-src 'none'`. Ideally, serve user-controlled previews from a separate, cookieless origin. Sample I's approach is a sound pattern.

**Verification:** A test should request `/preview?message=<script>x</script><img src=x onerror=y>` and assert that the body contains only escaped entities and that the CSP header is present.

---

## Sample I: `/preview` with escaping and CSP — no substantiated finding

`html.escape(..., quote=True)` encodes `& < > " '`. The value lands only in HTML element content inside `<p>`. The contract says no script later decodes or re-inserts it. On top of that, the CSP `default-src 'none'` blocks script, and `frame-ancestors 'none'` prevents framing. This is the complete output path, and there is no route to injection. Other account handlers are outside the supplied scope.

---

## Sample J: path traversal and arbitrary overwrite — High, confidence High

**Location:** review-packet.md:70–71 (`ROOT / item.filename` followed by `item.save(destination)`).

**What the code does:** The framework keeps the attacker's filename, "including absolute paths and `..` components," and `save` overwrites whatever is at that exact path.

- In `pathlib`, joining an absolute path discards the base. So `ROOT / "/srv/account-service/config/<name>"` resolves to that config path.
- `../account-service/config/<name>` escapes `ROOT` the same way.

**Supported consequence:** Any self-registered user can write or overwrite files, up to 16 KiB each, in the two places the app user can write: `/srv/uploads` (including other users' uploads) and `/srv/account-service/config`. The contract says overwriting configuration there "can disable account-service authentication on its next ordinary restart."

**Activation and prerequisites:**
- The damage takes effect at the next ordinary restart. Who can trigger a restart is not established: the contract says "No ... immediate restart control is established."
- To overwrite an existing config file, the attacker needs its filename. The packet doesn't supply an inventory of that directory.
- The contract rules out wider effects: "No root privilege, executable deployment directory, symlink attacker" is established, the app has no other write privilege, and uploads are "never executed or rendered."

**Fix:**
- Never use the client filename as a path. Generate a server-side name, such as a UUID with a validated extension, and store the original name only as metadata. Alternatively, apply Sample K's allowlist, resolve and `is_relative_to` checks.
- Use exclusive creation (`"xb"`) so existing files can't be overwritten.
- Least privilege: remove the upload service's write access to `/srv/account-service/config`.

**Verification:**
- Tests should send filenames `/srv/account-service/config/x`, `../account-service/config/x` and `a/../../x`, and assert a 400 response with nothing written outside `ROOT`.
- A test should confirm that a duplicate name cannot overwrite an existing file.
- Confirm the filesystem permission change on the deployed host.

---

## Sample K: hardened upload — no substantiated finding

The filename must fully match `[A-Za-z0-9_-]{1,48}\.txt`, which excludes `/`, `..` and absolute paths. The resolved destination is also checked with `is_relative_to(ROOT)`, which exists on Python 3.10+.

`open("xb")` refuses to overwrite existing files, and the contract says conflicts are handled. The contract also says the upload tree can't be replaced and that users can't create symlinks, hard links or directories, so there's no race or link path to exploit. Files are never executed, rendered, listed or downloadable, and size is capped at the edge. I found no route to traversal or overwrite.

---

## Review coverage and limits

- **Evidence is static only.** No sample was run, and no internal or `.invalid` address was contacted. The findings rely on the helper contracts as written: the HTTP client, the multipart framework's handling of `save`, and the edge limits.
- **Not reviewed:** the internals of `require_login`, other account handlers and endpoints, how the account service restarts, the contents of its config directory, and deployment details beyond what the contracts state.
- **Overall risk:** I didn't give one rating for an application, because these are independent excerpts. Each finding's rating is for its own sample only.

**Next steps:**
1. Fix F, H and J as described above.
2. For J, find out who can trigger an account-service restart, and audit `/srv/account-service/config` for files that may already have been tampered with.
