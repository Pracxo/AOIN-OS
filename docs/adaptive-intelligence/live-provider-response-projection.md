# AION-248 Response Projection

Provider responses are treated as transient untrusted candidate reasoning. The runner extracts bounded text only long enough to validate the local scenario and calculate safe fingerprints.

The committed response projection includes scenario code, request fingerprint, response fingerprint, provider response model ID, HTTP status, provider status, byte counts, token counts, latency and validation result. It excludes raw text, raw provider IDs, raw headers and provider error messages.
