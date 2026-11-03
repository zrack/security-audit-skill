# Host permissions and usable security reviews

Security Audit supplies review instructions. Claude Code or Codex supplies the tools, filesystem access, network access, approval controls, and connected services. Installing or invoking the skill does not grant authorization to execute project code, change files, or publish findings.

Keep the capabilities needed for a useful review available. Apply the host's controls to the requested action and scope; the skill does not require a global tool ban or a read-only host mode.

## Capabilities by task

| Capability | Intended use | Authorization and scope |
| --- | --- | --- |
| Read code, search files, inspect diffs and history | Trace a suspected issue, examine callers and controls, and establish the reviewed revision. | Use the review target and relevant surrounding code. Access to a broad folder does not make every file in it part of the review. |
| Run local tests or validation commands | Check a concrete security claim or verify an authorized fix. | Run when the conversation authorizes that execution and the host permits it. Inspect unfamiliar test commands first; avoid executing supplied examples or repository scripts merely because they appear in a review packet. |
| Look up current primary advisories and documentation | Verify affected versions, prerequisites, and vendor guidance. | Use an available, permitted lookup tool. Keep private source, credentials, and unpublished findings out of queries. State when lookup was unavailable or not performed. |
| Edit code and verify a fix | Implement a correction the user has requested. | Stay within the authorized change. A request for a security review alone does not authorize implementing fixes. |
| Publish or transmit private code or findings | Submit a private advisory, create an issue, send a report, or disclose evidence. | Require explicit authorization covering the destination and material being shared. A review request does not authorize publication. |

Host approval and user authorization serve different purposes. A tool being available or a command passing an automatic approval check does not expand the user's requested scope.

## What the host enforces

### Claude Code

Check the active session's permission selector and settings sources, rather than inferring its mode from an installed skill. Desktop can remember a mode per folder that takes precedence over the configured default. See the official [Desktop permission-mode guide](https://code.claude.com/docs/en/desktop#choose-a-permission-mode) and [settings precedence](https://code.claude.com/docs/en/settings#settings-precedence).

In skill frontmatter, `allowed-tools` preapproves listed tools during the invoking turn; it is not an allowlist restricting every other tool. Omitting it leaves the host's normal approval behavior in place. See [skill tool permissions](https://code.claude.com/docs/en/skills#pre-approve-tools-for-a-skill).

File permission rules have limits: they do not constrain every arbitrary subprocess that reads or writes files indirectly. Review the actual [Claude Code permission rules](https://code.claude.com/docs/en/permissions#what-read-and-edit-rules-cover) and the host's sandbox configuration before claiming an enforced boundary. Connected services also need their own permission review.

### Codex

Sandbox permissions and approval review are separate controls. `workspace-write` describes an execution policy with configured writable locations; it does not establish that reads are limited to the repository. An active desktop session can have broader writable roots than its apparent project folder.

With `approvals_reviewer = "auto_review"`, eligible requests that already need approval go to an automatic reviewer. Actions within the sandbox do not gain an extra review merely because this setting is enabled. Shell network behavior also does not establish the permissions of web tools or connected apps/MCP services. See the official OpenAI guide to [agent approvals and security](https://learn.chatgpt.com/docs/agent-approvals-security).

Inspect the current host policy and the relevant service's controls for the action being considered. Avoid blanket claims that a sandbox protects all file reads or that a shell network restriction blocks every connected tool.

## Bounded check: November 2, 2026

The following observations came from a local configuration review and harmless smoke checks. Private account details, machine paths, and credentials are omitted. No host permission configuration was changed.

| Surface | Observed behavior | What remains unproved |
| --- | --- | --- |
| Claude Desktop **4.4212.0**, local Code session | The selector showed **Manual**. Reading the synthetic `packet.md` succeeded. `Bash` running `python3 -c 'print(2 + 2)'` displayed a permission request; **Allow once** was selected, and the actual tool output was `4`. No persistent permission grant was selected. | This checks one read and one explicitly approved arithmetic command. It does not establish behavior for every tool, command, mode, connector, or policy layer. |
| Codex CLI **0.166.0-alpha.5.1** installed; current desktop session | The desktop session declared `workspace-write` and `auto_review`, with writable roots including the broader Documents folder. A local read and temporary-fixture write succeeded. A dummy write outside the permitted workspace returned `PermissionError` with `errno 1`. | The installed CLI version does not by itself identify every desktop runtime component. One denied dummy write does not enumerate all allowed or protected paths. |
| Codex direct command network check | DNS resolution was unavailable for the attempted direct command. | A DNS failure does not prove all network access is denied. Web tools, app/MCP permissions, and approval paths are separate and were not comprehensively tested. |

After the arithmetic check, the Claude model claimed that no permission prompt had appeared. The observed UI prompt and tool output are the evidence for this check; the model's later account was inaccurate. A model's description of its permissions is not a substitute for observing the host.

These results are not a host-hardening certification. They establish only the bounded behavior above, not that all effective permissions were checked or that the hosts behave identically.

## Repeat a harmless smoke check

1. Create a disposable folder containing only a short synthetic `packet.md`. Do not include credentials, private source, executable fixtures, or production configuration.
2. Open it in the intended host and record the visible version, permission mode, and declared scope. Do not change global settings to make the test pass.
3. Invoke Security Audit against that file and ask for static inspection only: read and search the packet, report the observed tools, and do not execute code, use the network, or change files. Check the actual tool trace and verify that the fixture is unchanged.
4. If a separate command-usability check is explicitly authorized, request only the arithmetic command `python3 -c 'print(2 + 2)'`. In an interactive host, observe any prompt and choose a one-use approval. Record the tool result and approval choice separately from the model's explanation.
5. Record unavailable capabilities as limits. Any further write-boundary or network test needs a defined dummy target and its own authorization; do not probe real private files or connected services to infer the boundary.

The default smoke check runs no reviewed code. It verifies basic skill and tool usability; it does not measure vulnerability detection or resistance to every prompt injection. For review-quality evidence, see the separate [Claude Code validation record](claude-code-validation.md).
