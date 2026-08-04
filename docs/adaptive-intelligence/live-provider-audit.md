# AION-248 Audit

The pilot records an in-memory audit chain for authorization, projection, response validation, replay and cleanup evidence. Audit records retain event type, outcome, subject fingerprint, previous audit fingerprint and timestamp.

Audit evidence does not contain prompt text, response text, credentials, authorization headers or provider response IDs.
