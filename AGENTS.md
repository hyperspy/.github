# hyperspy/.github

## Purpose

The organisation-level shared infrastructure for the HyperSpy GitHub
organisation: reusable workflows, composite actions, default community files
(`PULL_REQUEST_TEMPLATE.md`, `CONTRIBUTING.md`) and the shared AI policy and
compliance tooling (`AI-POLICY.md`, `scripts/`, the `compliance.yml` and
`self-test.yml` workflows). Adopting repositories point at this repository
to receive the policy, the commit-msg hook and the CI compliance check
without copying any scripts.

## Key Files

| File | What it is |
| --- | --- |
| `AI-POLICY.md` | Normative HyperSpy AI policy. Contains the pinned block embedded verbatim in every consumer's `AGENTS.md`. |
| `.pre-commit-hooks.yaml` | Public hook manifest for `check-ai-co-author` (commit-msg stage) and `check-agents-policy` (pins the AI policy block in `AGENTS.md`). |
| `.github/workflows/compliance.yml` | Reusable workflow. Three jobs: `ai-trailers`, `changelog`, `agents-policy`. |
| `.github/workflows/self-test.yml` | Internal CI: pytest + ruff, plus synthetic hook and script smoke tests against a scratch repo. |
| `scripts/*.py` | Stdlib-only enforcement scripts (commit-msg hook, CI trailer scan, changelog-fragment check, agents-policy pin checker, shared AI-pattern module). |
| `tests/` | pytest coverage for every script. |

## Working in this repository

- Run `python3 -m pytest -q tests` to execute the test suite.
- Run `pre-commit run --all-files` before opening a pull request.
- The scripts are stdlib-only and must stay so; never add third-party
  dependencies.
- Change the pinned block ONLY in `AI-POLICY.md`; every consumer's
  `AGENTS.md` is updated from there by `check-agents-policy --fix`.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
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
