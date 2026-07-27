#!/usr/bin/env python3
"""Uninstalled AION-219 public research pilot operator runner."""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "services" / "brain-api" / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def _ensure_brain_python() -> None:
    if os.environ.get("AION_PUBLIC_RESEARCH_PILOT_RUNNER_REEXEC") == "1":
        return
    try:
        import pydantic  # noqa: F401
    except ModuleNotFoundError:
        brain_python = REPO_ROOT / "services" / "brain-api" / ".venv" / "bin" / "python"
        if not brain_python.is_file():
            raise
        env = {
            **os.environ,
            "AION_PUBLIC_RESEARCH_PILOT_RUNNER_REEXEC": "1",
        }
        os.execve(str(brain_python), [str(brain_python), *sys.argv], env)


_ensure_brain_python()

from aion_brain.contracts.knowledge_public_research_pilot import (  # noqa: E402
    AUTHORIZATION_TRANSACTION_ID,
    LIVE_CONFIRMATION_TEXT,
    PublicResearchPilotAuthorizationEnvelope,
    PublicResearchPilotMode,
    PublicResearchPilotPlan,
    build_public_research_authorization_envelope,
    deterministic_json_bytes,
    public_research_fingerprint,
    reject_prohibited_text,
)
from aion_brain.knowledge_intelligence.public_research_dns import (  # noqa: E402
    InMemoryPublicResearchDnsBackend,
    SystemPublicResearchDnsBackend,
)
from aion_brain.knowledge_intelligence.public_research_http_transport import (  # noqa: E402
    InMemoryHttpsFixture,
    InMemoryPinnedHttpsBackend,
    SystemPinnedHttpsBackend,
)
from aion_brain.knowledge_intelligence.public_research_pilot import (  # noqa: E402
    ControlledPublicResearchPilot,
)
from aion_brain.knowledge_intelligence.public_research_policy import (  # noqa: E402
    canonicalize_public_research_url,
    robots_url_for_source,
)
from aion_brain.knowledge_intelligence.public_research_session import (  # noqa: E402
    PublicResearchPilotKillSwitch,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--confirm", required=True)
    parser.add_argument(
        "--mode",
        choices=("deterministic-simulation", "operator-invoked-live"),
        required=True,
    )
    parser.add_argument("--kill-after-step", choices=("before-run",), default=None)
    args = parser.parse_args()

    if args.authorization != AUTHORIZATION_TRANSACTION_ID:
        raise SystemExit("ERROR: authorization mismatch")
    if args.confirm != LIVE_CONFIRMATION_TEXT:
        raise SystemExit("ERROR: confirmation mismatch")

    plan_path = _absolute_existing_path(args.plan, label="plan")
    output_path = _absolute_output_path(args.output)
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    reject_prohibited_text(json.dumps(payload, sort_keys=True), "pilot plan envelope")
    plans = _load_plans(payload)
    mode = (
        PublicResearchPilotMode.OPERATOR_INVOKED_LIVE
        if args.mode == "operator-invoked-live"
        else PublicResearchPilotMode.DETERMINISTIC_SIMULATION
    )
    if any(plan.mode is not mode for plan in plans):
        raise SystemExit("ERROR: plan mode mismatch")

    now = datetime.now(UTC)
    envelope = _load_or_build_envelope(payload, plans=plans, mode=mode, now=now)
    kill_switch = PublicResearchPilotKillSwitch()
    _bind_signal_handlers(kill_switch)
    if args.kill_after_step == "before-run":
        kill_switch.trigger("operator_test_kill_before_run")

    if mode is PublicResearchPilotMode.OPERATOR_INVOKED_LIVE:
        pilot = ControlledPublicResearchPilot(
            dns_backend=SystemPublicResearchDnsBackend(),
            connection_backend=SystemPinnedHttpsBackend(),
        )
    else:
        dns_backend, connection_backend = _simulation_backends(plans, now=now)
        pilot = ControlledPublicResearchPilot(
            dns_backend=dns_backend,
            connection_backend=connection_backend,
            clock=lambda: now,
        )

    result = pilot.run(envelope=envelope, plans=plans, kill_switch=kill_switch)
    report = result.model_dump(mode="json")
    report["report_fingerprint"] = public_research_fingerprint(report)
    report["source_body_absent"] = _source_body_absent(report)
    report_bytes = deterministic_json_bytes(report)
    if len(report_bytes) > plans[0].resource_budget.maximum_pilot_report_bytes:
        raise SystemExit("ERROR: pilot report exceeds authorized report budget")
    output_path.write_bytes(report_bytes)
    print(
        "public research pilot completed "
        f"status={result.status.value} "
        f"requests={result.session.public_https_request_count} "
        f"dns={result.session.dns_resolution_count} "
        f"external_read={result.external_read_performed} "
        f"report={output_path}"
    )
    return 0


def _absolute_existing_path(raw_path: str, *, label: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        raise SystemExit(f"ERROR: {label} path must be absolute")
    resolved = path.resolve()
    if not resolved.is_file():
        raise SystemExit(f"ERROR: {label} path does not exist")
    return resolved


def _absolute_output_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        raise SystemExit("ERROR: output path must be absolute")
    resolved = path.resolve()
    if resolved.exists():
        raise SystemExit("ERROR: output path already exists")
    if resolved.is_relative_to(REPO_ROOT):
        raise SystemExit("ERROR: output path must be outside repository")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def _load_plans(payload: Any) -> tuple[PublicResearchPilotPlan, ...]:
    if isinstance(payload, dict) and "plans" in payload:
        raw_plans = payload["plans"]
    elif isinstance(payload, dict) and "plan" in payload:
        raw_plans = [payload["plan"]]
    else:
        raw_plans = [payload]
    if not isinstance(raw_plans, list) or not raw_plans:
        raise SystemExit("ERROR: plan payload must contain at least one plan")
    return tuple(PublicResearchPilotPlan.model_validate(item) for item in raw_plans)


def _load_or_build_envelope(
    payload: Any,
    *,
    plans: tuple[PublicResearchPilotPlan, ...],
    mode: PublicResearchPilotMode,
    now: datetime,
) -> PublicResearchPilotAuthorizationEnvelope:
    if isinstance(payload, dict) and "authorization_envelope" in payload:
        return PublicResearchPilotAuthorizationEnvelope.model_validate(
            payload["authorization_envelope"]
        )
    session_id = (
        str(payload.get("pilot_session_id"))
        if isinstance(payload, dict) and payload.get("pilot_session_id")
        else "aion-219-public-research-pilot"
    )
    operator_fingerprint = (
        str(payload.get("operator_identity_fingerprint"))
        if isinstance(payload, dict) and payload.get("operator_identity_fingerprint")
        else public_research_fingerprint({"operator": "aion-219-runner"})
    )
    return build_public_research_authorization_envelope(
        pilot_session_id=session_id,
        plan_ids=tuple(sorted(plan.pilot_plan_id for plan in plans)),
        operator_identity_fingerprint=operator_fingerprint,
        live_network_access_approved=mode is PublicResearchPilotMode.OPERATOR_INVOKED_LIVE,
        created_at=now,
        expires_at=now + timedelta(minutes=30),
    )


def _simulation_backends(
    plans: tuple[PublicResearchPilotPlan, ...],
    *,
    now: datetime,
) -> tuple[InMemoryPublicResearchDnsBackend, InMemoryPinnedHttpsBackend]:
    host_addresses: dict[str, tuple[str, ...]] = {}
    fixtures: dict[tuple[str, str], InMemoryHttpsFixture] = {}
    for plan in plans:
        for candidate in plan.explicit_source_candidates:
            canonical_url = canonicalize_public_research_url(candidate.original_url)
            host = candidate.domain
            host_addresses[host] = ("93.184.216.34",)
            robots_url = robots_url_for_source(canonical_url)
            fixtures[("GET", robots_url)] = InMemoryHttpsFixture(
                method="GET",
                url=robots_url,
                body=b"User-agent: *\nAllow: /\n",
            )
            fixtures[(candidate.method, canonical_url)] = InMemoryHttpsFixture(
                method=candidate.method,
                url=canonical_url,
                body=(
                    b"Deterministic AION-219 public research pilot fixture body. "
                    b"Operator review remains required."
                ),
                peer_address="93.184.216.34",
            )
    return (
        InMemoryPublicResearchDnsBackend(host_addresses, resolved_at=now),
        InMemoryPinnedHttpsBackend(fixtures, completed_at=now),
    )


def _bind_signal_handlers(kill_switch: PublicResearchPilotKillSwitch) -> None:
    def trigger(_signal_number: int, _frame: object) -> None:
        kill_switch.trigger("operator_signal")

    signal.signal(signal.SIGINT, trigger)
    signal.signal(signal.SIGTERM, trigger)


def _source_body_absent(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"body", "source_body", "content_bytes", "body_utf8", "raw_body"}:
                return False
            if not _source_body_absent(item):
                return False
        return True
    if isinstance(value, list | tuple):
        return all(_source_body_absent(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        return "deterministic aion-219 public research pilot fixture body" not in lowered
    return True


if __name__ == "__main__":
    raise SystemExit(main())
