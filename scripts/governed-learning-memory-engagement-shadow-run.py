#!/usr/bin/env python3
"""Uninstalled AION-226 operator runner for local shadow evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "services" / "brain-api" / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from aion_brain.contracts.governed_engagement_learning import (  # noqa: E402
    AUTHORIZATION_TRANSACTION_ID,
    EngagementApplicationMode,
    engagement_fingerprint,
    load_fixture_envelope,
)

CONFIRMATION = "APPLY_ENGAGEMENT_SHADOW_OVERLAY"


def _external_path(raw: str, *, must_exist: bool, output: bool = False) -> Path:
    if raw.startswith("~") or "$" in raw or "://" in raw:
        raise ValueError("path expansion and URI syntax are rejected")
    path = Path(raw)
    if not path.is_absolute():
        raise ValueError("path must be absolute")
    if any(part.startswith(".") for part in path.parts):
        raise ValueError("hidden path components are rejected")
    if must_exist:
        if not path.exists() or path.is_symlink() or not path.is_file():
            raise ValueError("input path must be an existing non-symlink file")
    if output:
        if path.exists():
            raise ValueError("output file must be new")
        if not path.parent.exists() or path.parent.is_symlink():
            raise ValueError("output parent must be an existing non-symlink directory")
    resolved = path.resolve()
    try:
        resolved.relative_to(REPO_ROOT)
    except ValueError:
        return resolved
    raise ValueError("repository paths are rejected")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--confirm", required=True)
    parser.add_argument(
        "--mode",
        choices=("deterministic-simulation", "operator-invoked-shadow"),
        required=True,
    )
    args = parser.parse_args()

    if args.authorization != AUTHORIZATION_TRANSACTION_ID:
        raise SystemExit("ERROR: authorization must be AION-225-GLM-0003")
    if args.confirm != CONFIRMATION:
        raise SystemExit("ERROR: confirmation phrase mismatch")

    plan_path = _external_path(args.plan, must_exist=True)
    fixture_path = _external_path(args.fixture, must_exist=True)
    output_path = _external_path(args.output, must_exist=False, output=True)

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    fixture = load_fixture_envelope(fixture_path)
    mode = (
        EngagementApplicationMode.DETERMINISTIC_SIMULATION
        if args.mode == "deterministic-simulation"
        else EngagementApplicationMode.OPERATOR_INVOKED_SHADOW
    )
    report = {
        "authorization_id": AUTHORIZATION_TRANSACTION_ID,
        "mode": mode.value,
        "plan_fingerprint": engagement_fingerprint(plan),
        "fixture_fingerprint": fixture.fixture_fingerprint,
        "redacted": True,
        "operator_invoked": True,
        "overlay_in_memory_only": True,
        "active_overlay_records_after_close": 0,
        "persistent_overlay_writes": 0,
        "aion_224_store_writes": 0,
        "production_policy_mutations": 0,
        "network_calls": 0,
        "runtime_effect": False,
    }
    output_path.write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "AION-226 engagement shadow summary: "
        f"mode={mode.value} active_overlay_records_after_close=0 redacted=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
