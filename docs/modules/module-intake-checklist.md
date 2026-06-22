# Module Intake Checklist

Use this checklist before a module can move from manifest review to later
activation design.

- [ ] manifest is valid
- [ ] no executable payload
- [ ] no external dependency download
- [ ] no full autonomy request
- [ ] no raw secret access request
- [ ] no dynamic route registration
- [ ] no policy escalation
- [ ] declared contracts exist
- [ ] declared settings exist
- [ ] sandbox requirement declared
- [ ] capability binding validates
- [ ] conformance passes
- [ ] readiness assessment created
- [ ] activation_ready=false
- [ ] operator review recorded
- [ ] audit/provenance present
- [ ] release/freeze gates remain green

Activation remains disabled until a future activation gate exists.

Code loading remains disabled for all metadata examples and intake records.

Modules must not modify Brain core.
