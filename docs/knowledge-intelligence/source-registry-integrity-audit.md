# Source Registry Integrity Audit

The AION-207 integrity audit validates append-only registry snapshots without mutating them.

Audit checks include:

- sequence starts at one
- no sequence gaps or duplicates
- previous-record fingerprint chain
- record fingerprint
- payload fingerprint
- unique record IDs
- supersession references
- supersession cycle detection
- source snapshot references
- envelope and metadata budgets
- no source body
- no claim verification
- no knowledge promotion
- no belief creation or mutation
- no persistent write
- no runtime effect

Integrity findings are redacted. They contain only safe IDs, registered reason codes, severity, and bounded summaries. Findings do not include source content, raw URLs, exception text, prompts, credentials, tokens, personal data, diffs, paths, or executable commands.
