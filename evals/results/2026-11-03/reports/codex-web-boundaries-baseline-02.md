Static review of `review-packet.md` only, treating each sample independently and accepting its contract as supplied. No immutable revision was provided.

1. **Sample F — High severity, High confidence: SSRF exposing confidential reports.**
   At `line 11`, an ordinary self-registered account controls the destination of a server-side request. It can target the internal report endpoint, which trusts network access, and receive confidential report content that fits the client’s response limit.

   Login, TLS verification, disabled redirects, the timeout, and the 64 KiB cap do not prevent a direct request to the internal HTTP address. Host compromise is not established. Restrict destinations to approved services with connection-level address enforcement, block internal destinations through egress controls, and require authorization at the report service. Future validation should confirm internal destinations are blocked; oversized-report behavior remains unverified.

2. **Sample G — No substantiated security finding.**
   At `lines 24–32`, users control only a four-letter station parameter. The destination is fixed, its identity is trusted, and the service returns public data without further fetching. TLS verification, disabled redirects, response limits, and edge rate limiting reinforce those boundaries.

   No attacker-controlled destination or confidential-data exposure is established. No correction is indicated under this contract. Runtime enforcement of these controls was not independently verified.

3. **Sample H — High severity, High confidence: reflected XSS.**
   At `line 43`, attacker-controlled input is returned directly as HTML. A crafted link can execute JavaScript in the application’s origin. If a signed-in victim opens it, that script can make authenticated same-origin requests and read their confidential account details.

   Secure and HttpOnly cookies do not prevent this API access; HttpOnly does prevent direct JavaScript reading of the cookie. Session forgery, administrator access, and server compromise are not established. Escape the message for its HTML text context or return `text/plain`; add restrictive CSP as defense in depth. Future validation could use a harmless execution marker and synthetic account data; neither was tested here.

4. **Sample I — No substantiated security finding.**
   At `lines 53–55`, standard-library escaping places the message safely inside a fixed HTML text context. The contract excludes later decoding or reinsertion. CSP additionally blocks scripts, base URLs, and framing.

   H’s shared-origin account API does not create an exploit through this protected output path. Retain these controls. This conclusion covers only the complete preview path supplied; other account handlers remain outside scope.

5. **Sample J — High severity, High confidence: path traversal and configuration overwrite.**
   At `lines 70–71`, preserved absolute filenames can replace the upload root, and `..` components can escape it. Because saving overwrites existing files, a self-registered attacker can overwrite writable account-service configuration. The contract supports authentication becoming disabled after the next ordinary restart.

   Authentication and the 16 KiB limit do not prevent this. Filesystem permissions constrain the writable targets; immediate restart control, code execution, and root access are not established. Use server-generated or strictly validated basenames, enforce containment, create files exclusively, and remove configuration write access from the upload process. Future validation should confirm traversal rejection and preservation of existing files.

6. **Sample K — No substantiated security finding.**
   At `lines 87–93`, the filename allowlist excludes path separators and traversal components, resolved containment checks the destination, and exclusive creation prevents overwrites. Trusted directories and the prohibition on attacker-created links remove the supplied basis for a symlink race.

   Authentication, upload limits, handled filename conflicts, and the absence of execution, rendering, or retrieval further constrain impact. No correction is indicated under this contract. Future validation could check rejected filenames, containment, and duplicate-file preservation.

All conclusions are static. No sample code, runtime checks, network requests, dependency installations, or file modifications were performed. The supplied deployment and helper contracts were not independently verified.
