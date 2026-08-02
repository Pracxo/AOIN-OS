# AION-243 Qualification Signatures

AION-243 uses one ephemeral Ed25519 qualification keypair for detached
signatures. The private key is memory-only and is never written, logged,
committed or retained.

The retained public key record is qualification-only and not a production
signing key. Detached signatures cover the candidate content manifest,
checksum manifest, provenance, SBOM and bundle manifest.
