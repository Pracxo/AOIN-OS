# Post-v0.1 UI No-Go Conditions

The following conditions block static console release and future UI work:

- frontend dependency added without approval
- write HTTP method added
- activation button added
- execute button added
- provider call button added
- login form added before auth release gate
- credential field added
- token storage added
- cookie storage added
- session storage added
- protected prompt displayed
- hidden reasoning displayed
- external URL called
- production-ready UI claim added

Any one condition requires stopping the UI release and restoring the static
checkpoint to a local, read-only, dependency-free state.
