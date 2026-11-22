# Contributing to HyperSpy projects

If you want to contribute to a repository of the HyperSpy organisation, please read the [HyperSpy developer guide](https://hyperspy.readthedocs.io/en/latest/dev_guide/intro.html), and the repository's own CONTRIBUTING file when it has one.

## Security Work

Use the [ecosystem security-work playbook](SECURITY-PLAYBOOK.md) to assess impact,
ownership, minimum fixes, evidence, dependencies, CI/CD, disclosure, and residual
risk. The [security agent brief](SECURITY-AGENT-BRIEF.md) bounds AI-assisted tasks,
and the [public lessons index](SECURITY-LESSONS.md) records reusable, verifiable
case studies. Report undisclosed vulnerabilities through the affected repository's
private security reporting channel rather than a public issue.

## AI-Assisted Contributions

Non-trivial AI-assisted changes require an accepted proposal in [hyperspy/hyperspy-proposals](https://github.com/hyperspy/hyperspy-proposals) before the implementation PR will be reviewed. Trivial AI-assisted changes do not require a proposal.

For more details, see the [proposal process](https://github.com/hyperspy/hyperspy-proposals#how-to-submit-a-proposal).

All AI-assisted commits must include the `Assisted-by: <tool>:<model>` trailer.

The normative rules and the shared enforcement tooling (pre-commit hooks and the reusable compliance workflow) live in [AI-POLICY.md](AI-POLICY.md).
