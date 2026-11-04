The packet is read, and an independent reviewer is building an evidence map from the source. I'll analyze each sample once that map comes back.

# Security review: review-packet.md

Three of the six samples have a real problem, all rated High: F lets any user read confidential internal reports, H runs attacker-supplied script in a victim's session, and J lets a user overwrite the account service's config. G, I and K have no substantiated findings.

**Scope:** I read only `review-packet.md` (six synthetic excerpts, each with its own contract, no fixed revision). I treated the contracts' helper descriptions as exact. Evidence comes from reading the code only. I also had a separate reviewer pull quotes from the packet without seeing my conclusions, so I could separate stated facts, stated guarantees and gaps. Nothing was run, fetched, installed or changed.

## Summary

| Sample | Result | Severity | Confidence |
|---|---|---|---|
| F – `/fetch` | Server-side request forgery (SSRF) exposes confidential tenant reports | High | High |
| G – `/weather` | No substantiated finding | — | — |
| H – `/preview` | Reflected XSS can read signed-in users' confidential account details | High | High |
| I – `/preview` | No substantiated finding | — | — |
| J – `/upload` | Path traversal lets users overwrite files, including account-service config | High | High |
| K – `/upload` | No substantiated finding (one item needs validation) | — | — |

---

## Sample F: SSRF to the internal report service (High, confidence High)

**Location:** `review-packet.md:11-13`

**Evidence:**
- The `url` query value goes straight into `http.get(destination, …)`, and the response body is returned to the caller.
- The contract says the client "performs no destination filtering".
- The application host can reach `10.40.0.15:8080`.
- `/exports/current` there returns confidential tenant account reports to any caller on that internal network, with no other credential.

**Prerequisites:** an ordinary self-registered account. The contract makes the route internet-facing and open to such accounts.

**Supported consequence:** any registered user can request `/fetch?url=http://10.40.0.15:8080/exports/current` and receive those reports, which the contract says no external route otherwise exposes.

**Controls and why they don't stop it:**
- `follow_redirects=False` doesn't help, because the attacker names the internal URL directly.
- TLS verification only applies to HTTPS; this target is plain HTTP.
- The 64 KiB response limit caps how much one response can return, but doesn't prevent the disclosure.
- The process has no host-administrator privilege, so this is not host compromise.

**Limits:**
- The report size isn't stated, so a single response may be cut off.
- Which tenants' data `/exports/current` covers, and any other internal targets, aren't specified. I haven't assumed cloud metadata or anything else reachable.

**Fix:**
- Replace the free-form URL with an allowlist of approved destinations. If arbitrary fetch is truly needed, resolve the hostname, reject private, loopback, link-local and internal ranges, and pin the connection to the checked address so a DNS change can't swap it later.
- Defence in depth: require authentication on the internal report service.

**Verification:** a test asserting that `/fetch` rejects `http://10.40.0.15:8080/...`, other private-range addresses, and hostnames that resolve to them.

## Sample G: no substantiated security findings

- The destination is fixed.
- `station` must fully match `[A-Z]{4}` and is passed as an encoded query parameter.
- Users can't change the URL, HTTP options, DNS or headers.
- The upstream service returns only public data and makes no further fetches.

There is no attacker-controlled path to a sensitive destination.

**Limit:** the edge rate limit's thresholds aren't specified. That doesn't affect this conclusion.

## Sample H: reflected XSS on the account origin (High, confidence High)

**Location:** `review-packet.md:43`

**Evidence:**
- `request.args["message"]` is returned unescaped as `text/html`.
- No CSP, iframe sandbox or upstream escaping is applied.
- Anyone can create a preview link and send it to someone else.
- The route shares its origin with the signed-in account interface, whose JSON API returns the current user's confidential details.

**Prerequisites:** a signed-in victim opens an attacker-crafted preview link.

**Supported consequence:**
- The attacker's script runs on the account origin.
- It can make same-origin requests to the JSON API, which carry the victim's cookies, and read the confidential details.
- With no CSP, it can send that data out.

**Controls:**
- Secure and HttpOnly cookies stop the script from reading the cookie itself. They don't stop same-origin requests that carry it.
- Sessions can't be forged.
- Stealing the session token or taking over the account is therefore not established. Any impact beyond reading what the API returns depends on API actions the packet doesn't describe.
- The packet makes no claim about administrator users or host privileges, so I haven't rated any escalation through those.

**Limit:** the packet doesn't say whether the JSON API needs anything besides the cookie, such as a CSRF token or custom header. Script running on the same origin can normally get those from the page, but this isn't confirmed.

**Fix (for example, as in Sample I):**
- HTML-escape the message for the context it's inserted into.
- Add a restrictive CSP.
- Preferably, serve previews from a separate, cookieless origin or as `text/plain`.

**Verification:** a test that sends `message=<script>…</script>` and asserts the response body contains `&lt;script&gt;` and that the CSP header is present.

## Sample I: no substantiated security findings

- `html.escape(..., quote=True)` encodes `<`, `>`, `&` and both quote characters, and the value lands in element content (inside the `<p>`).
- The contract guarantees no later decoding or re-insertion, and this is the complete output path.
- `default-src 'none'` would also block script even if escaping failed.

**Limit:** other account handlers are outside the supplied scope.

**Hardening (not a vulnerability):** add `charset=utf-8` and `X-Content-Type-Options: nosniff` to the response.

## Sample J: path traversal file write (High, confidence High)

**Location:** `review-packet.md:70-71`

**Evidence:**
- `ROOT / item.filename` takes the attacker's filename unchanged.
- The framework keeps absolute paths and `..` components.
- In `pathlib`, joining an absolute path replaces `ROOT` entirely, so a filename like `/srv/account-service/config/<file>` targets that file directly.
- `../account-service/config/<file>` reaches the same directory.
- `save` writes to that exact path and overwrites existing files.

**Prerequisites:** a self-registered account and one upload (16 KiB is enough for a config file).

**Supported consequences:**
1. **Demonstrated now:** any user can create or overwrite files in `/srv/uploads` (including other users' uploads) and in `/srv/account-service/config`.
2. **Follow-on:** the contract says overwriting that config "can disable account-service authentication on its next ordinary restart". Because the restart is ordinary, normal operations will trigger it. The attacker just can't choose when.

**Controls limiting impact:**
- The app has no other write privilege and no root.
- Uploaded files are never executed or rendered.
- Immediate restart control is not established.

So this is not code execution or host compromise. I rated it High rather than Critical because the authentication bypass is delayed and depends on a restart.

**Limits:** when restarts happen, and which specific config files matter, aren't stated.

**Fixes:**
- Ignore the client's filename and generate server-side names, or apply K's allowlist, resolve and containment checks.
- Use exclusive creation so existing files can't be overwritten.
- Remove the upload service's write access to `/srv/account-service/config` by running it under a different user.

**Verification:**
- Tests asserting that `/abs/path` and `../x` filenames return 400 and write nothing outside `/srv/uploads`.
- A permission check that the service user can't write to `/srv/account-service/config`.

## Sample K: no substantiated security findings

- The regex `[A-Za-z0-9_-]{1,48}\.txt` excludes `/` and `..`.
- On Python 3.10+, `resolve()` plus `is_relative_to(ROOT)` confirms the path stays inside `ROOT`.
- The guarantee that no symlinks, hard links or directories can be created, and that the parent directories can't be replaced, rules out path-swap races.
- `open("xb")` prevents overwriting, and conflicts are handled.
- Files are never executed, rendered, listed or served.

**Needs validation (storage exhaustion):** the packet gives no disk quota, per-account file count or upload rate limit. A user could fill the disk with many 16 KiB files. Whether that's possible and what it would affect isn't stated.
- **To check:** the volume's capacity and quotas, any upload rate limits, and whether other services share that volume.

**Hardening:** consider per-user or random filenames, so one user can't claim a name another user wants.

---

## Coverage and limits

- **Covered:** each sample's code and its contract, checked independently.
- **Not run:** no code was executed, no network calls were made, and no advisory lookups were done (no dependencies are involved).
- **Not verified:** what `@require_login` actually checks beyond the contracts, how anything is deployed, and runtime behaviour.
- **Overall risk:** findings are rated per sample. **Unrated: insufficient context** for any real application.
