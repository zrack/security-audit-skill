# Security policy

This repository contains an instruction-only security-review skill and its installation, validation, and packaging tools. It is not an audit service. Reports should concern a security issue in this repository, such as unsafe installer behavior or instructions that cause a supported trust-boundary failure.

## Report privately

Use [GitHub private vulnerability reporting](https://github.com/zrack/security-audit-skill/security/advisories/new). Do not disclose an unresolved vulnerability, credentials, or sensitive evidence in a public issue or pull request.

Include the affected revision, relevant host or environment, a minimal reproduction or evidence path, the supported impact, and any important prerequisites. Use synthetic data and redact secrets. A live exploit is not required when the evidence establishes the issue.

Vulnerabilities found in another project while using this skill belong with that project's maintainers and disclosure process. Do not send private findings from that project here.

## Scope and updates

Security fixes are made against the current default branch. There is no separate long-term support policy for older copies. Installed skills are local copies unless you deliberately link them to a checkout; review and apply updates when appropriate.

Review requests do not authorize testing discovered credentials, probing live systems, or publishing private findings. Keep any reproduction within the authorization you already have.
