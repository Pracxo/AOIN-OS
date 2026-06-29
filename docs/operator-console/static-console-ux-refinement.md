# Static Console UX Refinement

## Purpose

AION-103 refines the static local Operator Console so operators can scan the
existing read-only panels with less effort. The work improves navigation,
readability, keyboard access, and local evidence discovery without adding a UI
framework or runtime capability.

## What Changed

- Added top-level navigation groups for Platform, Modules, Providers, Actions,
  Auth and Sessions, Evidence, and Safety.
- Added a skip link and focus targets for keyboard users.
- Added section shortcuts for the main static panels.
- Added a safety blocker view that renders blocked descriptors and no-go
  conditions together.
- Replaced the local command block with command cards that can copy only
  approved local verification commands.
- Improved spacing, contrast, focus states, responsive behavior, and status
  presentation in the static CSS.

## What Stayed Forbidden

The console remains local, static, and read-only. It still has no production
auth, no auth runtime, no login or logout behavior, no credential controls, no
token or cookie issuance, no persisted sessions, no provider calls, no writes,
no activation, no execution, no runtime registration, no code loading, and no
external calls.

## Navigation Groups

The static navigation model groups views by operator intent:

- Platform: overview, readiness, and release candidate state.
- Modules: module lifecycle trail.
- Providers: provider hardening view.
- Actions: governed operator action preview.
- Auth and Sessions: local auth, role, local session, and disabled auth panels.
- Evidence: registry, lifecycle, audit, provenance, and command cards.
- Safety: incidents, settings safety, forbidden descriptors, and blocker view.

## Readability Improvements

Panels keep tighter headings, consistent spacing, stable cards, and shorter
section jump targets. Status values include text labels and border treatment so
the UI does not rely on color alone.

## Accessibility Improvements

The page has a skip link, keyboard-safe buttons, visible focus indicators,
heading structure for the rail and panel content, aria labels for navigation,
and responsive layouts that keep controls usable on narrow screens.

## Safety Banner Requirements

The static page must keep visible banners for read-only, no activation, no
execution, no provider calls, no login, and no credentials. These banners remain
release blockers in `./scripts/static-console-ux-check.sh` and
`./scripts/static-console-safety-check.sh`.

## Local-Only Command Copy Rules

Copy support is allowed only for these local read-only commands:

- `./scripts/ui-release-gate.sh`
- `./scripts/static-console-safety-check.sh`
- `./scripts/operator-platform-regression.sh`
- `./scripts/operator-platform-freeze-gate.sh`
- `./scripts/docs-check.sh`

Any command that activates modules, executes tools, enables providers, starts
production auth, or stores protected material is forbidden.

## No-Go Conditions

AION-103 fails if it adds frontend dependencies, package files, lockfiles, build
tooling, external URLs, API routes, SDK or CLI commands, migrations, production
auth, write controls, activation controls, execution controls, provider-call
controls, login controls, credential inputs, token or cookie storage, session
persistence, or a production UI claim.
