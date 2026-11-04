Static inspection of `review-packet.md` supports three findings: F, H, and J. Each sample was assessed independently under its supplied contract.

1. **Sample F — High severity, High confidence: SSRF reaches confidential reports.**
   The attacker-controlled URL flows directly into `http.get`, and the response is returned to the caller. A self-registered account can select the internal report endpoint. Confidential report disclosure is supported subject to the 64 KiB response limit; complete export retrieval is not established.

   Login, TLS verification, timeouts, response limits, and disabled redirects do not restrict the initial destination. Host administration or code execution is not established.

   **Fix:** Allowlist permitted destinations at connection time and restrict this worker’s access to internal services. Require independent authorization on the report service. **Verification:** Use a mocked transport to confirm prohibited destinations are rejected before connection.

2. **Sample G — No substantiated security finding.**
   The caller controls only a validated station parameter sent to a fixed, trusted public-data destination. The contract excludes attacker-controlled DNS, headers, options, redirects, and downstream fetching.

   TLS verification, response limits, timeout, and edge rate limits provide additional controls. The supplied data flow does not establish SSRF or confidential-data exposure.

3. **Sample H — High severity, High confidence: reflected XSS exposes victim account data.**
   `message` is returned unescaped as HTML. A signed-in victim following a crafted link can run attacker JavaScript in the account interface’s origin. That script can make authenticated same-origin requests and read the victim’s confidential account details.

   HttpOnly prevents direct JavaScript access to the cookie value; it does not prevent these authenticated requests or response reads. Secure cookies and unforgeable sessions do not stop the attack. Administrator compromise, state-changing API actions, and host execution are not established.

   **Fix:** Return plain text or apply HTML text-context escaping as in I. **Verification:** Confirm markup remains text throughout the complete output path, with no later decoding or reinsertion.

4. **Sample I — No substantiated security finding.**
   Standard-library escaping places attacker input safely within the paragraph’s text context. The contract explicitly excludes later decoding or insertion into another HTML context.

   Escaping is the primary control; the restrictive CSP adds protection. Secure and HttpOnly cookies remain relevant session controls. This conclusion covers only the supplied preview path, not other account handlers.

5. **Sample J — High severity, High confidence: path traversal permits configuration overwrite.**
   A POSIX absolute filename overrides `ROOT`; `..` components can also escape it. Because `save` overwrites the selected path, a self-registered user can overwrite writable account-service configuration. The contract supports authentication being disabled on the next ordinary restart.

   Filesystem permissions bound writes to the two supplied directories. The 16 KiB limit and prohibition on execution or HTML rendering do not prevent configuration tampering. Immediate restart control, root compromise, and code execution are not established.

   **Fix:** Use validated flat filenames, containment checks, and exclusive creation as in K; remove configuration-write permission from the upload process. **Verification:** Check that absolute/traversal filenames are rejected and existing files cannot be overwritten.

6. **Sample K — No substantiated security finding.**
   The filename allowlist rejects path separators and traversal syntax. Resolved-path containment restricts the destination, and exclusive creation prevents overwrites.

   The trusted-directory and no-link contracts remove the attacker-controlled filesystem changes needed for a symlink or path-resolution race. Existing-name conflicts are handled, and uploaded files have no execution, rendering, listing, or download exposure.

These are static conclusions based on the synthetic contracts. No sample code, runtime tests, network requests, dependency installation, unrelated project inspection, or file modifications occurred. Verification steps above are recommendations only; no immutable revision was supplied.
