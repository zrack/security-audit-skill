I've written a first draft of the review. An independent reviewer is now checking its factual claims against the packet. I'll finish the report once that check comes back.

# Security review: `review-packet.md` (synthetic samples F–K)

Three of the six samples have a real problem, all rated High: F lets any user fetch confidential internal reports, H lets an attacker read a victim's account details through a crafted link, and J lets any user write into the account service's config directory. G, I and K have no substantiated findings.

**Scope.** I only read `review-packet.md` and judged each sample against its own contract, treating the helpers as behaving exactly as described. I didn't run code, use the network, install anything or change any file. There's no fixed revision because the packet was supplied as text. A second reviewer independently fact-checked the draft against the packet, and its one correction (the 64 KiB limit in F) is included below.

| Sample | Result | Severity | Confidence |
|---|---|---|---|
| F `/fetch` | SSRF (server-side request forgery) reaching the internal report service | High | High |
| G `/weather` | No substantiated finding | — | — |
| H `/preview` | Reflected XSS (cross-site scripting) on the account origin | High | High |
| I `/preview` | No substantiated finding | — | — |
| J `/upload` | Path traversal lets users write files outside the upload folder | High | High |
| K `/upload` | No substantiated finding | — | — |

---

## Sample F: SSRF to the internal report service (High, confidence High)

**What goes wrong.** The route passes `request.args["url"]` straight to `http.get` with no destination filtering. Any self-registered user can request `/fetch?url=http://10.40.0.15:8080/exports/current`. Per the contract:
- the app host can reach that service;
- the service hands confidential tenant account reports to any caller on the internal network without another credential;
- the app returns the response body as-is.

**Consequence.** A low-privilege, self-registered account can read confidential tenant reports that no external route otherwise exposes.

**Controls that don't stop it:**
- `@require_login`: anyone can register.
- `follow_redirects=False`: the attacker supplies the internal URL directly, so no redirect is needed.
- TLS verification: the internal target is plain HTTP.

**Control whose effect is unknown:** the 64 KiB response limit. The contract doesn't say whether a larger response gets cut off or rejected, or how big the exports are. Reports within the limit come back in full. For a larger report, the attacker gets either the first 64 KiB or nothing.

**Not claimed:** host compromise, access to other internal services, or any write access.

**Fix:**
- Replace the free-form URL with an allowlist of destinations or IDs.
- If arbitrary fetches really are needed:
  - resolve DNS once;
  - reject private, loopback, link-local and metadata addresses;
  - connect to the IP you checked, so a DNS change can't swap it afterwards.
- Separately, block this process from reaching `10.40.0.15` at the network level, and require authentication on the report service.

**Verify:** tests showing that private, loopback and internal URLs are rejected, including hostnames that resolve to those addresses.

## Sample G: no substantiated finding

`station` must be exactly four uppercase letters and is sent as a query parameter to a fixed, trusted HTTPS host. Users can't change the URL, headers, DNS or redirect behaviour, the data is public, and the edge rate-limits requests. A missing `station` causes a framework error; the exact status code isn't established, and it isn't a security issue.

## Sample H: reflected XSS on the account origin (High, confidence High)

**What goes wrong.** The route takes `message` from the query string and returns it raw as `text/html`. There's no escaping, CSP (Content Security Policy) or sandbox, and the page shares an origin with the signed-in account interface.

**Attack path.**
1. The attacker sends a crafted preview link.
2. A signed-in victim opens it.
3. The attacker's script runs in the app's own origin.
4. It calls the same-origin JSON API, and the browser attaches the session cookies automatically.
5. It reads the victim's confidential account details and sends them out; nothing in the page blocks that.

**Why the cookie settings don't help.** HttpOnly stops the script from reading the cookie value, but not from making same-origin requests that carry the cookie. Secure doesn't matter here.

**Not claimed:** admin takeover, session forgery or host compromise. State-changing actions would depend on API endpoints the packet doesn't include.

**Fix:**
- Escape the output, as in sample I, or serve it as `text/plain`.
- Add a restrictive CSP.
- Consider serving user-supplied content from a separate origin.

**Verify:** `<script>` and `<img onerror=…>` payloads come back escaped, and the CSP header is present.

## Sample I: no substantiated finding

`html.escape(..., quote=True)` is enough inside element text. The `default-src 'none'` CSP blocks script as a second layer, and the contract rules out anything decoding or re-inserting the output later. Other account handlers are outside the supplied scope.

## Sample J: path traversal lets users write files outside the upload folder (High, confidence High)

**What goes wrong.** With `pathlib`, `ROOT / "/srv/account-service/config/X"` replaces the root with that absolute path, and `"../account-service/config/X"` climbs out of `/srv/uploads`. `save` then writes to that path and overwrites whatever is there.

**What's demonstrated.** Any self-registered user can:
- create or overwrite files of up to 16 KiB in `/srv/account-service/config`;
- overwrite other users' files in `/srv/uploads`.

**Conditional consequences:**
- The contract says overwriting the config "can disable account-service authentication on its next ordinary restart". That bypass is delayed, because the attacker doesn't control when the service restarts. It also requires knowing a config filename and content that would have that effect, which the packet doesn't give.
- Writing junk into the config could also break the account service on its next restart.

**Not claimed:** code execution, root access, or writes anywhere else. It's rated High rather than Critical because the auth impact waits on a restart the attacker can't trigger and needs config knowledge the packet doesn't establish. The packet also doesn't say the account service is internet-facing.

**Fix:**
- Generate filenames on the server, or apply K's strict filename check plus the resolved-path check.
- Create files exclusively, so existing ones are never overwritten.
- Remove the app user's write access to `/srv/account-service/config`.
- Inspect that config directory and restore known-good files before the next restart.

**Verify:** tests showing that absolute names and `../` names are rejected, plus a filesystem permission check.

## Sample K: no substantiated finding

The controls hold:
- `fullmatch` only allows a plain `.txt` filename with no directory parts.
- `resolve()` plus `is_relative_to` (Python 3.10) keeps writes inside the root.
- Opening with `"xb"` refuses to overwrite an existing file.
- Per the contract, the parent directories are trusted, and users can't create links or directories.

Two observations that aren't vulnerabilities:
- **Shared filenames:** all users share one filename space, so one user can claim a name before another. Impact is limited because files are never exposed.
- **No storage quota:** none is stated, but disk exhaustion is not established as an impact.

---

## Coverage and limits

- **Evidence:** static analysis only, against contract-defined behaviour. Nothing was reproduced at runtime.
- **Not reviewed:** how `require_login` works internally, framework error handling, and anything outside each sample's contract.
- **Overall risk:** not rated. These are separate synthetic excerpts, not one application.
