Reviewed only `review-packet.md`, treating each sample’s contract independently. This was static inspection: no sample execution, network access, dependency installation, or file modification. Suggested verification below was not performed.

1. **Sample F — High severity, High confidence: SSRF exposes confidential reports.**
   Lines 11–13 pass an account holder’s URL directly to the HTTP client and return its response. The contract establishes access to the internal report endpoint without another credential, so an ordinary self-registered user can obtain confidential report content through the application, subject to the client’s response limit.

   Login, TLS verification, timeout, disabled redirects, and the 64 KiB cap do not prevent this direct internal request. Host-administrator privilege is unnecessary for the demonstrated disclosure. Restrict destinations and prevent the fetch worker from reaching confidential internal services. Verify destination enforcement and egress restrictions; other reachable targets and consequences remain unexamined.

2. **Sample G — No substantiated security finding.**
   Lines 27–32 use a fixed, trusted destination. Users control only a four-letter station parameter. The contract explicitly excludes destination, DNS, header, and HTTP-option manipulation, redirects, and downstream fetching. TLS verification, response limits, edge rate limiting, and exclusively public response data further constrain the path.

   The supplied evidence does not establish SSRF or confidential-data disclosure. This conclusion depends on the stated client and service contracts; neither was tested.

3. **Sample H — High severity, High confidence: reflected XSS exposes victim account data.**
   Line 43 places attacker-controlled text directly into an HTML response. A victim opening a crafted preview link can execute attacker-supplied script on the account interface’s origin. That script can make authenticated same-origin API requests and read the victim’s confidential account details.

   HttpOnly prevents direct cookie reading; it does not prevent script from using the victim’s session. Secure cookies and unforgeable sessions likewise do not block this path. Administrator involvement and host privileges are **“not supplied”** at line 46; broader privileged compromise is unsupported.

   Return plain text or apply context-appropriate HTML escaping, with restrictive CSP as additional protection. Verify that attacker markup remains text throughout the complete output path.

4. **Sample I — No substantiated security finding.**
   Line 53 applies standard-library HTML escaping before inserting the message into HTML text. The contract guarantees exact delivery and no subsequent decoding or reinsertion. Line 55 adds a CSP that blocks scripts and other default resource loads, base URLs, and framing.

   These controls prevent H’s demonstrated injection path. The conclusion covers this complete preview output path; other account handlers are explicitly outside scope.

5. **Sample J — High severity, High confidence: path traversal permits authentication-disabling configuration overwrite.**
   Lines 70–71 combine an unrestricted attacker filename with `ROOT` and overwrite the resulting path. On POSIX, an absolute filename replaces the root prefix, while `..` can escape it. The process can therefore write attacker bytes into the account-service configuration directory.

   The contract explicitly supports disabling authentication **on the next ordinary restart**. Immediate restart control is **“not established”** at line 75; who can trigger activation remains unknown. Exact configuration filenames and required contents are unspecified.

   Filesystem writes are explicitly limited to the two named directories. The 16 KiB limit bounds each upload, and uploaded files are never executed or rendered as HTML. Code execution is not demonstrated.

   Enforce safe leaf filenames and containment, and remove configuration-write permission from the upload process. Verify both the destination boundary and effective filesystem permissions.

6. **Sample K — No substantiated security finding.**
   The filename allowlist excludes traversal and absolute paths; resolved containment adds a boundary check. Exclusive creation with `"xb"` prevents overwriting existing files, with conflicts handled.

   Trusted directory ownership and explicit restrictions against attacker-created directories, symlinks, and hard links block the supplied filesystem-substitution paths. Authentication and the size limit apply; files are neither executed, rendered, listed, nor downloadable. Aggregate storage limits are unspecified, but the packet does not establish a material storage-exhaustion consequence.
