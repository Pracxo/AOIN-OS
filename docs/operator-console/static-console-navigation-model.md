# Static Console Navigation Model

## Navigation Groups

The static rail exposes these groups: Platform, Modules, Providers, Actions,
Auth and Sessions, Evidence, and Safety. The All group resets the rail to the
full static view list.

## View Membership

| Group | Views and panels |
| --- | --- |
| Platform | Overview, Readiness, Release Candidate |
| Modules | Module Lifecycle |
| Providers | Model Provider Hardening |
| Actions | Operator Actions, Action Authorization panel |
| Auth and Sessions | Local Auth, Role Access, Local Session, Auth Runtime panels |
| Evidence | Registry and Lifecycle, Audit and Provenance, command cards |
| Safety | Incidents, Settings Safety, forbidden descriptors, safety blocker view |

## Operator Journey

Operators start at Overview, scan readiness status, move to section shortcuts,
and inspect blockers before running local checks. The journey never exposes
write controls.

## Module Journey

Operators select Modules, open Module Lifecycle, and review lifecycle stages,
capability metadata, activation blockers, mock runtime records, and review
checklist output.

## Provider Journey

Operators select Providers and inspect model provider hardening state. Provider
calls remain absent, and provider enablement is not offered.

## Auth Session Journey

Operators select Auth and Sessions or use the Auth shortcut. The local auth,
role access, local session, and disabled auth runtime panels remain preview-only
and do not authenticate users.

## Evidence Journey

Operators select Evidence to inspect registry or provenance views and copy
approved local read-only check commands. Evidence commands do not change
runtime state.

## Safety Journey

Operators select Safety or use Show all safety blockers. The console renders
forbidden descriptors, hard-false safety flags, blockers, and warnings without
enabling the blocked operations.
