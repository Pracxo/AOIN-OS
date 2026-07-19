# Shadow-Mode No-Go Regression Rules

AION-177 no-go checks must fail on:

- `.github/workflows/` changes.
- `services/brain-api/src/aion_brain/` runtime-source changes.
- `packages/aion-sdk-python/src/` changes.
- `services/brain-api/pyproject.toml` changes.
- `migrations/` changes.
- AION-178 shadow-mode source files appearing before AION-178.
- Runtime enablement flags becoming true.
- Git, branch, pull request, merge, deployment, provider, connector, network,
  model-training, approval-creation, self-approval, or protected-core bypass
  becoming enabled.
- v0.2 tag or release creation.
- `aion-v0.1.0` tag movement.

The checks must not skip or xfail safety assertions.
