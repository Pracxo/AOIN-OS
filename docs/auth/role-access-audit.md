# Role Access Audit

AION-096 adds a role access audit for the local role matrix. The audit checks all local roles across console views and records decisions for read, dry-run descriptor, review descriptor, and forbidden descriptor visibility.

The audit passes only when forbidden actions remain visible, redaction is applied, and write, execution, activation, and external-call grants are absent.

The audit is local-only and read-only. It does not create sessions, store credentials, issue tokens, issue cookies, or call external services.
