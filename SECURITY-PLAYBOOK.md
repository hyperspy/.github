# HyperSpy ecosystem security-work playbook

This is the canonical decision guide for security work across the HyperSpy
ecosystem. It covers reports, hardening, dependencies, CI/CD, disclosure, and
learning. It does not define a shared security implementation layer: fixes and
tests belong to the package that owns the demonstrated behavior.

Use the [security agent brief](SECURITY-AGENT-BRIEF.md) to authorize and bound
individual tasks. Record durable, public lessons in
[SECURITY-LESSONS.md](SECURITY-LESSONS.md). Follow the repository's security
policy for private reports and the normative [AI policy](AI-POLICY.md) for all
AI-assisted contributions.

## 1. Intake, threat model, and ownership

### Establish the affected user and demonstrated impact

Start with a specific actor, input, trust boundary, affected user, and outcome.
Record the required privileges, user interaction, configuration, versions, and
platform. Distinguish a demonstrated vulnerability, a robustness defect, an
intentional dangerous feature, and a hardening request.

Assess confidentiality, integrity, availability, and auditability through the
real public surface. A crash or parser exception alone does not establish a
security vulnerability. Conversely, a documented feature can cross a security
boundary when an application gives it untrusted input.

Classify the behavior without limiting the review to file parsing:

- **Code execution and injection:** expressions, templates, commands, plugins,
  metadata, generated code, and interpreter or shell boundaries.
- **Unsafe deserialization and expression evaluation:** pickle-like formats,
  object construction, dynamic imports, `eval`-style parsing, and unsafe type
  restoration.
- **File disclosure and path traversal:** archive members, absolute and relative
  paths, symlinks, external references, URL schemes, and implicit file access.
- **Dependency and software supply chain:** direct and transitive packages,
  build backends, actions, release tooling, artifacts, and provenance.
- **CI/CD:** token permissions, secrets, caches, artifacts, workflow triggers,
  script injection, and untrusted contributions.
- **Sensitive-data handling:** credentials, private datasets, personal data,
  logs, error messages, diagnostics, telemetry, and uploaded artifacts.
- **Resource exhaustion:** memory, CPU, disk, file descriptors, recursion,
  decompression, oversized metadata, and adversarial algorithmic complexity.
- **Native and platform boundaries:** memory safety, native parser behavior,
  filesystem semantics, process isolation, and platform-specific controls.

### Assign responsibility to the correct layer

Name the package, upstream project, application, and deployment owner involved.
Ask who can actually close the demonstrated behavior at its root:

- A package owns its own unsafe API behavior, integration mistakes, and failure
  to honor an explicit security contract.
- An upstream library owns defects in its parser, evaluator, runtime policy, or
  documented behavior. Route a minimal reproduction and evidence there.
- An application owns decisions to accept untrusted content, expose results,
  grant filesystem or network access, and select isolation.
- A deployment owner owns credentials, sandboxing, resource limits, network
  policy, and operating-system controls.

Do not fix vulnerabilities that belong upstream. Do not shift an application's
trust decision into a library, or disguise an upstream vulnerability as a
package-specific defect. Coordinate any temporary mitigation with the actual
owner and record its limits.

### Review primary-source prior art first

Prior-art review is mandatory before choosing a design. Read the current and
affected versions of upstream documentation, source, release notes, security
advisories, issue discussions, and proposed controls. Check Python and platform
capabilities, existing parsers and validators, safer dependencies, and runtime
policy controls.

Cite primary URLs and the review date. Verify claims against the actual code or
documentation version; do not treat search summaries, issue counts, generated
text, or another project's guard as proof. Record whether each control exists,
is merely proposed, or is rejected, and identify any downstream projects whose
behavior constrains a fix.

## 2. Minimum-fix decision tree

Work through these questions in order. Stop at the first disposition that
closes the demonstrated behavior without creating a broader maintenance burden.

1. **Is the impact demonstrated and owned here?**
   If not, obtain a focused reproduction, reclassify the report, or route it to
   the responsible project. Do not turn speculative hardening into an emergency
   security patch.

2. **Can upstream reasonably own the fix?**
   Prefer an upstream correction, explicit runtime policy, or documented trust
   boundary. Supply the smallest public-surface reproduction and affected
   versions. Do not maintain a downstream replica of an upstream fix.

3. **Does an existing mechanism already provide the boundary?**
   Prefer a maintained parser, validator, safer dependency, runtime policy
   control, operating-system restriction, or platform mitigation. Confirm that
   it covers the same entry points and native layer as the demonstrated behavior.

4. **Can a dependency or Python floor remove affected versions?**
   Compare advisory ranges with the actual supported minimum and the resolved
   environment. A floor is useful only if all supported resolutions exclude the
   affected behavior and the compatibility cost is justified.

5. **What is the smallest root-cause change?**
   Change the operation that crosses the boundary, not every caller that might
   reach it. Preserve valid use where possible. Prefer a direct fixture and one
   focused behavioral test over a generalized security harness.

6. **Are documentation and trust boundaries safer than an incomplete guard?**
   For intentional capabilities or risks that cannot be closed comprehensively
   at this layer, state the trust assumption, dangerous configuration, and safe
   deployment choice honestly. Do not imply that a partial filter makes hostile
   input safe.

7. **Is genuine isolation more honest than another limit?**
   Exhaustive resource-exhaustion guards are non-default. Prefer documented
   resource expectations and operating-system, process, container, or sandbox
   isolation for genuinely untrusted workloads. Add a specific limit only when
   a demonstrated case and ownership justify its ongoing cost.

8. **Is the change still proportionate?**
   Include API compatibility, downstream behavior, error clarity, testing,
   documentation, future upstream convergence, and maintenance in the cost.
   Reject a larger abstraction when a smaller disposition has the same security
   outcome.

Cut or stop the branch when impact cannot be demonstrated, another layer owns
the behavior, an existing control makes the change redundant, compatibility
cost exceeds the security benefit, or the design requires an expanding set of
partial guards. Record the reason and residual risk rather than continuing by
default. A bounded implementation spike may answer a specific technical
question; it is not authorization for a broad framework.

## 3. Evidence and compatibility

### Reproduce before editing

Exercise the real public API, CLI, workflow, or file-loading surface that an
affected user can reach. Record the exact commands, versions, fixture origin,
expected result, and observed result. Do not reproduce only through a private
helper that bypasses validation or dispatch.

Enumerate every public entry point to the behavior, including convenience APIs,
lazy and eager paths, plugin dispatch, and native calls where applicable. Test
the layer that performs the operation: when native code opens, parses, or
allocates, include its native interface or upstream test rather than assuming a
Python wrapper is the operative boundary.

### Prove the fix

Use base-fails/head-passes evidence. Run the same focused check against the
unmodified base and the candidate head, and include a positive control proving
that the fixture reaches the behavior and can distinguish them. A test that
passes on both sides is compatibility coverage, not proof of the fix.

Keep fixtures direct and minimal. Add roughly one focused test per stated
behavior at the seam being changed. Do not pin prose, exact advisory wording,
or documentation text with tests. Do not convert broad exception suppression
into evidence that the root cause is closed.

### Check downstream compatibility

For a public behavior change, identify affected downstream packages and run
representative base/head checks against their real public calls. Cover the
minimum supported and resolved dependency versions where relevant. Separate an
intentional, documented security behavior change from an accidental regression.

Put durable evidence in the pull request, upstream issue, advisory, test, or
project documentation as appropriate. Temporary agent logs and local scratch
files are supporting material, not the only record. Every completed security
change needs a durable residual-risk statement; unknowns and unverified claims
must remain explicit.

## 4. Secure development, dependencies, and CI/CD

Use the [NIST Secure Software Development Framework](https://csrc.nist.gov/Projects/ssdf)
as the high-level, risk-based reference: prepare the organization, protect the
software, produce well-secured software, and respond to vulnerabilities. Adapt
its outcomes to repository needs; do not turn every example into a mandatory
local checklist.

### Dependencies and supply chain

Review direct, transitive, build-time, test-time, and workflow dependency
changes. Use [GitHub dependency review](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-review)
where supported, and inspect advisory evidence at both the actual minimum
supported version and the resolved version. Check affected ranges, fixed
versions, transitive resolution, and whether the vulnerable operation is
reachable.

Prefer maintained dependencies, lock or constrain workflows appropriately, and
review action provenance. Do not claim protection from an advisory scanner
alone. Record follow-up when a floor, backport, or upstream release is needed.

### Workflow permissions, secrets, and untrusted contributions

Follow [GitHub's secure use reference](https://docs.github.com/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions).
Set workflow and job tokens to least privilege, normally read-only by default,
and elevate only the job that requires it. Pin or lock third-party workflow
dependencies using GitHub's recommended controls and review their source.

Protect environment secrets with required review where appropriate, prefer
short-lived scoped credentials such as OIDC when available, and keep sensitive
values out of workflow source, logs, artifacts, and diagnostics. Rotate exposed
secrets; redaction is not a substitute for rotation.

Never execute untrusted pull-request code, artifacts, or content with write
privileges or secrets. Treat `pull_request_target`, `workflow_run`, caches,
artifacts, and checkouts of fork code as trust boundaries. Avoid privileged
triggers unless required, and do not combine them with untrusted checkout.

Follow [GitHub's script-injection guidance](https://docs.github.com/en/actions/concepts/security/script-injections).
Do not interpolate attacker-controlled contexts into generated shell scripts.
Use an action argument or a quoted intermediate environment variable, and treat
titles, bodies, branch names, refs, labels, and similar fields as untrusted.

Reuse GitHub and OpenSSF guidance rather than inventing a local CI policy.
Review changes to reusable workflows and composite actions with the same care
as package code.

## 5. AI-agent execution discipline

Give the agent a case-specific brief with explicit authorization, affected
surface, demonstrated impact, upstream ownership, scope, non-goals, acceptance
commands, positive controls, and stop conditions. Keep private reports and
embargoed material inside authorized systems; sanitize public prompts and
publication text.

Require direct fixtures rather than generalized security harnesses and one
focused test per stated behavior. Forbid scope expansion into unrelated modules,
shared guard frameworks, new tooling, or speculative hardening without a new
maintainer decision.

Use independent review to challenge ownership, evidence, compatibility, and
confidentiality, with a hard cap of two review rounds after implementation.
Address concrete findings; do not repeat identical reviews to manufacture
consensus. No commits or pushes without explicit authorization. Follow the
canonical AI policy for proposal requirements, `Assisted-by: <tool>:<model>`
attribution, and the prohibition on AI `Co-authored-by:` trailers.

**Non-convergence stop rule:**

> When successive reviews keep discovering new implementation surfaces,
> simplify the policy, cut the branch, run a bounded implementation spike,
> or choose upstream/sandboxing instead of continuing the planning loop.

Stop and return to a maintainer when the acceptance criteria cannot distinguish
safe from unsafe behavior, evidence remains contradictory, or each fix exposes
another architectural surface.

## 6. Disclosure and residual risk

Follow the [OpenSSF coordinated vulnerability disclosure guide](https://oss-vulnerability-guide.openssf.org/)
and its maintainer process. Use the affected repository's private reporting
channel, not a public issue, for an undisclosed vulnerability.

1. Acknowledge receipt and identify a small response team and coordination owner.
2. Triage demonstrated impact, affected versions, intended behavior, and ownership.
3. Coordinate with the reporter, upstream projects, and affected downstream
   maintainers as needed; agree on communication and embargo expectations.
4. Develop and test privately when disclosure could increase user exposure.
5. Coordinate the fix, release, advisory, affected-version information, upgrade
   path, reporter credit, and CVE assignment where applicable.
6. Publish a sanitized account after coordination. Remove secrets, private
   data, undisclosed case details, and unnecessary exploit instructions while
   retaining actionable user guidance.

Every completed security change must include a residual-risk statement in a
durable location. State what remains unmitigated, who is affected, which
configurations or versions it concerns, available workarounds or isolation,
upstream dependencies, and the explicit revisit trigger. If there is no known
residual risk, say what evidence supports that conclusion and what was not
tested; do not claim absolute safety.

## 7. Post-release learning ritual

After release and disclosure, hold a time-boxed 30-minute review with the people
who owned the decision and evidence. Select at most three generalizable lessons.
Do not turn the review into a new implementation project.

For each lesson, ask whether it changes a future intake, ownership, minimum-fix,
verification, disclosure, or agent-execution decision. Update this playbook only
where future behavior would change; avoid adding narrative history or one-off
implementation details.

Add a public case study to [SECURITY-LESSONS.md](SECURITY-LESSONS.md) only when
its claims are independently verifiable. Create upstream watch items with an
explicit revisit trigger, such as a named release, merged API, published
advisory, or changed platform capability. Include an owner and the primary URL;
"monitor upstream" without a trigger is not a watch item.

## General references

- [NIST Secure Software Development Framework](https://csrc.nist.gov/Projects/ssdf)
- [OpenSSF coordinated vulnerability disclosure guide](https://oss-vulnerability-guide.openssf.org/)
- [GitHub Actions secure use reference](https://docs.github.com/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions)
- [GitHub Actions script injections](https://docs.github.com/en/actions/concepts/security/script-injections)
- [GitHub dependency review](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-review)

File and deserialization examples are catalogued separately in
[SECURITY-LESSONS.md](SECURITY-LESSONS.md); they illustrate decisions and do not
define the scope of this playbook.
