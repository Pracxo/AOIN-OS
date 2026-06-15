#!/usr/bin/env bash
set -euo pipefail

if docker compose version >/dev/null 2>&1; then
  docker compose up --build brain-api postgres redis nats opa
else
  docker-compose up --build brain-api postgres redis nats opa
fi
