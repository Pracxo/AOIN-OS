# AION-243 Release-Candidate Contracts

The public contract is `aion_brain.contracts.v02_release_candidate`.

It defines the authorization envelope, component binding, session, source
snapshot, version manifest, artifact plan, artifact manifest, SBOM, provenance,
checksums, qualification signatures, reproducibility, compatibility, migration,
retention, integrity and evidence bundle records.

All models forbid extra fields, hide input in errors and use immutable records.
The validation layer rejects protected evidence values, absolute paths, parent
traversal, non-UTC timestamps, non-SHA fingerprints and publication or
production claims.
