# Security work agent brief

Copy the template below and replace every angle-bracketed field before sending
it. Use it with [SECURITY-PLAYBOOK.md](SECURITY-PLAYBOOK.md); do not use it to
authorize a generalized security framework or to publish private material.

Resolve the model from the active AI tool's configuration or session metadata
when the template is used. Record the resolved value and its source; never copy
a model from an old brief or assume one from the tool name.

```text
SECURITY WORK AGENT BRIEF

MODEL AND POLICY
- Tool: <tool-name>
- Resolved model: <resolved-model>
- Model resolution source: <active AI tool's configuration command or session field>
- Canonical AI policy: <AI-POLICY.md URL or authorized local path>
- Accepted proposal, if required: <public proposal URL>

TASK
- Security question: <one decision or demonstrated behavior to address>
- Affected user and deployment: <who is affected, under which configuration>
- Attacker/input/trust boundary: <actor, controlled input, required access>
- Demonstrated impact: <observed confidentiality, integrity, availability, or
  auditability impact; distinguish vulnerability, robustness defect, intended
  dangerous feature, and hardening request>
- Real public reproduction surface: <API, CLI, workflow, or other entry point>
- Affected versions/platforms: <verified versions and environments>
- Upstream ownership decision: <package/upstream/application/deployment owner,
  with primary-source evidence>
- Required prior art: <upstream documentation, source, advisory, issue, release,
  parser, validator, runtime policy, or platform mitigation URLs>
- Prior-art review date: <YYYY-MM-DD>
- Minimum-fix rationale: <why this is the smallest change that closes the
  demonstrated behavior; why upstream, an existing control, a dependency floor,
  documentation, or isolation is not sufficient or is preferable>

DELIVERABLE
- <single bounded fix, documentation decision, or bounded spike>
- <specific files and behavior allowed to change>
- <focused regression evidence and user-facing documentation>
- <durable residual-risk statement and required upstream/downstream records>

SCOPE
In scope:
- <exact repository, checkout, branch, modules, and public surfaces>
- <specific entry points and supported configurations>

Explicit non-goals:
- <related behavior that must not be changed>
- <future hardening, refactors, or follow-up work excluded from this task>

Forbidden scope:
- No generalized security harness, shared guard framework, new parser, or
  speculative abstraction.
- No unrelated dependencies, CI/CD, workflow, formatting, or API changes.
- No public disclosure of private reports, secrets, unreleased advisories,
  embargoed evidence, or unverified case studies.
- <additional case-specific prohibitions>

AUTHORIZATION
- Base repository and branch: <owner/repository:branch and base SHA>
- Permitted working checkout: <path>
- Permitted remotes and push target: <exact fork/remote and branch, or none>
- Commits authorized: <yes/no; exact scope>
- Pushes authorized: <yes/no; exact scope>
- Pull request authorized: <yes/no; draft/ready, base, and title constraints>
- Merge, release, settings, or advisory publication authorized: <normally no;
  list any separate explicit authorization>
- Never infer commit, push, ready-for-review, merge, release, or disclosure
  authorization from permission to edit.
- Required commit trailer: Assisted-by: <tool-name>:<resolved-model>
- Never add an AI Co-authored-by trailer.

VERIFY
Before editing:
- Base reproduction command: <exact command>
- Base expected/observed result: <specific failing or unsafe result>
- Fixture and trust-boundary explanation: <direct minimal fixture, no harness>
- Entry-point inventory: <every public path to the same operation>

Acceptance commands:
- <exact command 1, including working directory and required environment>
- <exact command 2, including working directory and required environment>
- <exact base-fails command and expected failure>
- <exact head-passes command and expected success>

Required surfaces:
- <real public API/CLI/workflow surface to exercise>
- <native interface test when native code performs the operation>
- <lazy/eager, plugin, dispatch, or platform paths where applicable>

Positive controls:
- <control proving the fixture reaches the demonstrated behavior>
- <control proving the check distinguishes unmodified base from candidate head>
- <control proving valid behavior remains available where required>

Dependencies, CI/CD, and downstream compatibility (where applicable):
- Advisory and affected-range evidence: <primary URLs and review date>
- Minimum supported version check: <exact environment and command>
- Resolved version check: <exact environment and command>
- Dependency review: <direct/transitive/build/workflow changes and result>
- Workflow permissions/secrets/triggers review: <specific files and expected
  least-privilege, script-injection, and untrusted-content properties>
- Downstream base check: <exact repository, public surface, and command>
- Downstream head check: <exact repository, public surface, and command>
- Compatibility exceptions: <intentional behavior changes and documentation>

Evidence requirements:
- Return exact commands, exit statuses, relevant output, base/head SHAs, and
  unverified items.
- Put durable evidence in the PR, test, upstream issue, advisory, or project
  documentation; temporary agent logs alone are insufficient.
- Do not add prose tests, exact-wording synchronization checks, blanket
  exception handling, or suppressed diagnostics to obtain a green result.

REVIEW AND NON-CONVERGENCE
- Independent review must challenge demonstrated impact, ownership, minimum-fix
  choice, evidence, compatibility, confidentiality, and residual risk.
- Hard cap: <at most two independent review rounds after implementation>.
- Address concrete findings without restarting equivalent reviews.
- When successive reviews keep discovering new implementation surfaces,
  simplify the policy, cut the branch, run a bounded implementation spike,
  or choose upstream/sandboxing instead of continuing the planning loop.
- Stop and escalate contradictory evidence, an unclear trust boundary, or any
  need for a broader API, framework, or security architecture.

DISCLOSURE AND RESIDUAL RISK
- Private intake/coordination channel: <authorized channel and owner>
- Disclosure constraints: <embargo, upstream/downstream coordination, credit,
  CVE/advisory needs, and sanitized-publication requirements>
- Residual-risk destination: <PR, advisory, issue, or project documentation>
- Record remaining exposure, affected configurations, workarounds or isolation,
  untested claims, upstream dependencies, and an explicit revisit trigger.
- Do not publish case studies until their claims are public and independently
  verifiable.

CLEANUP
- <remove scratch processes, temporary fixtures, secrets, and unintended files>
- <preserve only intentional durable evidence and test fixtures>
- <return the worktree and temporary environments to their authorized end state>
- Report any pre-existing failure or unrelated change; do not repair or hide it.

STOP WHEN
- Every requested acceptance command has run with the stated result on the real
  surface, positive controls are valid, required compatibility checks pass, and
  the diff contains only the authorized minimum change.
- Durable evidence, residual risk, disclosure state, and cleanup are recorded.
- Only explicitly authorized commits, pushes, and PR actions have occurred.
- Or stop earlier and report the decision needed if impact is not demonstrated,
  another layer owns the fix, an existing control is sufficient, acceptance
  cannot distinguish base from head, review exceeds its cap, or the design is
  expanding into additional implementation surfaces.
```
