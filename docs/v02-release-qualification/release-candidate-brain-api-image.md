# AION-243 Brain API Candidate Image

The Brain API candidate image is built locally from the frozen AION-241 base
image and the `aion-brain-api` `0.2.0rc1` wheel.

The generated Dockerfile is temporary, outside the repository, and uses
`python -m pip install --no-index --no-deps --force-reinstall`. Docker builds
use `--pull=false`, `--network=none`, `--provenance=false` and `--sbom=false`.

The retained image tag is `aoinos-brain-api:aion-v0.2.0-rc.1`. The OCI archive
is retained in the candidate bundle. No registry login, pull or push is allowed.
