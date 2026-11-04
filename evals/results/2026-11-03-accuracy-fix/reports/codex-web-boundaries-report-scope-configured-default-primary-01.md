Static review of the supplied `review-packet.md`, treating each contract independently. No immutable revision was supplied. No sample code was executed, network accessed, dependencies installed, or files modified.

- **Sample F — High severity, High confidence: SSRF exposing confidential reports.** At `lines 11–16`, a self-registered account controls the destination and can select the supplied internal `/exports/current` endpoint. Confidential responses within the client’s 64 KiB limit are returned to that account.

  Login, TLS verification, disabled redirects, no proxy, and the two-second timeout do not prevent a direct request to this reachable internal HTTP service. Actual report sizes and oversized-response behavior are unspecified. The supported consequence is disclosure from the identified endpoint; the contract explicitly gives the fetch process no host-administrator privilege.

  **Fix:** Allowlist intended destinations against the actual connection addresses; require authorization at the report service. Suggested verification: confirm the internal destination is rejected while approved destinations work.

- **Sample G — No substantiated security finding.** At `lines 24–36`, users control only a four-letter station parameter. The destination is fixed and trusted, and the upstream performs no secondary fetching.

  Parameter separation, operator-controlled DNS/TLS, verified TLS, disabled redirects, restricted request options, response limits, authentication, and edge rate limiting constrain the supplied path. The contract establishes public-data retrieval, without a harmful attacker-selected destination. This conclusion relies on those explicit guarantees and covers this route only.

- **Sample H — High severity, High confidence: reflected XSS exposing victim account data.** At `lines 41–46`, attacker-controlled content becomes executable HTML. A signed-in victim opening the shared link permits attacker JavaScript to request and read confidential JSON data from the same origin.

  HttpOnly prevents direct cookie reads; Secure protects cookie transport. Neither prevents same-origin scripts from using the victim’s authenticated session. Session forgery is unnecessary. Victim interaction and an authenticated session are prerequisites for the confidential-data consequence. The contract states, “No claim about administrator users or host privileges is supplied.”

  **Fix:** Escape the message for its HTML text context or serve it as `text/plain`; add restrictive CSP as another control. Suggested verification: confirm supplied markup remains literal text and cannot execute scripts.

- **Sample I — No substantiated security finding.** At `lines 53–59`, standard-library escaping safely places the message inside an HTML text context. The explicit absence of subsequent decoding or reinsertion preserves that protection.

  CSP additionally blocks scripts through `default-src 'none'`, restricts base URLs, and prevents framing. This conclusion covers the complete supplied preview output path; other account handlers remain outside scope.

- **Sample J — High severity, High confidence: path traversal permitting authentication-configuration overwrite.** At `lines 70–75`, absolute filenames override the upload root, while `..` permits traversal. The specified save behavior permits attacker bytes to overwrite writable account-service configuration. Under the contract, an authentication-disabling configuration change takes effect on the next ordinary restart.

  Self-registration and the 16 KiB limit do not prevent this overwrite. Filesystem writes are explicitly restricted to the two supplied directories; nonexecution and nonrendering controls address different consequences. The contract says, “No root privilege, executable deployment directory, symlink attacker, or immediate restart control is established.” Who can trigger restart remains unknown. Exact configuration filenames, formats, and restart timing are not supplied.

  **Fix:** Enforce filename and resolved-path containment, prevent replacement where unnecessary, and remove upload-process write access to account-service configuration. Suggested verification: confirm absolute and traversal filenames cannot alter a configuration fixture.

- **Sample K — No substantiated security finding.** At `lines 87–97`, the filename allowlist excludes path syntax, resolved containment enforces the root, and exclusive creation prevents overwrites.

  Trusted directory ancestry and the explicit prohibition on attacker-created links or concurrent directory mutation close the relevant path-race alternatives. Authentication, upload limits, handled conflicts, and the absence of execution, rendering, listing, or download paths further constrain consequences. This conclusion depends on those supplied filesystem guarantees.

All verification steps above are recommendations only. Findings are supported by static inspection and the synthetic contracts; no runtime behavior was independently validated.
