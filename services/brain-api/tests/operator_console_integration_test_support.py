from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
OPERATOR_AUTH_PATH = (
    "examples/secure-runtime-integration/"
    "operator-console-integration-authorization.json"
)


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def operator_auth():
    return load_json(OPERATOR_AUTH_PATH)


def program_ledger():
    return load_json("docs/secure-runtime-integration/program-ledger.json")


def authorization_ledger():
    return load_json("docs/secure-runtime-integration/authorization-ledger.json")
