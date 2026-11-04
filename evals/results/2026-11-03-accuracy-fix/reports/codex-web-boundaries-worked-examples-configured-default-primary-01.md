Reviewed only the supplied `review-packet.md`, treating each contract as authoritative. Findings are based on static inspection. No code execution, network access, dependency installation, or file modification occurred. Verification steps below are recommendations only.

1. **Sample F — SSRF into confidential report service. High severity; High confidence.**
   At `lines 11–13`, an ordinary self-registered user controls the destination and can direct the server to the internal `/exports/current` endpoint. Successful response content is forwarded to that user.

   Login, HTTPS certificate verification, and disabled redirects do not prevent a direct internal HTTP request. The timeout and 64 KiB cap constrain retrieval; complete disclosure of larger exports and oversized-response behavior are not established. Host or administrator compromise is unsupported.

   **Fix:** Restrict destinations to required services, enforce the policy against actual resolved connection targets, and block unauthorized internal egress. **Suggested verification:** Use an isolated fixture to confirm private-address destinations and disallowed DNS resolutions are rejected before connecting.

2. **Sample G — No substantiated security finding.**
   The `request path` permits only a four-letter station parameter sent to a fixed, trusted public service. The contract excludes attacker control over destinations, DNS, headers, options, and onward fetching.

   TLS verification, disabled redirects, response limits, and edge rate limiting provide additional controls. No harmful attacker-selected destination or confidential response is established. No correction is indicated under this contract.

3. **Sample H — Reflected cross-site scripting. High severity; High confidence.**
   At `line 43`, attacker input becomes an HTML response without escaping. A signed-in victim opening a crafted link can execute attacker script on the account interface’s origin, allowing authenticated API requests and reads of that victim’s confidential account details.

   HttpOnly prevents direct reads of the cookie value; it does not prevent same-origin script from making authenticated requests and reading responses. Secure cookies protect transport. Neither control prevents this XSS. Administrator access, session forgery, and host compromise are not established.

   **Fix:** Escape the message for its HTML text context, as in I, or return `text/plain`; add restrictive CSP as defense in depth. **Suggested verification:** Confirm hostile markup remains literal text and cannot execute or read a mock account API.

4. **Sample I — No substantiated security finding.**
   At `lines 53–55`, standard-library escaping safely places the message inside paragraph text. The contract rules out subsequent decoding or reinsertion.

   CSP additionally blocks scripts through `default-src 'none'`; `base-uri` restricts base URLs and `frame-ancestors` prevents framing. CSP is neither a sanitizer nor a general iframe sandbox. No correction is indicated for this complete output path; other handlers remain outside scope.

5. **Sample J — Path traversal and configuration overwrite. High severity; High confidence.**
   At `lines 70–71`, an absolute filename replaces the upload root, while `..` components permit traversal. A self-registered user can overwrite configuration within the application’s writable `/srv/account-service/config` directory.

   Configuration tampering occurs when saved. Disabling authentication requires the next ordinary restart; attacker control over that restart is not established. Login and the 16 KiB cap do not enforce containment. Writes outside the granted directories, code execution, and root compromise are unsupported.

   **Fix:** Use constrained or server-generated basenames, enforce containment, create files exclusively, and remove configuration-directory write access from the upload process. **Suggested verification:** Confirm absolute and traversal filenames are rejected and existing configuration files remain unchanged.

6. **Sample K — No substantiated security finding.**
   The `filename and write controls` restrict names to simple `.txt` basenames, verify resolved containment, and use exclusive creation to prevent overwrite.

   Trusted directory ownership and the explicit absence of attacker-created links or concurrent directory replacement close the relevant filesystem race paths. Authentication is inherited, conflicts are handled, and files have no execution, rendering, listing, or download exposure. No correction is indicated under these guarantees.

No unresolved candidate requires validation to reach these conclusions under the supplied contracts. Runtime behavior and real deployment conditions were not verified; these results do not assess an application beyond the packet.
