# Prompt Egress Guard

Prompt egress preview converts prompt packet metadata and model input manifest
references into a redacted local preview. It is designed to prove what would be
checked before provider transmission without transmitting prompt content.

The guard blocks or warns on:

- prompt body fields
- hidden reasoning fields
- secret-like fields or values
- tool intent leakage
- untrusted retrieved context marked as trusted
- external model calls being enabled

The persisted preview stores redacted summaries only. It records
`egress_allowed=false` and `external_call_allowed=false` in AION-086.

