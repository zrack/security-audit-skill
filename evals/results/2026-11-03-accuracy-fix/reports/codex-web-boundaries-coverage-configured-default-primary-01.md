Reviewed only `review-packet.md` as six independent synthetic samples, accepting each contract as authoritative. No immutable revision was supplied. Inspection was static only; no sample execution, network access, dependency installation, unrelated-file inspection, or modification occurred.

**Sample F — High severity, High confidence: SSRF crosses the internal report boundary.** At `lines 11–13`, an ordinary self-registered account controls the fetch destination and receives the response body. The contract establishes a reachable internal endpoint that returns confidential tenant reports without further credentials.

Login, TLS verification, disabled redirects, timeout, and response limit do not prevent a direct internal HTTP request. The contract “imposes a 64 KiB response limit”; complete retrieval of larger reports is not established. Host-administrator privilege is explicitly absent and unnecessary for this disclosure.

Fix by restricting fetches to approved destinations and requiring appropriate authorization at the report service. Recommended verification: check destination restrictions against direct internal addresses and ensure unauthorized callers cannot retrieve reports.

**Sample G — No substantiated security finding.** The `request construction` fixes the destination and passes a four-letter station identifier as a parameter. The contract explicitly prevents attacker modification of the URL, headers, DNS configuration, and HTTP options, and excludes downstream fetches.

Trusted DNS/TLS identity, disabled redirects, public-only responses, response limits, and edge rate limiting further constrain the path. No attacker-controlled destination or confidential response is established. This conclusion relies on the supplied service and client contracts.

**Sample H — High severity, High confidence: reflected XSS exposes a signed-in victim’s account details.** At `line 43`, attacker-controlled input becomes executable HTML. A signed-in victim following a crafted preview link can run attacker-supplied script under the account interface’s origin, allowing reads of that victim’s confidential JSON API responses.

HttpOnly prevents direct cookie reads; it does not prevent script from making authenticated same-origin requests. Secure protects cookie transport, and session unforgeability does not prevent this use of the victim’s existing session. The contract says, “No claim about administrator users or host privileges is supplied”; those consequences are not established.

Fix by encoding the message for its HTML text context, as I does, or serving it as plain text. Recommended verification: confirm attacker markup remains inert throughout the complete output path.

**Sample I — No substantiated security finding.** At `lines 53–55`, standard-library HTML escaping places the message safely inside paragraph text. The contract guarantees exact delivery and excludes later decoding or reinsertion.

The restrictive CSP supplies additional script protection and blocks base URLs and framing. H’s vulnerable rendering operation does not carry over to this independent sample. Other account handlers are explicitly outside scope.

**Sample J — High severity, High confidence: path traversal permits authentication-configuration overwrite.** At `lines 70–71`, an absolute filename overrides `ROOT`, while `..` components can escape it. A self-registered uploader can overwrite writable configuration under `/srv/account-service/config`. The contract establishes that such an overwrite can disable authentication on the next ordinary restart.

The 16 KiB limit constrains payload size; directory permissions explicitly constrain filesystem writes. Files are never executed or rendered as HTML. The contract says, “No root privilege, executable deployment directory, symlink attacker, or immediate restart control is established.” Those are unresolved capabilities, not guarantees of absence. Authentication disablement depends on a subsequent restart; who can trigger it remains unestablished.

Fix with safe single-component filenames, containment enforcement, and non-overwriting creation; remove configuration-write permission from the upload process. Recommended verification: check absolute and traversal filenames cannot reach configuration and existing files cannot be overwritten.

**Sample K — No substantiated security finding.** The `upload path` combines a strict filename allowlist, resolved containment check, and exclusive creation with `"xb"`.

Trusted, nonreplaceable directory ancestry and explicit restrictions on links and directories address path-substitution concerns. Existing-file conflicts are handled; authentication and upload limits apply. Files are neither executed, rendered, listed, nor downloadable through the application. These conclusions depend on those explicit filesystem and exposure guarantees.

All verification steps above are recommendations, not performed tests. Findings establish the stated consequences within these contracts; they do not establish broader application compromise or whole-application security.
