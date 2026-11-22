Reusable GitHub workflow used in the HyperSpy community

This repository centralises the shared CI workflows, composite actions, and AI
policy enforcement tooling that the HyperSpy organisation uses across its
repositories. Adopting the AI policy in a downstream repository is a
four-step process described below.

## What lives here

### Reusable workflows (`.github/workflows/`)

- `doc.yml` - builds the documentation site.
- `push_doc.yml` - publishes the built documentation to the `gh-pages` branch.
- `push_doc_preview.yml` - publishes a preview of the documentation for a pull
  request.
- `package_and_test.yml` - builds sdist/wheel packages and runs the test suite.
- `integration_tests.yml` - runs the integration test matrix against multiple
  dependency versions.
- `download_exspy_GOS.yml` - downloads the eXSpy GOS test data artefacts.
- `download_rsciio_test_data.yml` - downloads the RosettaSciIO test data
  artefacts.
- `release_pure_python.yml` - publishes a pure-Python release to PyPI (cannot
  be reused as a composite workflow because of trusted-publisher constraints).

### Composite actions (under `.github/`)

- `create-github-release/` - creates a GitHub release from a tag.
- `download-artifact/` - downloads a workflow run artefact.
- `extract-release-notes/` - extracts release notes from a changelog fragment
  tree.

### AI policy compliance tooling

- `AI-POLICY.md` - the canonical HyperSpy AI policy text, including the
  sentinel-delimited block that must be pinned in every consumer's `AGENTS.md`.
- `scripts/` - the Python tools that the reusable workflow and the pre-commit
  hooks run:
  - `hyperspy_ai_patterns.py` - the single source of truth for the AI
    `Co-authored-by` regexes.
  - `check-ai-co-author.py` - commit-msg hook that rejects prohibited
    `Co-authored-by` AI trailers.
  - `ci-check-ai-trailers.py` - CI-side scan over a commit range.
  - `check-agents-policy.py` - verifies (and with `--fix` inserts/refreshes)
    the pinned policy block in `AGENTS.md`.
  - `ci-check-changelog.py` - towncrier-aware check that a changelog fragment
    is present when package source files change.
- `.pre-commit-hooks.yaml` - the manifest that publishes the
  `check-ai-co-author` hook to consumers that add this
  repository to their `repos:` list.
- `.github/workflows/compliance.yml` - reusable workflow for compliance checks
  and opt-in AI-policy updates. Normal jobs are `ai-trailers`, `changelog`,
  and `agents-policy`; `ai-policy-update` runs only when explicitly enabled.
- `.github/workflows/update-ai-policy-schedule.yml` - daily caller for this
  repository's policy updates.
- `.github/workflows/self-test.yml` - runs the test suite and an end-to-end
  smoke of the hooks and CI scripts on every pull request to this repository.

## Adopting the AI policy in a repository

The shared tooling is one repository, one hook list, and one workflow caller.
Adopting it in any HyperSpy organisation repository is a four-step recipe.

### 1. Add the pre-commit hooks

Add (or extend) the consumer's `.pre-commit-config.yaml` with the following
block, pinned to the first stable tag:

```yaml
default_install_hook_types: [pre-commit, commit-msg]
repos:
  - repo: https://github.com/hyperspy/.github
    rev: v1.0.0
    hooks:
      - id: check-ai-co-author
```

The `check-ai-co-author` hook ships from this repository's
`.pre-commit-hooks.yaml` and runs at the `commit-msg` stage. It rejects commits
that carry a prohibited AI `Co-authored-by:` trailer.

### 2. Add the compliance workflow caller

Create `.github/workflows/compliance.yml` in the consumer repository:

```yaml
name: Compliance
on:
  pull_request:
  push:
    branches-ignore: ['dependabot/**', 'pre-commit-ci-update-config']
jobs:
  compliance:
    uses: hyperspy/.github/.github/workflows/compliance.yml@v1
    with:
      source_dirs: <package dir>   # omit to derive from [tool.towncrier]
```

The workflow checks out this repository at the floating `v1` tag (configurable
via the `tooling_repo` / `tooling_ref` inputs, see below), so a consumer
update is a one-line bump of the `uses:` reference.

### 3. Keep the pinned policy block synchronized

Add a thin caller workflow to schedule policy synchronization daily:

```yaml
name: Schedule AI policy updates
on:
  schedule:
    - cron: "17 3 * * *"
  workflow_dispatch:
permissions:
  contents: write
  pull-requests: write
concurrency:
  group: ai-policy-update-${{ github.repository }}
  cancel-in-progress: false
jobs:
  update-policy:
    uses: hyperspy/.github/.github/workflows/compliance.yml@v1
    with:
      update_policy: true
```

The existing `compliance.yml` reusable workflow is kept as the only
implementation workflow. The schedule caller passes `update_policy: true` to
enable the opt-in policy-update job and grants write permissions only to that
job chain. Normal pull-request and push callers remain read-only.

The policy update uses a fixed `ai-policy-update` branch and opens or updates
a ready-to-review pull request containing only `AGENTS.md` changes. No direct commit is
made to `main`.

The workflow also accepts `policy_branch` and `policy_pr_title` inputs.
GITHUB_TOKEN-created pull requests may require workflow approval before CI runs;
use a GitHub App installation token or fine-grained PAT if PR workflows must
run without approval.

### 4. Require the status checks

In the consumer repository's branch protection settings, mark the three
required status checks:

- `compliance / ai-trailers`
- `compliance / changelog`
- `compliance / agents-policy`

Each job id becomes a required check automatically because the shared
workflow does not set a `name:` on its jobs.

## Workflow inputs

The shared `compliance.yml` workflow accepts the following inputs. They are
forwarded to the second `actions/checkout@v4` step that fetches this
repository at the chosen ref.

| Input                | Type    | Default            | Description |
| -------------------- | ------- | ------------------ | ----------- |
| `tooling_repo`       | string  | `hyperspy/.github` | Repository holding the shared compliance scripts and `AI-POLICY.md`. |
| `tooling_ref`        | string  | `v1`               | Git ref of `tooling_repo` to use (tag, branch, or commit SHA). |
| `pyproject`          | string  | `pyproject.toml`   | Path to the `pyproject.toml` used to derive towncrier settings. |
| `source_dirs`        | string  | `''`               | Space-separated source directories whose `.py` changes require a changelog fragment. Empty = derive from `[tool.towncrier]`. |
| `changelog_dir`      | string  | `''`               | Changelog fragment directory. Empty = derive from `[tool.towncrier].directory`. |
| `check_changelog`    | boolean | `true`             | Run the `changelog` job. |
| `check_agents_policy`| boolean | `true`             | Run the `agents-policy` job. |
| `agents_file`        | string  | `AGENTS.md`        | Root `AGENTS.md` that must carry the pinned policy block. |
| `update_policy`      | boolean | `false`            | Run only the policy-update job instead of normal compliance jobs. |
| `policy_branch`      | string  | `ai-policy-update` | Fixed branch used for policy update pull requests. |
| `policy_pr_title`    | string  | `Update pinned AI policy block` | Title for the policy update pull request. |

## Testing changes before a tag

The workflow can be exercised against a fork before any tag is published. In
a consumer's `compliance.yml`, override the two inputs so they point at the
fork:

```yaml
with:
  tooling_repo: <org>/<fork-of-dot-github>
  tooling_ref: <branch-on-fork>
```

While iterating, pin the pre-commit `rev:` to a full commit SHA from the fork
branch instead of a tag, so each consumer update lands immediately when the
SHA is bumped.

## Versioning

- This repository follows semver: tags have the form `vX.Y.Z`.
- The floating tag `v1` is moved forward on every compatible (non-breaking)
  release. Consumers that pin `v1` (the recommended choice for the shared
  workflow `uses:` reference) pick up new minor and patch releases
  automatically.
- The pre-commit.ci autoupdate follows the new tag. Consumers that pin
  `rev: vX.Y.Z` instead of `v1` should re-vendor on each minor bump.

## Developing

After cloning, install the local hooks:

```bash
pre-commit install --install-hooks
```

The Python tooling is exercised by:

- `pytest tests/` - the unit tests for the four scripts in `scripts/`.
- `pre-commit run --all-files` - the same checks that run on every pull
  request.
- The `.github/workflows/self-test.yml` workflow - an end-to-end smoke of
  the hooks and CI scripts on this repository.
