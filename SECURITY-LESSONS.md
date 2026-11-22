# HyperSpy ecosystem security lessons

This file indexes short, reusable lessons from publicly verifiable security
work. It separates general security references from illustrative file-I/O and
deserialization cases. The examples below are not the complete security scope;
use [SECURITY-PLAYBOOK.md](SECURITY-PLAYBOOK.md) for the full lifecycle.

Do not add private reports, unreleased advisories, undisclosed project cases, or
claims that cannot be checked in the cited primary sources. Re-read sources when
updating a lesson and record the review date and a specific revisit trigger.

## General security references

These references guide all ecosystem security work, not only file handling:

- [NIST Secure Software Development Framework](https://csrc.nist.gov/Projects/ssdf):
  risk-based secure-development outcomes and vulnerability response.
- [OpenSSF coordinated vulnerability disclosure guide](https://oss-vulnerability-guide.openssf.org/):
  private intake, triage, coordination, release, and disclosure.
- [GitHub Actions secure use reference](https://docs.github.com/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions):
  permissions, secrets, workflow dependencies, and untrusted code.
- [GitHub Actions script injections](https://docs.github.com/en/actions/concepts/security/script-injections):
  attacker-controlled contexts and safe script construction.
- [GitHub dependency review](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-review):
  dependency changes and known-vulnerability evidence in pull requests.

General references reviewed: 2026-11-22.

## Illustrative I/O and deserialization case index

| Case | Generalizable decision | Revisit trigger |
| --- | --- | --- |
| [NumPy `load`](#numpy-load-and-pickle) | Preserve safe deserialization defaults and the pickle trust boundary. | NumPy changes `load` defaults or pickle guidance. |
| [SymPy `sympify`](#sympy-sympify-and-expression-evaluation) | Do not treat expression evaluation as a safe parser for untrusted strings. | SymPy changes its evaluation or parsing security guidance. |
| [h5py#2891](#h5py2891-and-external-datasets) | Intentional external references and complex native parsing favor honest boundaries and isolation over partial downstream filters. | h5py or HDF5 provides a stable external-access policy control. |
| [HDFGroup/hdf5#6618](#hdfgrouphdf56618-and-runtime-policy) | Track runtime policy at the layer that performs external access; do not ship discussion proposals as available controls. | HDF5 publishes an accepted API, release, RFC, or revised decision. |

### NumPy `load` and pickle

- **Primary source:** [NumPy `load` API documentation](https://numpy.org/doc/stable/reference/generated/numpy.load.html).
- **Review date:** 2026-11-22.
- **Demonstrated impact:** Loading pickled object arrays can execute arbitrary
  code when the data is erroneous or maliciously constructed; the documentation
  explicitly identifies this risk.
- **Root cause:** Object-array loading uses Python pickle, which is a general
  object-deserialization mechanism rather than a safe numeric-array format.
- **Minimum effective disposition:** Preserve `allow_pickle=False`, including
  its documented default, for data from untrusted sources. Require an explicit
  trust decision before enabling pickle and prefer non-object array data.
- **Rejected alternatives and why:** Enabling pickle for untrusted input is
  rejected because the upstream warning says it can execute arbitrary code.
  Treating `allow_pickle=False` as a complete file-vulnerability or resource-
  exhaustion policy is also rejected because the documented control is specific
  to pickle and object arrays.
- **Verification evidence:** The current API page documents the default
  `allow_pickle=False`, the object-array failure when pickle is disallowed, and
  the warning to consider that setting for safer handling of untrusted sources.
- **Residual risk:** Other malformed-input, parser, memory, CPU, and file-access
  risks require their own demonstrated-impact and ownership analysis.
- **Revisit trigger:** A NumPy release changes the default, deserialization
  implementation, or security warning; update the affected guidance and tests.

### SymPy `sympify` and expression evaluation

- **Primary sources:** [SymPy basic operations tutorial](https://docs.sympy.org/latest/tutorials/intro-tutorial/basic_operations.html)
  and [`sympify` API documentation](https://docs.sympy.org/latest/modules/core.html#sympy.core.sympify.sympify).
- **Review date:** 2026-11-22.
- **Demonstrated impact:** Supplying an unsanitized string to an evaluator can
  cross from data processing into Python expression evaluation.
- **Root cause:** The `sympify` API documentation states that the function uses
  `eval`; it therefore must not be used on unsanitized input.
- **Minimum effective disposition:** Do not pass untrusted serialized strings to
  `sympify`. Keep the trust boundary explicit and use a constrained, structured
  representation chosen for the actual input requirement instead of evaluation.
- **Rejected alternatives and why:** Treating `sympify` as a safe general parser
  is rejected by its own warning. Assuming a downstream wrapper sanitizes input
  without a demonstrated, tested grammar is likewise not an effective boundary.
- **Verification evidence:** The tutorial documents string-to-expression
  conversion, while the linked API documentation carries the explicit `eval`
  and unsanitized-input warning. The two claims are cited separately.
- **Residual risk:** Application-specific expression features still need a
  defined grammar and threat model; avoiding one evaluator does not make every
  alternative parser safe or bounded.
- **Revisit trigger:** SymPy changes the `sympify` implementation or warning,
  or publishes a parser with an explicit untrusted-input security contract.

### h5py#2891 and external datasets

- **Primary sources:** [h5py issue #2891](https://github.com/h5py/h5py/issues/2891)
  and the maintainer's [sandbox recommendation](https://github.com/h5py/h5py/issues/2891#issuecomment-5327437568).
- **Review date:** 2026-11-22.
- **Demonstrated impact:** An application that reads attacker-controlled HDF5
  external datasets can access files with its own privileges and may expose the
  resulting data. Impact depends on the application's behavior and deployment.
- **Root cause:** HDF5 intentionally supports external datasets and other
  external-reference mechanisms that regular dataset reads can follow.
- **Minimum effective disposition:** Make the untrusted-file boundary explicit
  and use genuine sandboxing for properly untrusted HDF5. Follow upstream HDF5
  policy work rather than presenting h5py as the enforcement layer.
- **Rejected alternatives and why:** Checking only external datasets misses
  other mechanisms discussed by maintainers. Adding broad security enforcement
  in h5py was rejected or strongly questioned because the behavior belongs to
  HDF5 and partial application checks are laborious and incomplete.
- **Verification evidence:** Maintainers describe external datasets as an
  intentional documented feature, identify additional external-reference
  routes, recommend sandboxing untrusted HDF5, and redirect policy discussion
  to HDFGroup/hdf5#6618. The issue was closed after that discussion.
- **Residual risk:** HDF5 has a complex native parser and several external-file
  mechanisms. Documentation alone does not isolate file access, plugins, native
  defects, or resource consumption.
- **Revisit trigger:** h5py or HDF5 publishes a stable, documented control for
  external references or changes its sandboxing recommendation.

### HDFGroup/hdf5#6618 and runtime policy

- **Primary source:** [HDFGroup/hdf5 issue #6618](https://github.com/HDFGroup/hdf5/issues/6618).
- **Review date:** 2026-11-22.
- **Demonstrated impact:** Transparent external references can make a data read
  access another file; downstream applications need a reliable way to express
  their external-access policy when handling untrusted HDF5.
- **Root cause:** External datasets, virtual datasets, external links, and
  possibly other drivers cross file boundaries at the native HDF5 layer.
- **Minimum effective disposition:** Track and contribute evidence to the
  upstream runtime-policy discussion. Until a released control exists, retain
  honest trust-boundary documentation and deployment isolation rather than a
  speculative downstream policy framework.
- **Rejected alternatives and why:** Treating a prefix as a complete restriction
  is questioned in the discussion because symlinks and other paths need care.
  Treating a pre-flight audit as a replacement for runtime checks is also
  questioned because a separate audit does not enforce policy when the file is
  opened.
- **Verification evidence:** The public issue requests switches for external
  access. Maintainers and contributors discuss policy profiles, callbacks,
  direct controls, and an RFC; these are proposals in an open discussion, not
  verified stable HDF5 APIs at the review date.
- **Residual risk:** No final upstream design or availability is established by
  this issue. Proposed names and examples must not be used as implementation
  instructions or represented as current protections.
- **Revisit trigger:** HDF5 publishes an RFC, accepted design, released runtime
  control, or a revised decision; then assess the actual released API and its
  minimum supported version.

## Case-study template

Use this template only for a public, independently verifiable case. Delete the
instructional sentence after copying, but retain every field.

### <Public project and issue, advisory, or change>

- **Primary sources:** <documentation, source, advisory, issue, and release URLs>
- **Review date:** <YYYY-MM-DD>
- **Demonstrated impact:** <affected user, actor, trust boundary, configuration,
  and observed confidentiality, integrity, availability, or auditability effect>
- **Root cause:** <the operation and layer that actually produce the behavior>
- **Minimum effective disposition:** <smallest effective upstream, package,
  dependency, documentation, runtime-policy, or isolation outcome>
- **Rejected alternatives and why:** <alternatives considered, with evidence and
  maintenance or compatibility reasons rather than preference alone>
- **Verification evidence:** <real public surface, exact versions, base-fails/
  head-passes result, positive controls, native-layer and downstream checks>
- **Residual risk:** <remaining exposure, limitations, untested claims, and
  workarounds or isolation>
- **Revisit trigger:** <named upstream release, merged API, advisory, platform
  change, or other observable event that requires reassessment>
