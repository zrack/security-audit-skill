Static inspection found three substantiated issues: F, H, and J. Each sample was assessed independently under its supplied contract.

- **`Sample F` — High severity, High confidence: SSRF exposes internal reports.** A self-registered user can select the internal `/exports/current` URL. The application fetches it using its internal network access and forwards the response, exposing confidential reports within the client’s response limit.

  Login, verified TLS, disabled redirects, the two-second timeout, and the 64 KiB cap do not prevent this direct internal request. The cap limits disclosure; complete-report disclosure is not established. Host-administrator privilege is explicitly absent.

  **Fix:** Replace arbitrary URLs with server-controlled destinations or a strict destination allowlist enforced at connection time. Restrict internal egress and add authorization to the report service. **Future verification:** Confirm controlled internal destinations are rejected before connecting and permitted destinations still work.

- **`Sample G` — No substantiated security finding.** The user controls only a validated four-letter query parameter. The destination, DNS, headers, and HTTP options cannot be changed; redirects and downstream fetches are excluded by contract. Only public data is returned. TLS verification, rate limiting, the timeout, and the response cap further constrain abuse.

  No correction is indicated. Future verification should confirm invalid station values are rejected and valid values remain parameters to the fixed destination.

- **`Sample H` — High severity, High confidence: reflected XSS exposes a signed-in visitor’s account data.** Attacker-controlled `message` becomes executable HTML when a victim opens the crafted link. Its same-origin JavaScript can request and read the victim’s confidential account JSON.

  HttpOnly prevents direct cookie reading, but permits browser-authenticated same-origin requests. Secure cookies and unforgeable sessions do not interrupt this path. The contract states: “No claim about administrator users or host privileges is supplied.” Those consequences remain unestablished.

  **Fix:** Return plain text or escape the input for its HTML text context, as in I; retain restrictive CSP as additional protection. **Future verification:** Using test accounts, confirm supplied markup remains text and cannot execute or read account data.

- **`Sample I` — No substantiated security finding in the supplied preview path.** Standard-library escaping safely places the input inside the fixed paragraph. The contract excludes later decoding or reinsertion that could turn it back into markup. CSP additionally blocks scripts, base changes, and framing.

  No correction is indicated. Future verification should confirm markup and entity-containing inputs remain text and the CSP reaches the browser. Other account handlers are outside scope.

- **`Sample J` — High severity, High confidence: path traversal permits security configuration overwrite.** An absolute filename overrides the upload root; `..` components can also escape it. The supplied save contract permits attacker-controlled replacement of writable configuration files. This can disable account-service authentication on its **next ordinary restart**.

  Self-registration and the 16 KiB limit do not prevent configuration tampering. Explicit filesystem permissions bound the write capability to the uploads and configuration directories. The contract says: “No root privilege, executable deployment directory, symlink attacker, or immediate restart control is established.” These are unknowns, not guarantees of absence. Immediate authentication bypass, root compromise, and code execution are not demonstrated.

  **Fix:** Use server-generated or strictly validated filenames, enforce containment and exclusive creation, and remove the uploader’s configuration-write permission. **Future verification:** Check traversal and absolute-path rejection, existing-file preservation, and filesystem permissions.

- **`Sample K` — No substantiated security finding under the supplied contract.** The filename allowlist excludes traversal and absolute paths; resolved-path containment adds protection; `xb` prevents replacement. Trusted directory ownership and explicit restrictions on links and other writers leave no supported attacker-controlled filesystem race. Authentication is inherited, and files are neither executed nor exposed for rendering or download.

  No correction is indicated. Future verification should confirm filename rejection, handled conflicts, and the deployment’s directory and link restrictions.

Only the packet and security-audit instructions were read. No sample code was executed, network accessed, dependencies installed, unrelated files inspected, or files modified. Suggested verification steps were not performed; conclusions rely on the supplied contracts and do not rate any wider application.
