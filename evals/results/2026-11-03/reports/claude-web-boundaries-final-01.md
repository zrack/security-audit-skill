# Security review: `review-packet.md`

## Scope

- **Target:** only `review-packet.md`. It holds six synthetic Python/Flask-style excerpts (Samples F to K), each with its own contract. There is no revision or repository; it is a supplied artifact.
- **Method:** I read the code and contracts only. I ran nothing, used no network, installed nothing, opened no other files and changed nothing.
- **Basis:** I took each sample's contract as true, as the packet says to. Every conclusion rests on that.

## Summary

| Sample | Result | Severity | Confidence |
|---|---|---|---|
| F `/fetch` | SSRF exposes confidential internal tenant reports | High | High |
| G `/weather` | No substantiated finding | n/a | n/a |
| H `/preview` | Reflected XSS lets an attacker read the victim's confidential account details | High | High |
| I `/preview` | No substantiated finding | n/a | n/a |
| J `/upload` | Path traversal lets a user overwrite account-service config | High | High |
| K `/upload` | No substantiated finding | n/a | n/a |

---

## Sample F: `/fetch` lets any account read internal reports (SSRF)

**Severity:** High. **Confidence:** High (static analysis plus the contract).

**What the code does:** the `url` query parameter goes straight to `http.get(destination, ...)` (packet lines 11–12). The contract says the client does no destination filtering, and the route sends the fetched body back to the caller.

**How an attack works:**
- **Who:** anyone with an ordinary self-registered account. Signing up is the only barrier, so `@require_login` adds no real protection.
- **How:** request `/fetch?url=http://10.40.0.15:8080/exports/current`. The application host can reach that internal service. The service returns confidential tenant account reports to anyone on the internal network without asking for a credential.
- **What the attacker gets:** those reports, read through a route the internet can reach. The contract says no external route otherwise exposes them, so this crosses a real trust boundary.

**Limits on the impact:**
- Each response is capped at 64 KiB, so a larger report would come back truncated.
- Turning off redirects does not help here, because the attacker names the internal URL directly.
- These are not established: other internal services, cloud metadata endpoints, code execution, or anything at host-administrator level (the contract denies that privilege).

**Fix:**
- Best: remove arbitrary-URL fetching, or limit it to a server-side allowlist of exact hosts and schemes.
- If any user-chosen destination must stay: resolve the hostname, reject private, loopback, link-local and other internal ranges, then connect to the address you checked. Checking and then resolving again would allow DNS rebinding.
- Defense in depth: require authentication on the internal `/exports/current` service.

**How to verify:** in an isolated test setup, confirm that internal-address URLs, decimal or IPv6 forms of internal addresses, and hostnames that resolve to internal addresses are all rejected before any connection is made.

## Sample G: `/weather`, no substantiated security findings

**Why it holds:**
- The scheme, host and path are fixed. The only input, `station`, must match `[A-Z]{4}` exactly and is sent as an encoded query parameter.
- TLS is verified and redirects are off.
- The contract says the upstream is trusted, returns only public data and makes no further fetches based on `station`. Users cannot change the URL, the request options, DNS or headers.

So there is no route to an attacker-chosen destination. Abuse through volume is limited by the edge rate limit.

**Limit:** this relies on the contract's claims about how the upstream operator controls DNS and TLS.

## Sample H: `/preview` reflected XSS reads confidential account details

**Severity:** High. **Confidence:** High.

**What the code does:** the `message` parameter is returned unescaped as `text/html` (packet line 43). The contract confirms there is no CSP, no sandbox and no upstream escaping.

**How an attack works:**
- **Who:** any user can build a preview link with a script in `message`.
- **Victim step:** someone signed in to the account interface opens the link. This user interaction is the main prerequisite.
- **What runs:** the script runs in the same origin as the account interface. It can call that interface's JSON API, and the browser attaches the victim's session cookies automatically. The script can then read the response, because it is same-origin.
- **What the attacker gets:** the victim's confidential account details. With no CSP, nothing stops the script from sending them to the attacker.

**Controls considered:**
- HttpOnly stops the script from reading the cookie itself. It does not stop the script from making authenticated requests with it.
- The Secure flag and the fact that sessions cannot be forged don't change this, because the attack uses the victim's real session inside their own browser.

**Not established:**
- State-changing actions as the victim: the contract describes only a read API.
- Any administrator-specific impact or host access.

**Fix:**
- HTML-escape `message` for its context, as Sample I does, or serve it as `text/plain` with `X-Content-Type-Options: nosniff`.
- Add a restrictive CSP.
- Consider serving previews from a separate sandbox origin.

**How to verify:** a test that a `message` containing markup comes back as inert escaped text, and that the response carries the CSP header.

## Sample I: `/preview`, no substantiated security findings

**Why it holds:**
- `html.escape(..., quote=True)` turns `& < > " '` into entities, and the output sits in an HTML element-text context (`<p>...</p>`).
- The contract says nothing later decodes or re-inserts the output.
- As a second layer, `default-src 'none'` stops any script or resource from loading, `base-uri 'none'` stops `<base>` tricks, and `frame-ancestors 'none'` stops framing.

**Limit:** other account handlers are outside the supplied scope.

## Sample J: `/upload` path traversal overwrites account-service config

**Severity:** High. **Confidence:** High.

**What the code does:** `destination = ROOT / item.filename` (packet line 70), where the filename is chosen by the attacker. That causes two problems:
- With `pathlib`, an absolute filename such as `/srv/account-service/config/<file>` replaces `ROOT` entirely.
- A relative name such as `../account-service/config/<file>` escapes `/srv/uploads`, because nothing resolves or checks the path.

`save` then overwrites whatever is at that path.

**What an attacker can do:**
- **Who:** any self-registered user.
- **Overwrite account-service config:** the application user can write to `/srv/account-service/config`, so the attacker can replace configuration there with up to 16 KiB of their own content.
- **Resulting auth bypass:** per the contract, this can disable account-service authentication on its next ordinary restart. The attacker cannot trigger that restart, so the bypass is delayed and depends on when a restart happens. The config overwrite itself happens immediately.
- **Other users' files:** an attacker can also overwrite other users' files in `/srv/uploads` if they know or can guess the names.

**Not established:**
- Code execution: files are never executed, and no executable deployment directory exists.
- Root access, or writes outside those two directories.

**Fix:**
- Ignore the client's filename. Generate a server-side name such as a UUID, or, if you must keep the name, apply strict basename validation as Sample K does.
- Resolve the final path and require `is_relative_to(ROOT)`.
- Open with exclusive create (`"xb"`) so nothing is overwritten.
- Separately, remove the application user's write access to `/srv/account-service/config` (least privilege).

**How to verify:** tests that absolute paths, `..` segments and existing names are all rejected. Also confirm from the deployed permissions that the application user can no longer write to the account-service config directory.

## Sample K: `/upload`, no substantiated security findings

**Why it holds:**
- **Name check:** the regex allows only `[A-Za-z0-9_-]{1,48}\.txt`. That rules out `/`, `..` and absolute paths.
- **Path check:** after the name check, the code resolves the path and checks containment with `is_relative_to`, which exists in Python 3.10.
- **No overwrite:** `"xb"` prevents overwriting, and the contract says existing names get a handled conflict response.
- **No path tricks:** the contract says users cannot create symlinks, hard links or directories, and that `/srv/uploads` and its parent directories cannot be tampered with. That rules out redirecting a write through the file system or swapping the path between check and use.
- **No serving:** files are not executed, rendered, listed or offered for download.

**Optional hardening, not a vulnerability:** the contract sets no limit on how many files one account can create. Each file is at most 16 KiB, but repeated uploads could fill the disk. Whether that matters depends on disk quota and rate limits, which the contract doesn't give, so impact is not established.

---

## Coverage and limits

- **Static only:** nothing was run, reproduced, or checked against a live service. Each verdict holds only as far as its sample's contract is accurate and complete.
- **Not reviewed:** helper code such as `require_login`, `http.get` and `save`, which I took as described; framework internals; the account-service config format; and deployment beyond what the packet states.
- **Overall risk:** unrated, because there is not enough context to rate the application as a whole. The ratings above apply to each sample only.
