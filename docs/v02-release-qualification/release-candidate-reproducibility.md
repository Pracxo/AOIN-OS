# AION-243 Reproducibility

AION-243 records reproducibility honestly.

Required deterministic comparisons are enforced for the source archive, SDK
wheel, SDK source distribution and Operator Console bundle. Brain API candidate
image evidence records normalized invariants, including source commit,
source-tree fingerprint, base image, wheel fingerprint, Dockerfile fingerprint,
build-context fingerprint, package version and runtime command.

Byte-for-byte OCI reproducibility is recorded as the actual result and is not
forced true.
