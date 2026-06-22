# Generic Knowledge Intelligence Operator Review

## Review Goal

Operator review confirms that the Generic Knowledge Intelligence pack is a
safe metadata-only module package. Review approval may record future interest,
but it must not activate the module.

## Review Checklist

- Manifest key is `generic.knowledge_intelligence`.
- Package type is `module`.
- Version is `0.1.0-preview`.
- Capabilities are exactly:
  - `generic.knowledge.retrieve`
  - `generic.knowledge.summarize`
  - `generic.knowledge.ground`
  - `generic.knowledge.explain`
  - `generic.knowledge.answer`
- Declared routes are empty.
- Declared dependencies are empty.
- Capability bindings use `target_runtime=metadata_only`.
- Capability bindings set `controlled_supported=false`.
- Capability bindings set `dry_run_supported=true`.
- Sandbox requirement is declared for future runtime review.
- Conformance uses synthetic test vectors only.
- Readiness expects `activation_ready=false`.
- Activation request expects `activation_allowed=false`.
- Runtime registration preview expects `registration_allowed=false`.

## What To Approve

Approve only the metadata package as an example path through Brain gates.
Approval means:

- fixture shape is acceptable
- readiness evidence is understandable
- blockers are expected
- future activation requires a later architecture-approved task

## What Not To Approve

Do not approve:

- code loading
- package installation
- external calls
- route registration
- runtime registration
- capability activation
- controlled execution
- tool execution
- full autonomy
- raw secret access
- domain workflow behavior

## Safe Blocker Interpretation

Activation blockers are not demo failures. They are required v0.1 evidence.
The expected interpretation is:

- activation disabled: the module remains inactive
- runtime registration disabled: no runtime surface is created
- code loading disabled: no executable payload can run
- dynamic route registration disabled: no route is added

## Operator No-Go List

Stop the review if any fixture or doc asks to enable activation, code loading,
package installation, runtime registration, route registration, external
sources, external calls, tool execution, full autonomy, raw secret access, or
domain workflow logic.

## Future Activation Prerequisites

Future activation requires a separate task with architecture review, explicit
policy coverage, approval semantics, sandbox execution design, rollback and
disable paths, runtime adapter boundaries, conformance evidence, readiness
evidence, operator acceptance, and release discipline.
