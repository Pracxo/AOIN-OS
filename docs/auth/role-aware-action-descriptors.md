# Role-Aware Action Descriptors

Operator Console actions remain descriptors. They describe possible local review flows but do not execute.

`viewer` can inspect read-only descriptors. `operator` can see dry-run request descriptors. `reviewer` can see review-record descriptors. `auditor` can inspect redacted reports. `admin` can inspect local settings safety without enabling privileged behavior.

Forbidden descriptors such as activation, code loading, external calls, tool execution, policy bypass, and hard delete remain visible. They are never converted into enabled controls.
