# Security review: `review-packet.md`

**Scope:** I reviewed only `review-packet.md`, which holds six separate synthetic samples (F–K), each with its own contract. There is no revision ID because this isn't a git repository. I only read the code and contracts. I didn't execute anything, use the network, install anything, contact the internal address, or modify any files. Helpers behave exactly as their contracts say, and I didn't assume any control beyond those contracts.

| Sample | Result | Severity | Confidence |
|---|---|---|---|
| F `/fetch` | SSRF exposes confidential internal reports | High | High |
| G `/weather` | No substantiated finding | — | — |
| H `/preview` | Reflected XSS reads the victim's confidential account data | High | High |
| I `/preview` | No substantiated finding | — | — |
| J `/upload` | Path traversal lets an attacker overwrite account-service configuration | High | High |
| K `/upload` | No substantiated finding | — | — |

---

## Sample F: SSRF to the internal report service (High, High confidence)

**Location:** `fetch()`: `destination = request.args["url"]` is passed straight to `http.get(destination, ...)`.

**Evidence:** Any self-registered account controls the whole URL. The client does no destination filtering, and the app host can reach `10.40.0.15:8080`. That service's `/exports/current` returns confidential tenant account reports to any caller on the internal network without a credential. The response body goes back to the caller, up to 64 KiB.

**What it lets an attacker do:** Any ordinary account holder can request `/fetch?url=http://10.40.0.15:8080/exports/current` and read the confidential tenant reports. No external route exposes this data otherwise. That makes this a real data exposure across a trust boundary.

**Controls that don't stop it:**
- `require_login` only requires an account, and accounts are self-registered.
- `follow_redirects=False` doesn't matter, because the attacker names the internal host directly.
- TLS verification doesn't apply to a plain-HTTP internal URL.
- The 64 KiB limit only caps how much of each response comes back.

**Limits on the impact:**
- The route only issues GETs with no attacker-controlled headers.
- The process has no host-admin privilege.
- I'm not claiming access to any other internal service, write actions, or host compromise.
- I only know that this one export endpoint returns data. I'm not assuming reports beyond the first 64 KiB can be retrieved.

**Fix:**
- Remove the arbitrary-URL fetch, or replace it with a server-side allowlist of exact schemes, hosts and ports.
- If any user choice of destination has to stay, check the resolved IP address on every request and reject private, loopback, link-local and metadata ranges. Pin the connection to the IP you checked so DNS rebinding can't swap it.
- As a separate fix, require authentication on the internal report service and limit which hosts can reach it at the network level.

**How to verify:** Add tests that a request to `http://10.40.0.15:8080/...` is rejected, along with literal private IPs, hostnames that resolve to private IPs, and alternate IP encodings. Allowlisted destinations should still work.

---

## Sample G: fixed-destination weather fetch: no substantiated finding

- The scheme, host and path are constants.
- `station` must fully match `[A-Z]{4}` before use, and it's sent only as an encoded query parameter. So the user can't change the destination, inject headers or path segments, or smuggle in a different parameter.
- Redirects are off, TLS is verified, and the contract says the upstream service doesn't make further fetches based on the parameter.
- The response is public data.

**Limits:** This conclusion depends on the contract's trust in the upstream service's DNS, TLS and behaviour.

---

## Sample H: reflected XSS on the account origin (High, High confidence)

**Location:** `preview()`: `Response(request.args["message"], content_type="text/html")`.

**Evidence:** The `message` value is returned unescaped as HTML. There's no CSP, sandbox or upstream escaping. Anyone can create a link and send it to someone else. The route is on the same origin as the signed-in account interface, whose JSON API returns the current user's confidential account details.

**What it lets an attacker do:** A victim who is signed in and opens the crafted link runs the attacker's script on the account origin. That script can make same-origin requests to the JSON API and read the victim's confidential account details. It can then send them to the attacker.

**Controls that don't stop it:**
- HttpOnly only stops the script reading the cookie value directly. The browser still attaches the cookie to the script's same-origin requests.
- Secure cookies and unforgeable sessions don't help either, because the attacker is using the victim's real session.
- The preview route itself needs no session to reflect the payload.

**What it needs:** The victim has to open the link while signed in.

**What isn't established:**
- Admin users, host access, or theft of the cookie value itself.
- What other actions the account UI allows. Those would be possible in principle but aren't shown here.
- The cookie's SameSite setting isn't specified. That doesn't change the core finding, because the API calls start from a same-origin page.

**Fix:** Escape the input for its HTML context, as Sample I does. Better still, serve it as `text/plain`, or move the preview to a separate sandboxed origin without credentials. Add a restrictive CSP as defence in depth.

**How to verify:** Request `/preview?message=<script>…</script>` and `<img src=x onerror=…>`. The response should show only inert, escaped text, or the CSP should block execution.

---

## Sample I: escaped preview with CSP: no substantiated finding

- `html.escape(..., quote=True)` encodes `& < > " '`, and the value lands in element text inside `<p>`. That means it can't create markup.
- On top of that, the CSP sets `default-src 'none'`, which blocks scripts and other subresources. It also sets `base-uri 'none'` and `frame-ancestors 'none'`.
- The contract rules out later client-side decoding or re-insertion of the value.

**Optional hardening (not a vulnerability):** Add `charset=utf-8` to the content type and send `X-Content-Type-Options: nosniff`.

---

## Sample J: path traversal lets an attacker overwrite files (High, High confidence)

**Location:** `upload()`: `destination = ROOT / item.filename` is followed by `item.save(destination)`.

**Evidence:** The filename is fully attacker-controlled, including absolute paths and `..`. In `pathlib`, joining an absolute right-hand path throws away `ROOT` entirely: `/srv/uploads / "/srv/account-service/config/x"` becomes `/srv/account-service/config/x`. A `../account-service/config/x` name escapes the same way. `save` overwrites existing files.

**What it lets an attacker do:** Any self-registered user can create or overwrite files, up to 16 KiB, in `/srv/account-service/config`. They can also overwrite other users' files in `/srv/uploads`.

- **Directly shown:** an unauthorized user can change the account-service configuration.
- **Follow-on consequence:** per the contract, a chosen config can disable account-service authentication at the next ordinary restart. The attacker doesn't control when that restart happens, which delays the impact but doesn't remove it.

**What isn't established:**
- Writes outside those two directories.
- Code execution, root access, or symlink-based attacks. The contract rules these out.

**Fix:**
- Ignore the client filename for storage. Generate a server-side name such as a UUID, and keep the original name only as metadata.
- If client names have to stay, use Sample K's pattern: a strict allowlist regex, `resolve()` plus an `is_relative_to(ROOT)` check, and `open("xb")` so nothing is overwritten.
- Separately, remove the app user's write access to `/srv/account-service/config` (least privilege).
- Check the integrity of the existing account-service config.

**How to verify:** Upload files named `/srv/account-service/config/test`, `../account-service/config/test` and a filename that already exists. All three should be rejected, and nothing outside `/srv/uploads` should change.

---

## Sample K: contained upload: no substantiated finding

- The regex `[A-Za-z0-9_-]{1,48}\.txt` with `fullmatch` rules out `/`, `..`, absolute paths and trailing-newline tricks.
- The containment check uses `resolve()` and `is_relative_to`, which exists on Python 3.10 and later. It's redundant after the regex, but it's correct.
- `open("xb")` refuses to overwrite an existing file.
- The contract excludes symlinks, hard links, directory swaps and any rendering or download of the files.
- Authentication comes from the decorator, as the contract says.

**Not assessed:** whether a user can exhaust storage by uploading many 16 KiB files. The contract says nothing about quotas or counts, so I can't support a finding either way.

---

## Coverage and limits

- **Inspected:** all six samples and their contracts, covering SSRF, output encoding and CSP, and path containment and overwrite behaviour.
- **Not done:** no runtime reproduction, no network contact, no dependency or advisory checks. Framework behaviour is taken from the contracts. For `pathlib`, `html.escape` and `re.fullmatch`, I relied on standard Python semantics.
- **Overall risk:** Unrated. The review only covers these excerpts, so it says nothing about any whole application.

**Next action:** Fix the three High findings: allowlist F's destinations and authenticate the internal report service, escape or isolate H's output, and stop J from trusting client filenames while removing its write access to the account-service config.
