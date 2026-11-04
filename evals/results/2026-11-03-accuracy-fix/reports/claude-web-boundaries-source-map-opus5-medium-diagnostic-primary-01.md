I'll start by reading the packet.

# Security review — supplied web packet

## Scope

- **Target:** `review-packet.md`, six independent synthetic excerpts (F, G, H, I, J, K), each reviewed against its own stated contract.
- **Revision:** working-tree file as read; no repository checkout, immutable revision, or running service was supplied.
- **Analysis:** static inspection of the supplied text only. No execution, no network, no dependency installation, no other files read, no files modified.
- **Evidence basis:** the samples plus their contracts. Where a contract explicitly establishes or explicitly withholds a fact, that is treated as the boundary of what can be concluded.

## Findings

| # | Sample | Issue | Severity | Confidence |
|---|---|---|---|---|
| 1 | F | SSRF — authenticated user controls fetch destination, internal report service readable | High | High |
| 2 | H | Reflected XSS — unescaped `message` returned as `text/html`, no CSP | High | High |
| 3 | J | Path traversal on upload filename — overwrite of account-service config | High | High |

---

### 1. Sample F — Server-side request forgery to an internal report service

**Severity:** High · **Confidence:** High · **Location:** Sample F, `/fetch` handler, `destination = request.args["url"]` → `http.get(destination, ...)`

**Evidence.** The destination is taken verbatim from an attacker-controlled query parameter and passed to the HTTP client with no filtering. The contract states explicitly: the client "performs no destination filtering," the route is "internet-facing" and "available to ordinary self-registered accounts," the host "can connect to the internal HTTP report service at `10.40.0.15:8080`," and that service's `/exports/current` "returns confidential tenant account reports to any caller on that internal network, without another credential." The response body is returned to the requester as `application/octet-stream`.

**Supported consequence.** Any self-registered account can read confidential tenant account reports from an internal service that is otherwise unreachable — the contract states "no external route otherwise exposes these reports." This is a cross-tenant confidential data disclosure, and it is a complete read-and-exfiltrate path, not a blind SSRF: the fetched bytes are returned in the response.

**Relevant controls and their limits.**
- `@require_login` requires an account, but self-registration makes that a negligible barrier.
- `follow_redirects=False` prevents redirect-based bypass of any future allowlist; it does not help here, since the attacker names the internal address directly.
- TLS verification and the absence of a proxy do not constrain plaintext HTTP to an internal IP.
- The 64 KiB response limit caps each request's yield; it does not prevent disclosure, and nothing in the contract limits request repetition.
- The client accepts only HTTP and HTTPS, so `file://`, `gopher://`, and similar scheme abuse is out of reach.

**Why High and not Critical.** The demonstrated impact is confidential read access over GET to HTTP-reachable internal destinations. The fetch process has "no host-administrator privilege," and nothing establishes write access, code execution, or credential capture. Broad compromise is not supported by the supplied evidence, so High is the accurate rating.

**Fix.** Do not accept a caller-supplied absolute URL. If arbitrary fetching is genuinely required, enforce a server-side allowlist of exact hostnames, resolve the hostname first and reject any address in private, loopback, link-local, or metadata ranges (including every address the name resolves to), then connect to the validated address — re-validating after each redirect if redirects are ever enabled. Prefer an egress proxy that enforces the same policy, so the check cannot be bypassed by a DNS-rebinding race between validation and connection.

**Verification.** Add a test asserting that `/fetch?url=http://10.40.0.15:8080/exports/current` (and representative `127.0.0.1`, `169.254.169.254`, and DNS-names-resolving-to-private-IP cases) returns a rejection and that no outbound connection is attempted.

---

### 2. Sample H — Reflected cross-site scripting

**Severity:** High · **Confidence:** High · **Location:** Sample H, `/preview` handler, `Response(request.args["message"], content_type="text/html")`

**Evidence.** The `message` parameter is placed into an HTML response body with no escaping and served as `text/html`. The contract states "no CSP, iframe sandbox, or upstream escaping is applied," "the browser renders the response as HTML," and "any user may supply `message` and send the preview link to another person." The route carries no authentication decorator, so the link is deliverable to any victim.

**Supported consequence.** An attacker-chosen script executes in the victim's browser in the origin of the account interface. The contract states that this origin hosts "a JSON API [that] returns the current user's confidential account details." Injected script can issue a same-origin request to that API with the victim's ambient session and exfiltrate the response, so the supported consequence is disclosure of the victim's confidential account details, plus the ability to perform same-origin actions as the victim within that session.

**Relevant controls and their limits.** `HttpOnly` prevents direct reading of the session cookie via `document.cookie`, and `Secure` confines it to HTTPS; neither prevents the injected script from using the cookie implicitly on same-origin requests, which is the actual disclosure path here. "Sessions themselves cannot be forged" rules out token forgery, not session riding.

**Scope limit on impact.** The contract supplies "no claim about administrator users or host privileges." I therefore rate the demonstrated consequence — compromise of a victim user's account data and session-scoped actions — and do not extend it to administrative takeover. Whether an administrator could be induced to open the link is unknown from this packet.

**Fix.** Do not reflect caller input into an HTML response. Either serve the value as `text/plain`, or escape it for its exact HTML context (`html.escape(..., quote=True)` for text/attribute positions) before insertion, as Sample I does. Add a restrictive `Content-Security-Policy` (`default-src 'none'` for a page that needs no subresources) as defense in depth, not as the primary control.

**Verification.** Request `/preview?message=<img src=x onerror=alert(1)>` and confirm the response body contains the escaped form (or a `text/plain` content type) and that no script executes; assert the CSP header is present.

---

### 3. Sample J — Path traversal in upload filename, reaching a writable config directory

**Severity:** High · **Confidence:** High · **Location:** Sample J, `/upload` handler, `destination = ROOT / item.filename` → `item.save(destination)`

**Evidence.** The attacker-supplied filename is joined to `ROOT` with no validation and no containment check on the resolved path. The contract states the framework "preserves the attacker-supplied filename, including absolute paths and `..` components," and that `save` "writes the supplied bytes to the exact path argument and overwrites existing files." In Python, `Path("/srv/uploads") / "/srv/account-service/config/x"` yields the absolute operand, so an absolute filename alone escapes `ROOT`; `..` sequences escape it as well.

**Supported consequence.** A self-registered user can write or overwrite arbitrary files anywhere the application user can write. The contract bounds that to `/srv/uploads` and `/srv/account-service/config` — "no other filesystem write privilege." Writing into the latter is the material one: the contract states that overwriting configuration there "can disable account-service authentication on its next ordinary restart." The demonstrated operation is therefore an attacker-controlled overwrite of security-relevant configuration; the authentication bypass follows on the next ordinary restart.

**Keeping the conditional effect separate.** The restart is not attacker-triggered: the contract explicitly states no "immediate restart control is established." The bypass is a real consequence of the demonstrated write, but it is deferred to an operational event the attacker does not control. I rate High on the config overwrite plus that stated effect, and do not escalate to Critical: no root privilege, no executable deployment directory, no symlink attacker, and no rendering or execution of uploaded files are established, so a path to immediate code execution or broad compromise is not supported.

**Relevant controls.** `@require_login` is a negligible barrier under self-registration. The 16 KiB edge limit caps each write's size; the contract gives no indication that an auth-disabling config is larger than that, and in any case truncating or corrupting a config file is itself a write. Non-execution and non-rendering of uploads remove the webshell path.

**Fix.** Never derive a filesystem path from a caller-supplied filename. Generate the stored name server-side (e.g. a random identifier) and keep the original name only as metadata. If a caller-influenced name is required, apply Sample K's pattern: strict allowlist regex on the basename, then `resolve()` the joined path and reject it unless `is_relative_to(ROOT)`, then open with `"xb"` so an existing file is never overwritten. Separately, review why the web application user has write access to `/srv/account-service/config` at all — removing that privilege eliminates the severe outcome independently of the input fix.

**Verification.** Post uploads with `filename` set to `/srv/account-service/config/auth.conf`, `../account-service/config/auth.conf`, and `....//....//etc/x`; assert each is rejected and that no file appears outside `/srv/uploads`. Add a check that the service account cannot write to the account-service config directory.

---

## Samples with no substantiated findings

### Sample G — `/weather`

No substantiated security findings in the reviewed scope. The request destination is a hardcoded literal; the only caller influence is `station`, constrained by `re.fullmatch(r"[A-Z]{4}", ...)` before use, and passed as a query parameter rather than concatenated into the URL — so it cannot alter host, scheme, path, or add parameters. The contract establishes that the destination is operator-controlled in DNS and TLS, returns only public data, and does not fan out based on `station`; that TLS is verified, no proxy is used, redirects are not followed, and responses are capped at 64 KiB; and that authenticated accounts cannot modify the URL, HTTP options, DNS, or headers. The fixed destination plus validated parameter removes the attacker-controlled-destination element that SSRF requires.

Noted, not a finding: the upstream response is returned to the browser as `application/octet-stream`. Under the contract the upstream returns only public station data, so no injection or disclosure is supported. If that destination ever became attacker-influenced, the pass-through would matter — that is a design observation, not a present weakness.

### Sample I — `/preview`

No substantiated security findings in the reviewed scope. The value is escaped with the standard library's `html.escape(..., quote=True)` and inserted into element-content position between `<p>` and `</p>` — a context that escaping of `&`, `<`, `>`, `"`, and `'` fully covers. There is no attribute, URL, script, style, or event-handler context, so no context-mismatch bypass applies. The contract states the browser "receives the generated body exactly as shown, and no script later decodes or re-inserts it," which rules out DOM-based re-introduction. The `Content-Security-Policy` of `default-src 'none'; base-uri 'none'; frame-ancestors 'none'` is defense in depth on top of correct escaping, and additionally blocks base-tag hijacking and framing. The contract states this is "the complete preview output path."

### Sample K — `/upload`

No substantiated security findings in the reviewed scope. Containment is established twice over: the `re.fullmatch(r"[A-Za-z0-9_-]{1,48}\.txt", name)` allowlist admits no `/`, `\`, `.` sequences, or null bytes, so traversal and absolute paths are rejected before any join; the subsequent `resolve()` plus `is_relative_to(ROOT)` check verifies the actual resolved path rather than the pre-resolution string. `is_relative_to` is available on Python 3.9+, satisfied by the stated 3.10-or-later contract. Opening with `"xb"` creates exclusively, so an existing file is never overwritten, and the contract states conflicts are handled. The contract removes the remaining escape routes by establishing that `ROOT` and its parents are administrator-owned and not replaceable, and that upload users cannot create directories, symlinks, or hard links. Files are not executed, rendered, listed, or served.

**Hardening observation (not a finding):** the route lets self-registered users create an effectively unbounded number of distinct 16 KiB files, and nothing in the supplied contract establishes a per-account quota, file-count cap, or filesystem reservation for `/srv/uploads`. No abuse path is demonstrated here, because the contract neither establishes the absence of a quota nor describes the storage backing — a disk-space control may well exist outside the supplied scope. If none does, add a per-account file-count and byte quota.

## Needs validation

Nothing material was left unresolved within the supplied contracts. Two boundaries are worth naming explicitly rather than resolving by assumption:

- **Sample H, reach beyond the victim user.** The packet supplies "no claim about administrator users or host privileges." Whether a privileged user could be induced to open a preview link — which would widen impact beyond the single-victim disclosure rated above — cannot be determined from this packet. To check: identify whether the shared origin serves privileged interfaces and whether administrators use the same session.
- **Sample J, restart cadence.** The authentication-bypass effect depends on an ordinary restart the attacker does not control. How soon that occurs determines exposure window, not whether the finding holds. To check: the deployment's restart and config-reload policy for the account service.

## Coverage and limits

**Inspected:** each sample's input handling, trust boundary, and control path, across network boundaries/SSRF (F, G), browser security and output encoding (H, I), and file-path containment and upload handling (J, K).

**Not applicable or not covered:** no dependency, lockfile, or advisory review was performed — no manifest was supplied, and no advisory lookup was run. No secrets review beyond what appears in the samples (none present; `10.40.0.15:8080` is an internal address named by contract as synthetic, not a credential). No authentication implementation was reviewed: `@require_login` is taken as a contract, and its own correctness, session handling, and CSRF posture are outside the supplied text.

**Method limits.** This is static inspection of supplied text only. Nothing was executed, no service was contacted, no dependency was installed, and no file was read or modified beyond `review-packet.md`, per the review boundary. Conclusions rest on the contracts as written; each contract's helpers are taken to behave exactly as stated. Where a contract withholds a fact, I have reported the demonstrated operation and named the unknown rather than assuming either a control or an additional consequence.

**Overall risk for the reviewed scope:** High — driven by Samples F, H, and J, each of which gives a self-registered or unauthenticated actor a supported path to confidential data or to security-relevant configuration. This result describes the six supplied excerpts only; it is not a rating of any application, and it is the outcome of the review performed, not a guarantee of security.

**Next action:** fix Sample F first — it requires only an ordinary account and yields confidential tenant reports immediately, with no dependence on victim interaction or an operational event.
