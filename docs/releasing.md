# Releases and verified installation

The portable skill remains three files: `SKILL.md`, `agents/openai.yaml`, and `LICENSE`. Release controls protect how those files reach you. They do not change your host's tools or require a particular permission mode.

## Verify and install a release

This route needs a current [GitHub CLI](https://cli.github.com/) with release/attestation verification commands, internet access, and an archive extractor. It does **not** need Git, Python, or an installer script. Have your local Claude Code or Codex host installed and signed in first.

Install under the same account and environment that runs the host. If you use WSL, a container, or a remote host, its skill folder belongs inside that environment. Copying into your desktop profile does not automatically install into those environments or web/cloud sessions.

Check GitHub CLI sign-in with `gh auth status`. If needed, complete `gh auth login` using your own GitHub account. You do not need write or administrator access to this public repository to verify a release.

For **v0.2.1**, use the copyable download and verification commands in the [current release notes](https://github.com/zrack/security-audit-skill/releases/tag/v0.2.1), then follow extraction and installation below. Those commands include the exact source commit for that release. The [source-checkout quickstart](../README.md#install) also selects v0.2.1.

The commands below are a reproducible **prior-release example for v0.2.0**, whose source is [commit `6d1b7bbea1e9804585df912a51d53cb350dea9d5`](https://github.com/zrack/security-audit-skill/commit/6d1b7bbea1e9804585df912a51d53cb350dea9d5). Review the source changes you intend to trust. When selecting another release, change its version and both `--source-digest` and `--signer-digest` values together to that release's expected commit; do not copy a commit from downloaded metadata alone.

### 1. Download and verify

Run in your terminal. Create a new, empty directory first; choose another directory name if it already exists. These commands work in macOS/Linux shells and Windows PowerShell:

```sh
mkdir security-audit-v0.2.0
cd security-audit-v0.2.0
gh release verify v0.2.0 --repo zrack/security-audit-skill
gh release download v0.2.0 --repo zrack/security-audit-skill --pattern security-audit.zip
gh release verify-asset v0.2.0 security-audit.zip --repo zrack/security-audit-skill
```

Verify the ZIP's build identity against that exact source and workflow commit. This is one command on one line, including in PowerShell:

```sh
gh attestation verify security-audit.zip --repo zrack/security-audit-skill --signer-workflow zrack/security-audit-skill/.github/workflows/release.yml --source-ref refs/heads/main --source-digest 6d1b7bbea1e9804585df912a51d53cb350dea9d5 --signer-digest 6d1b7bbea1e9804585df912a51d53cb350dea9d5 --deny-self-hosted-runners
```

Stop if any verification fails. Do not bypass a failure by accepting a checksum alone. A valid signature binds origin and bytes; it does not establish that the instructions are safe or that the host is configured appropriately.

### 2. Extract and copy the skill folder

After verification succeeds, extract with your archive application, or use the command for your shell:

macOS / Linux, from the download directory:

```sh
unzip security-audit.zip -d unpacked
```

Windows PowerShell:

```powershell
Expand-Archive -LiteralPath .\security-audit.zip -DestinationPath .\unpacked
```

Open `unpacked`. Its inner `security-audit` folder contains exactly:

```text
security-audit/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── LICENSE
```

Using your file manager, create the parent `skills` directory below if needed, then copy the **inner `security-audit` folder** into it. Choose the host you use, or repeat for both:

| Host | Parent directory on macOS / Linux | Parent directory on Windows |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/` | `%USERPROFILE%\.claude\skills\` |
| Codex | `~/.agents/skills/` | `%USERPROFILE%\.agents\skills\` |

Here, `~` and `%USERPROFILE%` refer to your user home/profile folder. Enable hidden-file display if your file manager hides the dot-prefixed directories. Use a destination with no existing `security-audit` folder; compare and back up an older installation before replacing it.

For example, a Codex installation must end in `~/.agents/skills/security-audit/SKILL.md` (Windows: `%USERPROFILE%\.agents\skills\security-audit\SKILL.md`). Avoid an extra `security-audit/security-audit` level. The ZIP intentionally has no `scripts/install.py`.

### 3. Open the host and try it

Start a fresh local session in the code project you want reviewed. Choose an existing code file and replace `src/main.py` below with its path. Paste the request into the host's **chat**, not the terminal shell.

Claude Code:

```text
/security-audit Review src/main.py and its callers for security issues. State the reviewed scope and any missing context.
```

Codex CLI / IDE:

```text
$security-audit Review src/main.py and its callers for security issues. State the reviewed scope and any missing context.
```

In the desktop app, select **Security Audit** from its skill picker and send the same review request without the `$security-audit` prefix. Check that the response names the file you selected. If the skill is missing, see [troubleshooting](../README.md#troubleshooting). The [README demo](../README.md#use) uses an included packet from the source checkout; you do not need that checkout to review your own code with the ZIP installation.

The source-checkout installer in the [README](../README.md#install) remains an alternative. It requires Git and Python but no GitHub CLI. A copy is a snapshot; a deliberate directory symlink follows checkout changes. Neither path changes host permission settings.

The remaining sections are for **repository maintainers**. Installing or using the skill does not require these steps.

## Maintainer prerequisites

Configure these repository controls before publishing:

- Enable release immutability. It protects future releases; v0.1.1 predates this process and remains mutable.
- Protect version tags matching `refs/tags/v*` against updates and deletion, with no bypass actors. Allow creation of new version tags.
- Restrict the `release` environment to the `main` branch. No additional reviewer or wait timer is required for this solo-maintainer workflow; an explicit manual dispatch starts publication.
- Keep the existing three required validation checks on `main`. Review changes to skill instructions, installers, and workflows before merging.

The owner can inspect release immutability with `gh api repos/zrack/security-audit-skill/immutable-releases`. It must report `enabled: true`. Do this using existing repository-administration access. The release workflow deliberately has no administration credential and cannot enforce this setting itself. Its post-publication check also requires the resulting release to be immutable.

## Publish

1. Merge the intended changes through a pull request and wait for all required checks. Inspect the resulting `main` commit.
2. Run the **Release** workflow on `main`, supplying a new stable `vMAJOR.MINOR.PATCH` version and that exact full commit SHA. A moved branch or mistyped commit fails the build guard.
3. The read-only build job checks out that commit, runs structural checks and tooling tests, creates the portable ZIP, and records the source/run identity and resolved Python/zlib versions. Only the intended release files are uploaded as a workflow artifact.
4. The separate publication job downloads the artifact by its exact ID from the same run and fails on an artifact digest mismatch. It has release-write and short-lived attestation permissions; it does not check out or execute repository scripts.
5. Publication creates or verifies the version tag at the expected commit, produces build provenance, prepares a draft with its assets, checks the asset inventory/digests, and publishes. It never force-moves tags or replaces uploaded assets.
6. Confirm the published release is immutable, then run the consumer verification commands against the downloaded ZIP and expected commit.

For example, in **Bash**, after reviewing the current remote `main` revision. Choose a new, unused stable version; v0.2.0 and v0.2.1 are assigned releases:

```sh
git fetch origin main
release_commit=$(git rev-parse origin/main)
release_version=v0.2.2
gh workflow run release.yml --repo zrack/security-audit-skill --ref main \
  -f version="$release_version" -f expected_sha="$release_commit"
```

The ZIP is accompanied by checksums, build metadata, and its provenance bundle. GitHub's release attestation locks the published tag/assets to a signed release record. Build provenance separately identifies the workflow and source revision. Consumers must verify those identities for the controls to help.

Python uses the current patch in the workflow's selected minor version, and the actual runtime is recorded. Package tests check repeated builds within one runtime; identical DEFLATE bytes across different Python/zlib versions are not promised.

## Recover from a failed release

Inspect the failed run before retrying. A failure before publication may leave a version tag or draft. Keep its tag pinned to the original commit. If the workflow refuses an existing draft or conflicting assets, inspect it privately and repair/remove only the unpublished draft as appropriate; never overwrite assets blindly or retarget its tag. Use a new version when the source commit changes.

After immutable publication, fix mistakes with a new release version. Published assets cannot be replaced. Deleting an immutable release does not make its version tag reusable. Retain the failed run and source revision when investigating verification failures.

## References

- [GitHub immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
- [Enable immutability for future releases](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes)
- [Artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations)
- [GitHub CLI release verification](https://cli.github.com/manual/gh_release_verify)
- [GitHub CLI asset verification](https://cli.github.com/manual/gh_release_verify-asset)
- [GitHub CLI build verification](https://cli.github.com/manual/gh_attestation_verify)
