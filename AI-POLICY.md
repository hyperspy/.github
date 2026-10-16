# HyperSpy AI Policy

This file is the normative contract for AI-assisted contributions to repositories of the
[HyperSpy GitHub organization](https://github.com/hyperspy). The explanatory guide is the
HyperSpy developer guide section *Coding with AI assistants*; the proposal process lives in
[hyperspy/hyperspy-proposals](https://github.com/hyperspy/hyperspy-proposals). When texts
disagree, this file wins.

## Rules

- **R1 Proposal gate.** Non-trivial AI-assisted changes require an accepted proposal in
  hyperspy/hyperspy-proposals before the implementation pull request is reviewed. Trivial
  AI-assisted changes and human-only changes need no proposal (recommended for large
  human-only changes).
- **R2 Attribution.** Every commit produced with AI assistance carries the git trailer
  `Assisted-by: <tool>:<model>` (the Linux kernel convention), naming the tool you interact
  with directly, not a wrapper around it.
- **R3 `Co-authored-by:` is for humans.** Commits must not carry `Co-authored-by:` trailers
  naming AI tools. The shared commit-msg hook and CI check reject them.
- **R4 Disable auto-injection.** Configure your tool so it does not add AI co-author trailers
  (Claude Code: `"includeCoAuthoredBy": false`; GitHub Copilot: disable
  `github.copilot.chat.commitMessageGeneration`; Cursor: disable commit attribution;
  OpenCode / oh-my-openagent: check skill and plugin configurations).
- **R5 Disclosure.** Declare AI assistance in the pull-request template and link the accepted
  proposal when R1 applies.
- **R6 Responsibility.** The contributor reviews, understands and takes full responsibility for
  every submitted line; AI-assisted contributions meet the same quality bar as any other.

## Enforcement (shared tooling in this repository)

- pre-commit hooks (`.pre-commit-hooks.yaml`): `check-ai-co-author` (commit-msg stage) and
  `check-agents-policy` (keeps the pinned block below in sync).
- Reusable workflow `.github/workflows/compliance.yml` with jobs `ai-trailers`, `changelog`
  and `agents-policy`.
- Adoption instructions: see [README.md](README.md).

## Pinned block for AGENTS.md

Repositories embed the block below verbatim in the MANUAL section of their root `AGENTS.md`;
the `check-agents-policy` hook inserts and updates it. Never edit it in a repository - change
it here.

<!-- hyperspy-ai-policy:begin -->
## HyperSpy AI policy (ecosystem contract)

Canonical source: https://github.com/hyperspy/.github/blob/main/AI-POLICY.md - do not reword
this block; the `check-agents-policy` pre-commit hook keeps it synchronized.

- Non-trivial AI-assisted changes need an accepted proposal in
  https://github.com/hyperspy/hyperspy-proposals BEFORE the implementation PR is reviewed.
  Trivial changes: PR review suffices.
- Every AI-assisted commit carries the trailer `Assisted-by: <tool>:<model>`
  (example: `Assisted-by: OpenCode:deepseek-4.0-pro`). Attribute the tool you interact with,
  not a wrapper.
- NEVER add `Co-authored-by:` trailers for AI tools; they are reserved for human co-authors.
  The `check-ai-co-author` commit-msg hook and the `compliance / ai-trailers` CI check reject
  them.
- Disable your tool's automatic co-author injection before committing: Claude Code
  `"includeCoAuthoredBy": false`; GitHub Copilot `github.copilot.chat.commitMessageGeneration`
  off; Cursor commit attribution off; OpenCode / oh-my-openagent: check skill and plugin configs.
- Run `pre-commit install` (installs the commit-msg stage) before your first commit; CI
  re-checks every PR commit regardless.
- Declare AI assistance in the pull-request template and link the accepted proposal when one
  is required.
<!-- hyperspy-ai-policy:end -->
