Static review of `review-packet.md`, using each sample’s contract independently. No immutable revision was supplied. No sample code was executed, network used, dependencies installed, unrelated files inspected, or files modified.

**Sample F — High: SSRF exposing internal reports. Confidence: High.**
Location: lines 11–13; contract at line 16.

A self-registered account controls the complete destination URL. The server can therefore request the specified internal report endpoint and relay confidential responses accepted by the HTTP client.

Login does not exclude the attacker. TLS verification and disabled redirects do not block a direct HTTP request to the internal service. The timeout and 64 KiB limit constrain requests; they do not enforce destination authorization. Handling of oversized reports is unspecified, so full disclosure of arbitrarily large reports is not established. Host-administrator compromise is unsupported.

Fix: restrict destinations with an enforced allowlist and internal-network egress controls. Require authorization at the report service. Verification should establish that attacker-selected destinations cannot reach internal services.

**Sample G — No substantiated security finding.**
Location: lines 24–33; contract at line 36.

The attacker controls only a four-uppercase-letter station parameter sent to a fixed, trusted public service. The contract excludes control over destinations, DNS, headers, or HTTP options, and excludes secondary fetches. Verified TLS and disabled redirects preserve that boundary. Public-only responses, response limits, timeouts, and edge rate limits further constrain exposure.

The server-side request alone does not establish SSRF. No correction is indicated under this contract; preserve these controls.

**Sample H — High: reflected XSS exposing account details. Confidence: High.**
Location: line 43; contract at line 46.

An attacker-controlled message is rendered directly as HTML. A signed-in victim opening a crafted preview link can execute attacker JavaScript in the account interface’s origin. That script can make authenticated requests to the specified JSON API, read confidential account details, and disclose them.

HttpOnly prevents direct cookie reads, but does not prevent authenticated same-origin requests. Secure cookies and unforgeable sessions do not stop script execution within the victim’s existing session. Administrator access, host compromise, and actions involving unspecified handlers are unsupported.

Fix: return the message as plain text, or escape it for its HTML text context. Add a restrictive CSP as additional protection. Verification should establish that submitted markup remains text and cannot create executable elements.

**Sample I — No substantiated security finding.**
Location: lines 53–55; contract at line 59.

Standard-library `html.escape(..., quote=True)` correctly encodes input inserted into the paragraph’s text context. The contract excludes later decoding or reinsertion. The restrictive CSP adds protection against script execution.

The shared account origin does not establish an exploit through this output path. No correction is indicated; preserve escaping and CSP. Other account handlers remain outside scope.

**Sample J — High: path traversal enabling configuration overwrite. Confidence: High.**
Location: lines 70–71; contract at line 75.

The preserved filename can contain traversal components or an absolute path. On POSIX, an absolute right-hand path replaces the upload root; traversal can also escape it. `save()` then overwrites the chosen writable destination.

A self-registered attacker can overwrite account-service configuration, enabling authentication to be disabled on the next ordinary restart. This consequence is delayed; immediate restart control is not established.

Filesystem permissions bound the writes to the stated writable locations. The 16 KiB limit does not prevent small configuration changes. Code execution, root access, and HTML execution are unsupported.

Fix: generate filenames, enforce containment, create files exclusively, and remove the upload process’s configuration-write permission. Verification should cover absolute paths, traversal, overwrite rejection, and filesystem permissions.

**Sample K — No substantiated security finding.**
Location: lines 87–93; contract at line 97.

The full-match filename allowlist excludes path separators and traversal. Resolution and containment checks reinforce that boundary. Exclusive creation prevents overwrites, with conflicts handled as specified.

Trusted directories and the explicit restrictions on links and concurrent filesystem replacement remove the prerequisites for the suspected symlink or replacement race. Authentication, upload-size limits, and the absence of execution, rendering, listing, or downloading further constrain exposure.

Aggregate storage exhaustion is not established without evidence about quotas, capacity, and service impact. No correction is required for an established vulnerability under this contract.

All conclusions are based on static evidence and the supplied helper contracts. Runtime behavior, deployed controls, and remediation effectiveness were not tested.
