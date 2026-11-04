# Security Audit

A reusable skill for evidence-backed security reviews in Claude Code and Codex.

Security Audit gives your coding agent a review method: establish the scope, trace a suspected issue through the surrounding code, check existing controls, and report only what the evidence supports. It works with the host's available tools and can fit inside an existing security-review workflow.

![Security Audit workflow: define the scope, investigate the path, check controls, and report supported findings with coverage limits.](assets/security-audit-workflow.svg)

[Install](#install) · [First review](#use) · [Troubleshooting](#troubleshooting)

## What it reviews

Use it for a security-focused review of a snippet, selected files, working-tree changes, a commit range, a pull request, dependency changes, or a repository. Relevant review areas include:

- Secrets, sensitive data exposure, and unsafe logging.
- Authentication, object authorization, tenant isolation, and privilege changes.
- Injection, browser security, and session handling.
- File paths, uploads, archive extraction, and unsafe parsing.
- Network trust boundaries, SSRF, and TLS configuration.
- Security-sensitive state, resource abuse, and agent/tool permissions.
- Deployment defaults, CI permissions, and dependency changes.

A suspicious pattern starts an investigation. It does not automatically become a vulnerability. The skill separates supported findings, candidates that need validation, and optional hardening observations.

## Install

Start with a working, signed-in **Claude Code or Codex** on your computer. This skill has no separate account or API setup. If you need the host first, follow the official [Claude Code quickstart](https://code.claude.com/docs/en/quickstart) or [Codex CLI setup](https://learn.chatgpt.com/docs/codex/cli).

Choose an installation route:

- **Source installer below:** requires Git and Python 3.10 or newer. No extra Python packages are needed.
- **[Verified ZIP](docs/releasing.md#verify-and-install-a-release):** requires a current GitHub CLI and an archive extractor, with no Git or Python required.

These are local installations. For Claude Desktop, use its local **Code** mode; for Codex, use a local desktop, CLI, or IDE session. If the host runs in WSL, a container, or a remote environment, install there. Local folders are not automatically synced to web/cloud sessions or other computers.

### 1. Download the source

Run these commands in your **terminal**, such as Terminal on macOS/Linux or PowerShell on Windows:

```sh
git clone --branch v0.2.1 --depth 1 https://github.com/zrack/security-audit-skill.git
cd security-audit-skill
```

The version tag pins the release. Git may print a normal "detached HEAD" notice when checking out a tag.

### 2. Choose your host and install

From the checkout above, run **one** command for the host you use:

| Install for | macOS / Linux | Windows PowerShell |
| --- | --- | --- |
| Claude Code | `python3 scripts/install.py --target claude` | `py -3 scripts/install.py --target claude` |
| Codex | `python3 scripts/install.py --target codex` | `py -3 scripts/install.py --target codex` |
| Both hosts | `python3 scripts/install.py --target both` | `py -3 scripts/install.py --target both` |

Check your Python version with `python3 --version` or `py -3 --version`; it must be 3.10 or newer. If Windows provides Python through `python` instead of `py`, use `python` in the commands above.

### 3. Confirm the installation

The installer prints `Installed` and the destination for each selected host. `Already installed; unchanged` also means the files are in place. The final paths should be:

| Host | Required installed file |
| --- | --- |
| Claude Code | `~/.claude/skills/security-audit/SKILL.md` |
| Codex | `~/.agents/skills/security-audit/SKILL.md` |

Here, `~` means the home directory of the account running Python, including your user profile on Windows. The installer creates missing skill folders and copies only the portable instructions, metadata, and license. It does not install scanners or change host permissions.

Next, [open the host and run your first review](#use). A successful file copy and host discovery are separate checks.

### Optional: install for one project

Personal installations above work across your local projects. To keep the skill in just one project, run the installer from this checkout with the path to an **existing** code-project folder. Quote paths containing spaces. For example, for Codex:

```sh
python3 scripts/install.py --target codex --project "/path/to/your code project"
```

In Windows PowerShell:

```powershell
py -3 scripts/install.py --target codex --project "C:\path\to\your code project"
```

Replace the example path with your project and use `--target claude` for Claude Code, or `both` for both hosts. Project installs use `.claude/skills/security-audit` and/or `.agents/skills/security-audit` inside that folder. `--project .` refers to the current directory, so using it from this checkout installs into the skill repository itself.

For a manual source-checkout installation, copy the entire `skills/security-audit` folder to your chosen host's `skills` directory. For a release ZIP, copy the extracted `security-audit` folder instead; see the [ZIP steps](docs/releasing.md#verify-and-install-a-release). Use a destination that does not already exist.

### Updating an installed copy

Choose the next version, verify it, compare any local customizations, and back up the installed folder before replacing it. Use a fresh versioned checkout for the installer above. Rename or remove the old skill folder yourself, then rerun the installer. The installer leaves a different existing version untouched. A deliberate symlink installation follows checkout edits and updates immediately; use it when you want that development workflow. See [compatibility notes](docs/validation.md) and the [release guide](docs/releasing.md).

## Use

### Run your first review

This demo assumes a personal installation. If you installed only into a project, open that project and skip to [Review your own project](#review-your-own-project).

For a quick check with included sample code, open this `security-audit-skill` checkout in your local host. In a terminal, start `claude` or `codex` from this directory; in a desktop app or IDE, select this folder and start a fresh local session.

Paste the following into **Claude Code's chat**, not your terminal shell:

```text
/security-audit Review examples/review-packet.md for security issues. Use static inspection only; do not execute the sample or modify files. State the reviewed scope and any missing context.
```

In **Codex CLI or the IDE extension**, type `$` and select `security-audit`, or paste this into its chat:

```text
$security-audit Review examples/review-packet.md for security issues. Use static inspection only; do not execute the sample or modify files. State the reviewed scope and any missing context.
```

In the desktop app, select **Security Audit** from the skill picker and send the same review request without the `$security-audit` prefix if that interface uses a picker instead. See the official [Codex skill guide](https://learn.chatgpt.com/docs/build-skills) for your interface.

Check that the skill appears in the host's command/skill selector: type `/` in Claude Code, or use `/skills` or `$` in Codex CLI/IDE. Start a fresh session or restart Codex if it does not appear. The response should identify `examples/review-packet.md` as the target. This is a deliberately insecure, non-runnable example; compare the result with the [illustrative report](examples/review-report.md).

### Review your own project

Open the code project you actually want reviewed and start a session there. Give the agent a real file, change, or revision range in that project. Installing this skill does not make its source checkout the default audit target.

For example, replace `src/api/uploads.ts` with an existing path in your project:

```text
/security-audit Review src/api/uploads.ts and its callers for path traversal and unsafe file handling.
```

For Codex, use `$security-audit` or its skill picker with the same request. To review uncommitted work:

```text
$security-audit Review the current working-tree changes for security issues. State the base revision, separate new issues from existing ones, and report coverage limits.
```

If your working tree is clean, choose an existing file or a commit range instead. Dependency-review example:

```text
$security-audit Review the dependency changes between main and HEAD. Verify current advisory claims where lookup is available, and distinguish affected versions from reachable application impact.
```

The skill activates for security-focused work. It is not intended to turn every implementation task or general code review into a security audit.

Use your normal host permissions. Code reading, search, diffs, authorized local tests, and current advisory lookups are useful review capabilities. This skill neither grants tools nor installs tool restrictions. See [practical host permissions](docs/host-permissions.md) for choosing the scope and checking approvals without disabling useful work.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `git` or Python command is not found | Install the prerequisite for the source route, or use the verified ZIP route. On Windows, try the installed `py -3` or `python` launcher; check for Python 3.10+. |
| Git says the checkout directory already exists | Clone into a fresh folder; do not mix a new checkout into an existing directory. |
| `scripts/install.py` cannot be found | Run the installer from the cloned `security-audit-skill` directory. The portable ZIP intentionally contains no installer. |
| `Refusing to overwrite existing destination` | Compare and back up the printed destination, then rename or remove that old installation before reinstalling. With `both`, a conflict in either host prevents both installs; choose just your host when appropriate. |
| Installed, but the skill is missing | Check the exact `SKILL.md` path above, restart the session/app, and verify you installed for the same OS account and environment the host uses. Check any managed skill restrictions. |
| Skill folder contains another `security-audit` folder | Place the directory containing `SKILL.md` directly under `skills`, so the path ends in `skills/security-audit/SKILL.md`. Compare existing contents before moving files. |
| Review reports no changed files | A clean working tree has no uncommitted diff. Give an existing file or an explicit commit range. |

Host discovery details: [Claude Code skills](https://code.claude.com/docs/en/skills) and [Codex skills](https://learn.chatgpt.com/docs/build-skills).

## What to expect

A report records the reviewed target and revision, the evidence actually examined, and the limits of the review. Findings include severity, confidence, location, impact, relevant prerequisites, a concrete fix, and a verification step. Unresolved candidates explain the missing evidence and a bounded next check.

When the evidence does not support a finding, the result is **No substantiated security findings in the reviewed scope**, followed by coverage and limits. A narrow review does not justify rating the security of the whole application.

See the [synthetic example report](examples/review-report.md) for the expected format. A user-requested report format or governing workflow takes precedence over that example.

## How the repository is organized

```text
security-audit-skill/
├── skills/security-audit/
│   ├── SKILL.md                 # Portable review instructions
│   ├── agents/openai.yaml        # Codex display metadata and default prompt
│   └── LICENSE                  # MIT notice retained in portable installs
├── assets/
│   └── security-audit-workflow.svg
├── examples/
│   ├── review-packet.md         # Synthetic code and review context
│   └── review-report.md         # Synthetic report example
├── docs/validation.md           # Compatibility and validation record
├── docs/host-permissions.md     # Useful tools, host controls, and permission checks
├── docs/releasing.md            # Verified installation and maintainer release process
├── evals/                       # Shared cases, rubric, and recorded native-host results
├── scripts/
│   ├── install.py               # Personal or project installation
│   ├── validate.py              # Structural checks
│   ├── evaluate.py              # Isolated case preparation and explicit result recording
│   └── package.py               # Distributable package
├── tests/                       # Repository tooling tests
├── .github/                     # Issue, pull request, and CI configuration
├── README.md
├── CONTRIBUTING.md
├── SECURITY.md
└── LICENSE
```

The portable instructions live in `SKILL.md`. The host supplies the model, tools, repository access, and authorization. The Python scripts support installation, validation, packaging, and evaluation records; they are not audit engines.

## Development

Run the repository checks after making changes:

```sh
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

To build a distributable package:

```sh
python3 scripts/package.py
```

Read [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance and [SECURITY.md](SECURITY.md) to report a vulnerability privately.

For instruction changes, use the [shared native-host evaluation suite](evals/README.md). Its optional standard-library helper prepares isolated cases and records explicit operator grades; it does not call providers or change host permissions.

## Limits and validation

This is an instruction-only skill, not an audit service or a guarantee that vulnerabilities will be found. Results depend on the host model, available tools, supplied context, review scope, and validation performed. Current advisory checks require access to current primary sources; the report must say when they were not performed.

The skill does not authorize running untrusted code, using discovered credentials, probing services, publishing findings, or implementing fixes. Those actions require authorization from the conversation and any governing workflow.

Validation includes structural checks and live native-host evaluations in Claude desktop Code mode and Codex CLI. The [shared results matrix](evals/results/2026-11-03/README.md) preserves baseline failures, fixes, rechecks, and invalidated fixtures. The final development candidate passed all six Codex cases and four of six Claude report-quality cases; both found the seven supported root causes, while Claude retained factual-calibration failures. See [validation and compatibility](docs/validation.md) for the exact scope and limits. These checks are not an effectiveness benchmark and do not establish detection rates or identical behavior across hosts.

Release hardening adds an explicit source-commit check, separate build and publication jobs, build provenance, and verification instructions. These controls establish the origin of a release; they do not certify the security of reviewed code. The [release guide](docs/releasing.md) describes the required GitHub controls and recovery procedure.

Created by Scott Zeitner. Released under the [MIT license](LICENSE).
