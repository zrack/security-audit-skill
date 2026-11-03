# Releases and verified installation

The portable skill remains three files: `SKILL.md`, `agents/openai.yaml`, and `LICENSE`. Release controls protect how those files reach you. They do not change your host's tools or require a particular permission mode.

## Verify and install a release

Use a current [GitHub CLI](https://cli.github.com/). These commands require its release and artifact-attestation verification commands. Choose a version and obtain its full reviewed commit SHA from the release's tag and source changes. Check that revision against the changes you intend to trust; do not treat metadata downloaded beside a ZIP as an independent trust decision.

Run in a new, empty download directory:

```sh
gh release verify v0.2.0 --repo zrack/security-audit-skill
gh release download v0.2.0 --repo zrack/security-audit-skill --pattern security-audit.zip
gh release verify-asset v0.2.0 security-audit.zip --repo zrack/security-audit-skill
```

Then verify the ZIP's build identity, replacing `FULL_REVIEWED_COMMIT_SHA` with the expected 40-character commit:

```sh
gh attestation verify security-audit.zip \
  --repo zrack/security-audit-skill \
  --signer-workflow zrack/security-audit-skill/.github/workflows/release.yml \
  --source-ref refs/heads/main \
  --source-digest FULL_REVIEWED_COMMIT_SHA \
  --signer-digest FULL_REVIEWED_COMMIT_SHA \
  --deny-self-hosted-runners
```

Stop if any verification fails. Do not bypass a failure by accepting a checksum alone. A valid signature binds origin and bytes; it does not establish that the instructions are safe or that the host is configured appropriately.

After verification, extract into a new directory. The ZIP contains only `security-audit/SKILL.md`, `security-audit/agents/openai.yaml`, and `security-audit/LICENSE`. Copy that directory to `~/.claude/skills/security-audit`, `~/.agents/skills/security-audit`, or both. Project-local equivalents are supported too. Use a destination that does not exist, and compare/back up an older installation before replacing it. Start a fresh host session if needed.

The source-checkout installer in the [README](../README.md#install) remains an alternative. It requires Git and Python but no GitHub CLI. A copy is a snapshot; a deliberate directory symlink follows checkout changes. Neither path changes host permission settings.

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

For example, after reviewing the current remote `main` revision:

```sh
git fetch origin main
release_commit=$(git rev-parse origin/main)
gh workflow run release.yml --repo zrack/security-audit-skill --ref main \
  -f version=v0.2.0 -f expected_sha="$release_commit"
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
