# Role-Aware Console Preview

The static Operator Console includes a demo-only role switcher for `viewer`, `operator`, `reviewer`, `admin`, and `auditor`.

The switcher loads bundled JSON from `operator-console-static/demo-data`. It does not authenticate users, does not persist browser state, and does not call external services.

The panel shows visible views, removed sections, removed actions, forbidden-action visibility, and the safety flags that remain false: `write_allowed`, `execute_allowed`, `activation_allowed`, and `external_calls_allowed`.

`system_service` is intentionally absent from the switcher because it is an internal role, not a UI role.
