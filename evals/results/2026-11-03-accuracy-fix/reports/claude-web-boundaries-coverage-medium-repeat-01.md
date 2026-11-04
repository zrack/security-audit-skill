# Security review: `review-packet.md`

Three of the six samples have security problems: F (High), H (High) and J (High). G, I and K have none.

## Scope
- **What I reviewed:** samples F–K in `review-packet.md`, each against its own contract. The file has no revision or version history, so I reviewed it as it is on disk.
- **How:** I only read the code. I ran nothing, made no network requests, installed nothing, opened no other files and changed nothing.
- **What I relied on:** the packet's contracts, taken as true. The packet says the helpers "behave exactly as described."

## Summary

| Sample | Result | Severity | Confidence |
|---|---|---|---|
| F `/fetch` | Server-side request forgery (SSRF) exposes confidential tenant reports | High | High |
| G `/weather` | No security findings | — | — |
| H `/preview` | Reflected XSS lets an attacker read a victim's confidential account details | High | High |
| I `/preview` | No security findings | — | — |
| J `/upload` | Path traversal lets a user overwrite files, including account-service config | High | High |
| K `/upload` | No security findings | — | — |

---

## Sample F: SSRF to the internal report service (High, confidence High)

**Location:** `fetch()`, packet lines 11–13.

**What the code does:** it takes `request.args["url"]` as given, fetches it with `http.get(destination, ...)`, and returns the response body (`result.content`) to the caller.

**Why it's a vulnerability:** anyone can self-register, and that account can request `/fetch?url=http://10.40.0.15:8080/exports/current`. The contract says:
- the client "performs no destination filtering";
- the application host can reach that internal service;
- `/exports/current` returns "confidential tenant account reports to any caller on that internal network, without another credential";
- "No external route otherwise exposes these reports."

So an ordinary user gets confidential reports from other tenants that they couldn't get any other way.

**Controls that don't stop it:**
- **Login requirement:** stops anonymous users, but any self-registered account passes.
- **No redirects followed:** this only matters for redirect-based tricks. The attacker can name the internal address directly.
- **TLS verification and no proxy:** these don't help, because the target is plain HTTP.
- **64 KiB response limit:** caps how much comes back per request, but doesn't stop the exposure.
- **No host-administrator privilege:** doesn't matter here, since reading the reports needs no special privilege.

**Not shown by the packet:** that the attacker can reach anything other than the named report service, or that they can learn which other internal hosts exist.

**Fix:**
- Best option: remove the feature that fetches any URL, or limit it to an allowlist of exact external origins.
- If any URL must be allowed: resolve the hostname, reject private, loopback, link-local and other internal addresses, and connect to the IP address you checked so DNS can't swap in a different one afterwards.
- As defence in depth: require a credential on the internal `/exports/current` route.

**How to verify:** add unit tests that call `/fetch` with `http://10.40.0.15:8080/...`, decimal or IPv6 forms of internal addresses, and a hostname that resolves to a private IP. Each should be rejected before any connection is made.

## Sample G: no security findings

- The client can only choose `station`.
- That value must match `[A-Z]{4}` exactly, and it is sent as an encoded query parameter to a fixed, trusted HTTPS address.
- The contract rules out attacker control of the URL, options, DNS and headers. It also says the client doesn't follow redirects and the upstream makes no further fetches.

So there is no attacker-chosen destination, and the response is public data. This conclusion depends on the contract's statements about the upstream service.

## Sample H: reflected XSS on the account interface's origin (High, confidence High)

**Location:** `preview()`, packet line 43.

**What the code does:** it returns `request.args["message"]` unchanged with `content_type="text/html`. The contract says there is no CSP, no iframe sandbox and no upstream escaping.

**Why it's a vulnerability:**
1. An attacker sends a signed-in victim a `/preview?message=<script>…</script>` link.
2. The script runs on the same origin as the account interface.
3. Its same-origin requests to the JSON API carry the victim's session cookies, so it can read "the current user's confidential account details."
4. With no CSP in place, the script can send that data to the attacker.

**Controls that don't stop it:**
- **Secure and HttpOnly cookies:** stop the script from reading the cookie directly. They don't stop it from making same-origin requests that use the session.
- **Unforgeable sessions:** irrelevant, because the attack rides the victim's real session.

**Prerequisite:** the victim must open the link while signed in.

**Not shown by the packet:**
- Any effect on administrators or the host. The packet says no claim about them is supplied.
- Whether the API has state-changing actions the script could perform. I rated only the data exposure.

**Fix:** use Sample I's approach:
- `html.escape(message, quote=True)` in a text context;
- a restrictive CSP;
- or serve the message as `text/plain` with `X-Content-Type-Options: nosniff`.

**How to verify:** add a test that requests `/preview?message=<script>x</script>` and asserts the body contains `&lt;script&gt;` and the CSP header is present.

## Sample I: no security findings

- `html.escape(..., quote=True)` escapes `& < > " '`, and the output only goes into text inside `<p>`. The contract says nothing later decodes it.
- `default-src 'none'` also blocks scripts, so the CSP would contain the damage even if escaping were bypassed.

The packet limits this review to this output path. It says "Other account handlers are outside the supplied scope."

## Sample J: path traversal lets a user overwrite files (High, confidence High)

**Location:** `upload()`, packet lines 70–71.

**What the code does:** it builds the path as `ROOT / item.filename`. Per the contract, the attacker controls the filename, which may be absolute or contain `..`. With `pathlib`, an absolute filename replaces `ROOT` entirely, and `..` components escape it. `save` then writes to that exact path and overwrites any existing file.

**What an attacker can do:** any self-registered user can write up to 16 KiB of their own content to any path the application user can write to. The contract names two directories:
- `/srv/account-service/config`. According to the contract, overwriting configuration there "can disable account-service authentication on its next ordinary restart."
- `/srv/uploads`. Other users' uploads there can be overwritten, even without traversal, because existing files are replaced.

**When the damage takes effect:** the config change applies at the next ordinary restart of the account service. The packet doesn't say who can trigger a restart; it says only that "No … immediate restart control is established." The attacker also needs to know, or guess, the name of the config file the service reads. The packet doesn't say what it is.

**Severity rationale:** a self-registered user gets unauthorized write access to the configuration that controls authentication. That is a serious integrity failure even though the authentication bypass only arrives at the next restart.

**Not shown by the packet:** code execution, root access, writes outside the two named directories, or anything involving symlinks. The packet explicitly says none of these is established.

**Fix:**
- Ignore the client's filename and store each upload under a generated name, such as a UUID.
- If the original name must be kept, use Sample K's pattern: an allowlist regex, then `resolve()` plus `is_relative_to(ROOT)`, then open with `"xb"` so existing files aren't overwritten.
- Separately, take away the upload process's write access to `/srv/account-service/config`.

**How to verify:** add tests that upload files named `/srv/account-service/config/x`, `../account-service/config/x` and the name of an existing upload. Each should be rejected, and no file should be written or changed.

## Sample K: no security findings

- The regex `[A-Za-z0-9_-]{1,48}\.txt` with `fullmatch` rules out `/`, `..`, absolute paths and trailing newlines.
- `resolve()` plus `is_relative_to` adds a second containment check.
- `open("xb")` refuses to overwrite an existing file.
- The contract rules out symlinks, hard links and tampering with parent directories, so there's no race or link-following attack.

## Open questions
- **J: who can trigger the restart, and what is the config file called?** Both determine when the authentication bypass could happen and how easily an attacker can aim at it. To find out, check the account service's restart triggers (deploys, crash or health-check restarts, whether a user can force one) and how predictable its config filenames are.
- **K: is there a cap on how many files a user can upload?** Each upload is at most 16 KiB, but the packet doesn't mention per-user quotas or upload-rate limits, so I can't establish a disk-exhaustion attack either way. This only matters if storage capacity is part of what you're protecting.

## Coverage and limits
- **Areas covered:** SSRF and network boundaries (F, G), output encoding and browser same-origin rules (H, I), and path containment and overwrite behaviour (J, K).
- **Taken from the contracts, not checked:** how `require_login` works, plus the framework, HTTP client and multipart parser.
- **Not done:** I didn't run anything, test anything at runtime, look up advisories, or contact `10.40.0.15` or `weather.example.invalid`.
- **Overall risk:** I've rated each sample on its own. These are separate synthetic excerpts, so I haven't rated any application as a whole.
