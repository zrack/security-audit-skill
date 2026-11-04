# Security review: review-packet.md (Samples F–K)

**Scope:** I reviewed only `review-packet.md`, a supplied set of synthetic samples with no code revision. Each sample was judged against its own contract, and the contracts' descriptions of helpers were taken as true. I only read the code. Nothing was run, nothing was fetched over the network, no packages were installed and no files were changed.

## Summary

| Sample | Result | Severity | Confidence |
| --- | --- | --- | --- |
| F `/fetch` | A logged-in user can make the server fetch any URL, including an internal report service | High | High |
| G `/weather` | No problem found | — | — |
| H `/preview` | Cross-site scripting: the message is returned as raw HTML | High | High |
| I `/preview` | No problem found | — | — |
| J `/upload` | The filename controls where the file is written, so users can write outside the upload folder | High | High |
| K `/upload` | No problem found | — | — |

---

## Sample F: the server fetches any URL a user gives it (High, High confidence)

**Location:** `fetch()`. `request.args["url"]` goes straight into `http.get(destination, …)`, and the response body goes back to the caller.

**What the code does:** Any account can request any HTTP or HTTPS address, and the server sends back what it got. The contract says the client "performs no destination filtering". The application host can reach `10.40.0.15:8080`, whose `/exports/current` route "returns confidential tenant account reports to any caller on that internal network, without another credential."

**Supported consequence:** Any self-registered account can ask for `http://10.40.0.15:8080/exports/current` and receive confidential tenant account reports. According to the contract, no outside route normally exposes them. The rating is High because the attacker only needs an account they can create themselves, and the data is confidential and covers multiple tenants.

**Controls in place and what they limit:**
- **Login is required**, but anyone can register, so it doesn't stop this.
- **No redirects are followed**, which only blocks redirect-based tricks. The direct request still works.
- **The 64 KiB response limit** caps how much comes back per request. Whether a full report fits is not supplied.
- **No host-administrator privilege** means I'm not claiming the host itself is taken over.

The contract only names this one internal service. I'm not claiming any other internal targets.

**Fix:**
- Remove the free-form URL parameter, or limit it to a short list of approved external hosts.
- If arbitrary URLs must stay, resolve the hostname and reject private, loopback, link-local and other internal address ranges. Then connect to the exact IP that was checked, so the name can't be switched to a different address in between (DNS rebinding).
- Add a network-level outbound rule that blocks the fetch process from reaching `10.40.0.0/16`.
- Separately, the report service should require its own credential rather than trusting anything on the internal network.

**Verification:** Write tests with a stubbed client:
- `url=http://10.40.0.15:8080/exports/current` is rejected with no outgoing request.
- A hostname that resolves to a private address is also rejected.

## Sample G: no problem found

The station code must be exactly four capital letters (`[A-Z]{4}`). It is passed as an encoded query parameter to a fixed, trusted HTTPS address. Users can't change the URL, options, DNS or headers, and the service makes no further requests based on the parameter. The response is public station data, sent back as a download (`application/octet-stream`). I found no way for a user to steer the request to another destination or to inject anything.

## Sample H: cross-site scripting through the preview link (High, High confidence)

**Location:** `preview()` returns `request.args["message"]` unchanged with `content_type="text/html"`.

**What the code does:** Whatever is in the message is rendered as HTML on the same site as the signed-in account interface. The contract says there is no Content-Security-Policy, no iframe sandbox and no escaping, and that any user can send the link to someone else.

**Supported consequence:**
1. A victim who is signed in opens an attacker's preview link.
2. The attacker's script runs on the application's own site.
3. Because the request comes from the same site, it can call the JSON API with the victim's session and read the victim's confidential account details. It can then send them anywhere.

**Controls in place and what they limit:**
- **Secure and HttpOnly cookies** stop the script from reading the cookie itself. They do not stop it from making requests that carry the cookie automatically.
- **Sessions can't be forged**, but the attack doesn't need a forged session.

**Not supported by the contract:** The contract says "no claim about administrator users or host privileges is supplied," so I'm not claiming admin takeover. Other actions the script might take are also not claimed, because no other state-changing endpoints are described.

**Fix:** Escape the message before output, as Sample I does (`html.escape(..., quote=True)`), or return it as `text/plain`. Also add a restrictive CSP, such as I's `default-src 'none'` policy.

**Verification:** A test with `message=<script>alert(1)</script>` should return the escaped text `&lt;script&gt;…` and include the CSP header.

## Sample I: no problem found

The message is escaped with `html.escape(..., quote=True)` and placed as plain text inside `<p>`, so it can't become markup. The contract says nothing decodes or re-inserts it later. On top of that, the CSP `default-src 'none'` would block scripts even if escaping failed, and `frame-ancestors 'none'` stops other sites from framing the page.

**Optional hardening:** Set `text/html; charset=utf-8` explicitly so the browser never has to guess the encoding.

## Sample J: users can write files outside the upload folder (High, High confidence)

**Location:** `upload()`, at `destination = ROOT / item.filename` and then `item.save(destination)`.

**What the code does:** The filename the user supplies decides where the file is written:
- With Python's path joining (`pathlib`), an absolute filename such as `/srv/account-service/config/<name>` replaces `/srv/uploads` completely.
- Filenames with `../` steps also climb out of the folder.

The contract says the framework keeps both forms and that `save` overwrites existing files. The application user can write to `/srv/account-service/config`.

**Supported consequence:** Any self-registered account can create or overwrite files in `/srv/account-service/config`, up to 16 KiB each. That is unauthorized modification of another service's security configuration. Users can also overwrite files in `/srv/uploads` whose names they know.

**When it takes effect:** The contract says overwriting that config "can disable account-service authentication on its next ordinary restart." So turning off authentication depends on a restart. The contract states "no … immediate restart control is established", so the attacker can't be assumed to trigger that restart. Even so, I rate this High: the write to the auth configuration is fully shown, and an ordinary restart is expected to happen eventually.

**Controls in place and what they limit:**
- Login is required, but anyone can register.
- The 16 KiB upload limit caps file size, not where the file goes.
- Files are never executed or rendered, so there is no code-execution path.
- The application user can't write anywhere else on the filesystem, so the reach stops at these two folders.

**Fix:**
- Generate the stored filename on the server, or apply K's approach: a strict filename allowlist, `resolve()`, an `is_relative_to(ROOT)` check, and opening with `"xb"` so existing files are never overwritten.
- Separately, take away the application user's write access to `/srv/account-service/config`.

**Verification:** Tests should confirm that:
- `../account-service/config/x` and `/srv/account-service/config/x` are rejected and nothing is written.
- A filesystem permission check confirms the app user can no longer write to the config folder.

## Sample K: no problem found

Several checks stack up:
- **Filename allowlist:** Names must match `[A-Za-z0-9_-]{1,48}\.txt`. That rules out `/`, `..` and absolute paths.
- **Folder check:** `resolve()` plus `is_relative_to(ROOT)` (available on Python 3.10, as the contract states) is a second check that the file stays inside the upload folder.
- **No overwrites:** Opening with `"xb"` refuses to overwrite an existing file.
- **No folder tricks:** The contract rules out symlinks, hard links, users creating directories, and the parent folders being swapped out.
- **No exposure:** Files are never executed, rendered, listed or offered for download.

## Needs validation

- **F:** How large is a typical `/exports/current` report compared with the 64 KiB limit? This only affects how much is read per request, not whether the problem exists.
- **J:**
  - Who can trigger or speed up an account-service restart? The contract says no immediate restart control is established.
  - Can an attacker learn or guess the config filenames that matter? Having write access to the folder doesn't tell them which files are in it.
  - Does the account service also load *new* files from that folder, or only ones that already exist?
- **J / K:** Is there a per-account limit on how many files or how much disk an account can use? None is supplied, so whether repeated uploads could fill the disk is unknown. I'm not rating it.

## Review coverage

- **Checked:** whether user input could steer server requests (F, G), cross-site scripting and same-site data access (H, I), and file paths and overwrites (J, K).
- **Taken as given:** how `require_login` works, along with every behaviour each contract describes.
- **Not checked:** the framework and helpers themselves, deployment configuration, other routes, how sessions are issued, and any behaviour at runtime.

All conclusions come from reading the code against the supplied contracts; none were confirmed by running anything. Overall risk is not rated for an application beyond these six samples.
