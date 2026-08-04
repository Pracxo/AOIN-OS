# AION-248 Credential Boundary

The live pilot reads one credential source only: `OPENAI_API_KEY` from the runner process environment. The key is read inside the runner, removed from that process environment after read, used only to create transient authorization headers, and never passed into installed package APIs.

Credential files, CLI credential arguments, credential fingerprints, credential persistence, token persistence, logging and committed credential evidence are prohibited.
