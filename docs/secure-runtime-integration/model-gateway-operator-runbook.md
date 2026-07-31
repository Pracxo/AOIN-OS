# Model Gateway Operator Runbook

The AION-233 gateway is operator-invoked local simulation evidence only. Use
`scripts/model-gateway-local-simulation-run.py` with the repository-selected
Brain API Python interpreter when a local simulation fixture must be generated.
The runner is not installed as a package entry point, service, API route,
startup hook, scheduler, or worker.

Required operator constraints:

- Use `--authorization AION-232-SRI-0002`.
- Use absolute paths for the binding, manifests, request, temporary root, and
  output.
- Keep temporary input and output outside the repository.
- Keep the temporary root mode at `0700`.
- Keep input fixture permissions no broader than `0600`.
- Write only to a new output path and set output mode `0600`.
- Confirm with `RUN_CONTROLLED_MODEL_GATEWAY_SIMULATION`.

Do not provide credential, API-key, token, endpoint, network, tool, function,
connector, browser, module, shell, subprocess, persistence, production,
deployment, or model-training arguments. Remove temporary fixtures and output
after the pilot. Commit redacted evidence only.
