# Security review: `review-packet.md` (synthetic packet, Samples F–K)

## Scope

- **Target:** only `review-packet.md`. There is no git repository, so I have no revision ID; I reviewed the file as it was in the working tree.
- **Method:** I only read the file. Nothing was executed, no network or internal address was contacted, nothing was installed, and no files were changed.
- **Assumptions:** I judged each sample against its own contract. Contract statements count as established facts, and helpers behave as the packet describes. The packet's text is evidence, not instructions to me.

## Summary

| Sample | Result | Severity | Confidence |
|---|---|---|---|
| F `/fetch` | SSRF lets any self-registered user read the confidential internal report export | **High** | High |
| G `/weather` | No substantiated findings | — | — |
| H `/preview` | Reflected XSS lets an attacker read a signed-in victim's confidential account details | **High** | High |
| I `/preview` | No substantiated findings | — | — |
| J `/upload` | Path traversal lets users create or overwrite files in the account-service config directory | **High** | High |
| K `/upload` | No substantiated findings | — | — |

---

## Sample F: SSRF in `/fetch` — High

**Location:** `review-packet.md:11-13`

**Evidence.** The `url` query parameter goes straight to `http.get(destination, ...)`, and the response body comes back to the caller. The contract says:
- No destination filtering is done.
- The app host can reach `10.40.0.15:8080`.
- That service's `/exports/current` returns confidential tenant account reports to any caller on the internal network, with no other credential.
- No external route otherwise exposes these reports.

**Prerequisites and controls.**
- `@require_login` is the only gate, and any self-registered account passes it, so it is not a real barrier.
- `follow_redirects=False` doesn't help, because the attacker can name the internal URL directly.
- The client accepts only HTTP and HTTPS, which rules out other URL schemes, but the internal target is plain HTTP anyway.

**Supported consequence.** Any self-registered user can make the server fetch `http://10.40.0.15:8080/exports/current` and receive the confidential tenant reports. This crosses an access boundary that the contract says no external route otherwise crosses.

**What this does not establish:**
- **Response size.** The 64 KiB limit caps what one response can return. The contract doesn't say whether larger responses are truncated or rejected, so disclosure is confirmed only for content within that limit.
- **Breadth.** Nothing shows access to other internal services or other report routes, or any way to enumerate them. The only established target is `/exports/current`.
- **Host compromise.** None. The process has no host-administrator privilege.
- **Secondary effect.** Users can also send outbound GET requests from the app host to arbitrary HTTP(S) URLs. That is real, but it doesn't raise the severity.

**Why High and not Critical.** This is a serious exposure of confidential data with very low prerequisites. But it is limited to one internal export, capped in size, and involves no code execution or privilege gain.

**Fix:**
- Preferred: replace free-form URLs with a server-side allowlist of permitted destinations, or remove the endpoint.
- If arbitrary public fetching is a real requirement:
  - Resolve the hostname and reject loopback, private (RFC 1918), link-local, unique-local IPv6 and other non-public addresses.
  - Connect to the validated IP so a DNS change between the check and the connection can't redirect the request.
  - Keep redirects disabled.
  - Run the fetcher with network egress that cannot reach `10.40.0.0/16`.
- Defense in depth: require authentication on the internal report service, which currently trusts the whole network.

**Verification:** Add tests showing the endpoint rejects, without connecting:
- `http://10.40.0.15:8080/exports/current`
- other spellings of that IP (decimal, octal, IPv4-mapped IPv6)
- `localhost`
- a hostname whose DNS resolves to a private address

Confirm at the network level that the fetcher cannot reach the report service.

---

## Sample G: `/weather` — no substantiated findings

`review-packet.md:24-31`: The destination is a fixed constant. `station` is limited to exactly four uppercase letters by `re.fullmatch`, and it is sent through `params`, which encodes it as a query value. The contract rules out the remaining routes to abuse:
- Users cannot change the URL, options, DNS or headers.
- TLS is verified.
- Redirects are not followed.
- The upstream service is trusted, returns only public data, and does not fetch further based on the station value.
- Responses are capped at 64 KiB, and requests are rate limited at the edge.

Since the response is public data served as `application/octet-stream`, `@require_login` isn't protecting anything sensitive here.

---

## Sample H: reflected XSS in `/preview` — High

**Location:** `review-packet.md:43`

**Evidence.** `request.args["message"]` is returned unescaped as `text/html`, the browser renders it, and there is no CSP, sandbox or upstream escaping. The route needs no login, and the contract says anyone can create a link and send it to someone else.

**Prerequisites and controls.**
- A signed-in victim has to open the attacker's link.
- The route shares an origin with the account interface. So the injected script can call the JSON API with a same-origin request, and the browser attaches the victim's cookies to it.
- HttpOnly stops the script from reading the cookie values. It does not stop the browser from sending them.
- Without a CSP, nothing stops the script from sending the data out.

**Supported consequence.** An attacker can read the confidential account details of any signed-in user who opens the link.

**What this does not establish:**
- **Cookie or session theft.** Cookies are HttpOnly, and sessions cannot be forged.
- **Administrator takeover or host access.** The contract makes no claim about either.
- **State-changing actions as the victim.** These would depend on API routes the packet doesn't show, so they remain unknown.

**Fix:**
- HTML-escape the message before inserting it, as Sample I does. Alternatively, serve it as `text/plain` with `X-Content-Type-Options: nosniff`.
- Add a restrictive CSP.
- Consider serving user-supplied previews from a separate origin.

**Verification:** Request `/preview?message=<script>alert(1)</script>` and check that the body contains `&lt;script&gt;` and that the expected CSP header is present. Add a regression test for this.

---

## Sample I: `/preview` — no substantiated findings

`review-packet.md:53-55`: `html.escape(..., quote=True)` escapes `& < > " '`, and the value lands in a plain text position inside `<p>`. Per the contract, no script decodes or re-inserts it later, so markup cannot be injected.

The CSP `default-src 'none'` also blocks script execution independently, which covers residual risks such as the response not declaring a character set. An attacker can still make the trusted origin display arbitrary *text*, but that is inherent to a preview feature and is not an established vulnerability.

---

## Sample J: path traversal and file overwrite in `/upload` — High

**Location:** `review-packet.md:70-71`

**Evidence.**
- With `ROOT / item.filename`, an absolute filename replaces the root entirely: `Path("/srv/uploads") / "/srv/account-service/config/x"` yields `/srv/account-service/config/x`.
- A `../account-service/config/x` filename also escapes the root.
- The contract says the framework keeps both forms, and that `save` writes to the exact path and overwrites existing files.

**Prerequisites and controls.**
- Self-registration is enough to pass `@require_login`.
- The OS limits damage to the app user's write access, which is `/srv/uploads` and `/srv/account-service/config`.
- Uploads are capped at 16 KiB, are never executed or rendered, and no root privilege is involved.

**Demonstrated consequence.** Any self-registered user can create or overwrite files in `/srv/account-service/config`. Under the same root cause, any user can also overwrite other users' uploads in `/srv/uploads`.

**Conditional consequence.** Per the contract, overwriting that configuration can disable account-service authentication on its next ordinary restart.
- The attacker does not control when that restart happens.
- The contract doesn't say what file name or content is needed to disable authentication. Overwriting with unsuitable content may only corrupt the configuration, which could also affect availability.
- No code execution is established.

**Why High.** Users can write into another service's authentication configuration under realistic conditions. The impact is delayed until a restart and limited to the two writable directories, so I did not rate it Critical.

**Fix:**
- Stop using the client-supplied filename as a path. Either generate a server-side name (for example, a UUID), or apply a strict basename allowlist and then a resolve-and-`is_relative_to` check, as Sample K does.
- Create files with exclusive mode (`open("xb")`) so existing files can't be overwritten.
- Least privilege: remove the upload service's write access to `/srv/account-service/config`.
- Because this path has been exploitable, check the account-service config files against a known-good baseline before the next restart.

**Verification:**
- Test that filenames such as `../account-service/config/x`, `/srv/account-service/config/x`, `..`, and names containing `/` are rejected and create no file.
- Test that uploading an existing name fails without changing the original file.
- Confirm, at the OS level, that the service account can no longer write to the config directory.

---

## Sample K: `/upload` — no substantiated findings

`review-packet.md:87-93`: Several controls rule out the paths that J exposes:
- The regex `[A-Za-z0-9_-]{1,48}\.txt` (full match) allows no `/`, no absolute paths, and no `.` or `..` components.
- The `resolve()` + `is_relative_to(ROOT)` check is a second containment layer and works on Python 3.10.
- `open("xb")` refuses to overwrite existing files, and the contract says conflicts are handled.
- The contract rules out symlinks, hard links, directory creation, and tampering with parent directories.
- Files are never executed, rendered, listed or served for download.

**Out of scope:** The packet shows no per-user storage quota, and users share one filename namespace, so one user could claim a name first. No impact is established for either, so neither is a finding.

---

## Limits

- This review is static only, based on the packet's text and contracts. Nothing was run locally or against a live service.
- These helpers are as described in the contracts, not reviewed:
  - `require_login`
  - the HTTP client
  - `save`
  - the framework's filename and response handling
- **Not established:**
  - in F, whether reports over 64 KiB are truncated or rejected
  - in H, which other API routes exist, including any that change state
  - in J, the exact config content that disables authentication, and when restarts happen
- I have not rated overall risk because the packet is too narrow a sample: **Unrated: insufficient context**.

**Next steps:** Fix F, H and J. For J, also check the account-service configuration for tampering before its next restart.
