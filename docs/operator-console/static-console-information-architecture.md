# Static Console Information Architecture

## Content Hierarchy

1. Shell header with local read-only status.
2. Navigation rail with group and view controls.
3. Active view heading, status, and summary.
4. Section shortcut navigation.
5. Static panels for auth, sessions, modules, actions, evidence, safety, and
   local checks.
6. Safety footer with persistent no-go banners.

## Default Landing View

Overview remains the default landing view. It is the safest first viewport
because it summarizes read-only platform status before narrower module,
provider, action, auth, evidence, or safety journeys.

## Status Sections

Status sections use text, boolean values, badges, and blocker messages. Ready,
warning, blocked, and unavailable states are readable without relying only on
color.

## Blockers And Warnings

Blockers remain visible even when role filtering hides other read-only details.
The safety blocker view consolidates the static no-go conditions for review.

## Evidence Refs

Evidence refs remain local file references, demo JSON refs, or script names.
They do not link to external services or runtime provider calls.

## Command Cards

Command cards list only approved local read-only checks. The clipboard helper
does not store state and blocks commands outside the allowlist.

## Safety Footer

The footer keeps the persistent release-gate language: read-only, no
activation, no execution, no provider calls, no login, no credentials, no
external calls, no protected output, and no hidden private reasoning.
