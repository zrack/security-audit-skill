Static inspection supports **three findings: F, H, and J**. G, I, and K have no substantiated findings under their supplied contracts. Only the packet was reviewed; no immutable revision was supplied.

1. **F — High severity, High confidence: SSRF exposes internal reports.**
   At `lines 11–13`, an ordinary self-registered account controls the destination and receives the response. Selecting the internal `/exports/current` endpoint crosses the network trust boundary and exposes confidential report content accepted by the 64 KiB response limit.

   Login, TLS verification, timeout, and disabled redirects do not block a direct internal HTTP request. Supported impact is report disclosure; host compromise is unestablished. **Fix:** restrict destinations to approved services and enforce network egress restrictions. **Proposed verification:** use an isolated HTTP stub to confirm internal destinations are rejected before connecting.

2. **G — No substantiated security finding.**
   At `lines 24–33`, user input affects only a validated station parameter. The destination, DNS identity, headers, and HTTP options remain outside attacker control. The trusted service returns public data and performs no secondary fetches. TLS verification, disabled redirects, response limits, timeout, and edge rate limits reinforce this boundary. No correction is supported by the supplied evidence.

3. **H — High severity, High confidence: reflected XSS.**
   At `line 43`, attacker input becomes unescaped HTML. A signed-in recipient opening a crafted link can run attacker JavaScript in the account interface’s origin. That script can make authenticated requests to the stated JSON API and read the recipient’s confidential account details.

   HttpOnly prevents direct cookie reads, while the browser still attaches cookies to matching requests. Secure restricts cookie transmission; it does not prevent XSS. Cookie theft, administrator access, and additional account operations are unestablished. **Fix:** escape the message for its HTML text context, as in I. **Proposed verification:** confirm markup renders as text in an isolated browser test.

4. **I — No substantiated security finding.**
   At `lines 53–55`, standard-library escaping keeps input within paragraph text. The exact-output and no-reinsertion contracts exclude a later unsafe rendering step. CSP adds protection against script execution and resource loading; its other directives prohibit base URL changes and framing. Cookie flags retain their limited roles described above. This conclusion covers only the supplied preview path.

5. **J — High severity, High confidence: path traversal permits configuration overwrite.**
   At `lines 70–71`, an absolute filename overrides `ROOT`, and `..` components can escape it. A self-registered user can overwrite writable account-service configuration, potentially disabling authentication on the next ordinary restart.

   Filesystem permissions bound the writable scope. The 16 KiB limit and nonexecution/nonrendering controls do not prevent configuration tampering. Immediate restart control, root access, and code execution are unestablished. **Fix:** use server-generated basenames and exclusive creation within the upload directory; remove uploader write access to service configuration. **Proposed verification:** confirm traversal and absolute-path inputs cannot alter an isolated sentinel configuration file.

6. **K — No substantiated security finding.**
   At `lines 87–93`, the filename allowlist excludes path components, resolved containment checks the destination, and exclusive creation prevents overwrites. Trusted, stable directories and the prohibition on attacker-created links address filesystem escape races under this contract. Authentication, bounded uploads, handled conflicts, and absence of execution, rendering, or download exposure further constrain consequences.

All findings rely on the stated contracts. No sample execution, network access, dependency installation, unrelated project inspection, or file modification occurred. Proposed verification steps were not performed; deployment behavior and other application paths remain unvalidated.
