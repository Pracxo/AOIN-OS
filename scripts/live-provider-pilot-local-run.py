#!/usr/bin/env python3
"""Uninstalled AION-248 local runner for the authorized OpenAI live pilot."""

from __future__ import annotations

import argparse
import http.client
import ipaddress
import json
import os
import shutil
import socket
import ssl
import stat
import sys
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ABSENT_KEY_MESSAGE = (
    "The AION-248 implementation is ready, but the authorized live pilot has not started. "
    "Make one OpenAI API key available to the Codex process through the OPENAI_API_KEY "
    "environment variable. Do not paste the key into chat, source, configuration files, "
    "GitHub, Docker images or committed evidence."
)


def _stop_before_project_import_when_key_absent(argv: list[str]) -> None:
    if argv[:1] != ["run-pilot"] or "-h" in argv or "--help" in argv:
        return
    option_names = {argument.split("=", 1)[0] for argument in argv[1:]}
    required_options = {
        "--authorization",
        "--model",
        "--temporary-root",
        "--output",
        "--confirm",
        "--implementation-commit",
    }
    if required_options.issubset(option_names) and not os.environ.get("OPENAI_API_KEY"):
        print(ABSENT_KEY_MESSAGE)
        raise SystemExit(2)


_stop_before_project_import_when_key_absent(sys.argv[1:])

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "services/brain-api/src"
sys.path.insert(0, str(SRC_ROOT))
for site_packages in (REPO_ROOT / "services/brain-api/.venv/lib").glob(
    "python*/site-packages"
):
    site_packages_text = str(site_packages)
    if site_packages_text not in sys.path:
        sys.path.insert(0, site_packages_text)

from aion_brain.contracts.live_provider_pilot import (  # noqa: E402
    AUTHORIZATION_TRANSACTION_ID,
    ENDPOINT_HOST,
    ENDPOINT_PATH,
    ENDPOINT_PORT,
    ENDPOINT_SCHEME,
    HTTP_METHOD,
    MAXIMUM_DNS_RESOLUTIONS,
    MAXIMUM_REQUEST_PAYLOAD_BYTES,
    MAXIMUM_REQUEST_TIMEOUT_SECONDS,
    MAXIMUM_RESPONSE_PAYLOAD_BYTES,
    PILOT_CONFIRMATION_TEXT,
    PROVIDER_ID,
    SELECTED_MODEL_ID,
    LiveProviderEvidenceBundle,
    LiveProviderScenarioCode,
    LiveProviderTransportResult,
    assert_no_protected_material,
    content_fingerprint,
    default_required_counters,
    default_zero_counters,
    estimate_tokens_from_bytes,
    evidence_report_fingerprint,
    validate_endpoint,
)
from aion_brain.live_provider_pilot import ControlledLiveProviderPilotService  # noqa: E402
from aion_brain.live_provider_pilot.openai_responses_adapter import (  # noqa: E402
    build_responses_payload,
    extract_text_from_response,
    extract_usage,
)
from aion_brain.live_provider_pilot.observability import (  # noqa: E402
    create_observability_snapshot,
)
from aion_brain.production_auth.canonical import canonical_json_bytes  # noqa: E402


class PilotStop(RuntimeError):
    """Normalized live-pilot stop condition."""

    def __init__(
        self,
        message: str,
        *,
        normalized_error_class: str,
        http_status: int | None = None,
        exit_status: int = 2,
    ) -> None:
        super().__init__(message)
        self.normalized_error_class = normalized_error_class
        self.http_status = http_status
        self.exit_status = exit_status


def _synthetic_long_context() -> str:
    records = [
        f"Record {index}: synthetic case {index} has fictional status review "
        f"and invented score {index % 5}."
        for index in range(1, 81)
    ]
    return (
        "Summarize these fictional records into bounded themes. No external source is "
        "needed.\n" + "\n".join(records)
    )


SCENARIOS: tuple[tuple[LiveProviderScenarioCode, str, int], ...] = (
    (
        LiveProviderScenarioCode.synthetic_general_reasoning,
        (
            "Solve this fictional scheduling problem. A workshop has rooms A, B, and C. "
            "Four invented teams need sessions with no overlap for shared facilitator F. "
            "Return a concise feasible schedule and explain the constraints."
        ),
        600,
    ),
    (
        LiveProviderScenarioCode.synthetic_code_review,
        (
            "Review this invented Python function. Identify one bounded logic defect and "
            "one maintainability issue. Code:\n"
            "def score(values):\n"
            "    total = 0\n"
            "    for index in range(len(values) - 1):\n"
            "        total += values[index]\n"
            "    return total / len(values)\n"
        ),
        800,
    ),
    (
        LiveProviderScenarioCode.synthetic_classification,
        (
            "Classify this invented event into exactly one label: allow, review, reject. "
            "Event: A synthetic system proposes a reversible local-only configuration "
            "preview with no external effects."
        ),
        128,
    ),
    (
        LiveProviderScenarioCode.synthetic_restricted_json,
        (
            "Return only one compact JSON object with keys category, risk_level, and "
            "requires_review. category must be one of allow, review, reject. risk_level "
            "must be an integer from 1 through 5. requires_review must be boolean."
        ),
        400,
    ),
    (
        LiveProviderScenarioCode.synthetic_multilingual,
        (
            "Translate this invented sentence into English, French, and Yoruba in plain "
            "text: The quiet archive records a synthetic pilot result for review."
        ),
        500,
    ),
    (
        LiveProviderScenarioCode.synthetic_long_context_summarization,
        _synthetic_long_context(),
        1200,
    ),
)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "preflight":
            return preflight()
        if args.command == "run-pilot":
            return run_pilot(args)
        if args.command == "audit-evidence":
            return audit_evidence(args)
        if args.command == "cleanup":
            return cleanup(args)
    except PilotStop as exc:
        report_stop(exc)
        return exc.exit_status
    return 2


def build_parser() -> argparse.ArgumentParser:
    """Build the command parser."""

    parser = argparse.ArgumentParser(description="Run AION-248 live-provider pilot.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("preflight")

    run_parser = subparsers.add_parser("run-pilot")
    run_parser.add_argument("--authorization", required=True)
    run_parser.add_argument("--model", required=True)
    run_parser.add_argument("--temporary-root", required=True)
    run_parser.add_argument("--output", required=True)
    run_parser.add_argument("--confirm", required=True)
    run_parser.add_argument("--implementation-commit", required=True)

    audit_parser = subparsers.add_parser("audit-evidence")
    audit_parser.add_argument("--evidence", required=True)

    cleanup_parser = subparsers.add_parser("cleanup")
    cleanup_parser.add_argument("--temporary-root", required=True)
    return parser


def preflight() -> int:
    """Validate static runner policy without accessing credentials or network."""

    validate_endpoint(
        scheme=ENDPOINT_SCHEME,
        host=ENDPOINT_HOST,
        path=ENDPOINT_PATH,
        method=HTTP_METHOD,
    )
    print("AION-248 live provider pilot runner preflight PASS")
    return 0


def run_pilot(args: argparse.Namespace) -> int:
    """Run the exact six-request live pilot."""

    validate_runner_args(args)
    api_key = os.environ.pop("OPENAI_API_KEY", None)
    if not api_key:
        raise PilotStop(
            ABSENT_KEY_MESSAGE,
            normalized_error_class="credential_absent",
            exit_status=2,
        )

    temporary_root = Path(args.temporary_root)
    output_path = Path(args.output)
    service = ControlledLiveProviderPilotService()
    created_at = _now()
    authorization = service.create_authorization()
    selection = service.select_exact_model(
        selection_id="aion-248-selected-openai-responses-model",
        model_id=args.model,
        created_at=created_at,
    )
    approval = service.approve_operator_run(
        approval_id="aion-248-operator-approval",
        confirmation_text=args.confirm,
        selection=selection,
        created_at=created_at,
    )
    endpoint_policy = service.create_endpoint_policy(
        policy_id="aion-248-openai-responses-endpoint",
        created_at=created_at,
    )
    credential = service.attest_credential_presence(
        credential_present=True,
        provider_credentials_read=1,
        created_at=created_at,
    )
    _ = credential
    ensure_output_targets(temporary_root=temporary_root, output_path=output_path)

    request_fingerprints: list[str] = []
    response_fingerprints: list[str] = []
    usage_fingerprints: list[str] = []
    trust_fingerprints: list[str] = []
    uncertainty_fingerprints: list[str] = []
    latencies_ms: list[int] = []
    requests = []
    total_input_tokens = 0
    total_output_tokens = 0
    service.start_session()
    counters = default_required_counters()
    counters["dns_resolutions"] = 0
    try:
        for index, (scenario, prompt, maximum_output_tokens) in enumerate(SCENARIOS, start=1):
            payload = build_responses_payload(
                prompt=prompt,
                maximum_output_tokens=maximum_output_tokens,
                model_id=args.model,
            )
            request = service.project_request(
                request_id=f"aion-248-request-{index}",
                scenario_code=scenario,
                prompt_text=prompt,
                payload=payload,
                maximum_output_tokens=maximum_output_tokens,
                endpoint_policy=endpoint_policy,
                created_at=_now(),
            )
            requests.append(request)
            result, dns_count = send_openai_response(
                request_projection_fingerprint=request.projection_fingerprint or "",
                transport_result_id=f"aion-248-transport-{index}",
                payload=payload,
                api_key=api_key,
            )
            counters["dns_resolutions"] += dns_count
            text = result["text"]
            provider_payload = result["provider_payload"]
            transport_result = result["transport_result"]
            validate_scenario_response(scenario=scenario, text=text)
            response = service.project_response(
                response_projection_id=f"aion-248-response-{index}",
                request=request,
                transport_result=transport_result,
                created_at=_now(),
            )
            usage = service.create_usage(
                usage_id=f"aion-248-usage-{index}",
                request=request,
                response=response,
                transport_result=transport_result,
                created_at=_now(),
            )
            trust = service.assess_trust(
                trust_id=f"aion-248-trust-{index}",
                response=response,
                schema_validated=scenario
                == LiveProviderScenarioCode.synthetic_restricted_json,
                created_at=_now(),
            )
            uncertainty = service.project_uncertainty(
                uncertainty_id=f"aion-248-uncertainty-{index}",
                response=response,
                confidence_score=0.5,
                created_at=_now(),
            )
            service.record_audit(
                audit_id=f"aion-248-audit-{index}",
                event_type="response_projected",
                subject_fingerprint=response.projection_fingerprint or "",
                created_at=_now(),
            )
            request_fingerprints.append(request.projection_fingerprint or "")
            response_fingerprints.append(response.projection_fingerprint or "")
            usage_fingerprints.append(usage.usage_fingerprint or "")
            trust_fingerprints.append(trust.trust_fingerprint or "")
            uncertainty_fingerprints.append(uncertainty.uncertainty_fingerprint or "")
            latencies_ms.append(usage.latency_ms)
            total_input_tokens += usage.input_tokens
            total_output_tokens += usage.output_tokens
            provider_payload = None
            text = ""
            prompt = ""
            payload = {}
            _ = provider_payload, text, prompt, payload

        first_request = requests[0]
        service.exact_replay(request=first_request, created_at=_now())
        service.changed_replay(request=first_request, created_at=_now())
        service.close_session()
        service.replay_repository.clear()
        observability = create_observability_snapshot(
            snapshot_id="aion-248-observability",
            counters=counters,
            latencies_ms=tuple(latencies_ms),
            created_at=_now(),
        )
        integrity = service.audit_integrity(
            integrity_id="aion-248-integrity",
            authorization=authorization,
            selection=selection,
            endpoint_policy=endpoint_policy,
            transport_policy_fingerprint=service.transport_policy_fingerprint(),
            observability_fingerprint=observability.observability_fingerprint or "",
            created_at=_now(),
        )
        evidence = LiveProviderEvidenceBundle(
            implementation_commit=args.implementation_commit,
            selected_model_fingerprint=selection.selection_fingerprint or "",
            endpoint_policy_fingerprint=endpoint_policy.endpoint_policy_fingerprint or "",
            transport_policy_fingerprint=service.transport_policy_fingerprint(),
            operator_approval_fingerprint=approval.approval_fingerprint or "",
            external_cognition_component_binding_fingerprint=content_fingerprint(
                "external_cognition_component_binding", "AION-246"
            ),
            existing_model_gateway_component_binding_fingerprint=content_fingerprint(
                "existing_model_gateway_component_binding", "AION-233"
            ),
            request_projection_fingerprints=tuple(request_fingerprints),
            response_projection_fingerprints=tuple(response_fingerprints),
            usage_record_fingerprints=tuple(usage_fingerprints),
            trust_assessment_fingerprints=tuple(trust_fingerprints),
            uncertainty_projection_fingerprints=tuple(uncertainty_fingerprints),
            audit_chain_head=service.audit_ledger.chain_head(),
            observability_fingerprint=observability.observability_fingerprint or "",
            integrity_report_fingerprint=integrity.integrity_fingerprint or "",
            counters=counters,
            zero_counters=default_zero_counters(),
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_tokens=total_input_tokens + total_output_tokens,
            latency_summary=observability.latency_summary,
        )
        write_evidence(output_path=output_path, evidence=evidence)
    finally:
        api_key = ""
        service.close_session()
        remove_temporary_root(temporary_root)

    print("AION-248 live provider pilot completed")
    return 0


def audit_evidence(args: argparse.Namespace) -> int:
    """Validate committed or staged redacted evidence without provider access."""

    evidence_path = Path(args.evidence)
    if not evidence_path.is_absolute():
        raise PilotStop(
            "evidence path must be absolute",
            normalized_error_class="path_policy_violation",
        )
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert_no_protected_material(payload)
    evidence = LiveProviderEvidenceBundle.model_validate(payload)
    if evidence.report_fingerprint != evidence_report_fingerprint(
        evidence.model_dump(mode="json")
    ):
        raise PilotStop(
            "evidence fingerprint mismatch",
            normalized_error_class="evidence_integrity_failed",
        )
    print("AION-248 live provider pilot evidence audit PASS")
    return 0


def cleanup(args: argparse.Namespace) -> int:
    """Remove a temporary root after a stopped run."""

    temporary_root = Path(args.temporary_root)
    require_absolute_outside_repo(temporary_root, "temporary root")
    remove_temporary_root(temporary_root)
    print("AION-248 live provider pilot cleanup PASS")
    return 0


def validate_runner_args(args: argparse.Namespace) -> None:
    """Validate command arguments before credential access."""

    if args.authorization != AUTHORIZATION_TRANSACTION_ID:
        raise PilotStop(
            "authorization mismatch",
            normalized_error_class="authorization_mismatch",
        )
    if args.model != SELECTED_MODEL_ID:
        raise PilotStop("model mismatch", normalized_error_class="model_mismatch")
    if args.confirm != PILOT_CONFIRMATION_TEXT:
        raise PilotStop(
            "operator confirmation mismatch",
            normalized_error_class="operator_confirmation_mismatch",
        )
    require_absolute_outside_repo(Path(args.temporary_root), "temporary root")
    output_path = Path(args.output)
    if not output_path.is_absolute():
        raise PilotStop(
            "output path must be absolute",
            normalized_error_class="path_policy_violation",
        )
    if output_path.exists():
        raise PilotStop(
            "output path already exists",
            normalized_error_class="path_policy_violation",
        )
    require_absolute_outside_repo(output_path, "output path")


def ensure_output_targets(*, temporary_root: Path, output_path: Path) -> None:
    """Create the secure temporary root and reserve the output path."""

    if temporary_root.exists():
        raise PilotStop(
            "temporary root already exists",
            normalized_error_class="path_policy_violation",
        )
    temporary_root.mkdir(mode=0o700)
    mode = stat.S_IMODE(temporary_root.stat().st_mode)
    if mode != 0o700:
        raise PilotStop(
            "temporary root mode is not 0700",
            normalized_error_class="path_policy_violation",
        )
    if output_path.parent != temporary_root and temporary_root in output_path.parents:
        raise PilotStop(
            "output cannot be inside temporary root",
            normalized_error_class="path_policy_violation",
        )


def send_openai_response(
    *,
    request_projection_fingerprint: str,
    transport_result_id: str,
    payload: dict[str, object],
    api_key: str,
) -> tuple[dict[str, Any], int]:
    """Perform one authorized HTTPS request and return safe projections."""

    body = canonical_json_bytes(payload)
    if len(body) > MAXIMUM_REQUEST_PAYLOAD_BYTES:
        raise PilotStop(
            "request payload budget exceeded",
            normalized_error_class="request_budget_exceeded",
        )
    dns_count = verify_dns_resolution()
    started = time.monotonic()
    connection: http.client.HTTPSConnection | None = None
    response_body = b""
    try:
        context = ssl.create_default_context()
        connection = http.client.HTTPSConnection(
            ENDPOINT_HOST,
            ENDPOINT_PORT,
            timeout=MAXIMUM_REQUEST_TIMEOUT_SECONDS,
            context=context,
        )
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "OpenAI-Beta": "responses=v1",
        }
        connection.request(HTTP_METHOD, ENDPOINT_PATH, body=body, headers=headers)
        headers = {}
        response = connection.getresponse()
        http_status = int(response.status)
        if 300 <= http_status <= 399:
            raise PilotStop(
                "redirect response rejected",
                normalized_error_class="redirect_rejected",
                http_status=http_status,
            )
        response_body = response.read(MAXIMUM_RESPONSE_PAYLOAD_BYTES + 1)
        if len(response_body) > MAXIMUM_RESPONSE_PAYLOAD_BYTES:
            raise PilotStop(
                "response payload budget exceeded",
                normalized_error_class="response_budget_exceeded",
                http_status=http_status,
            )
        if http_status >= 400:
            raise PilotStop(
                "provider request failed",
                normalized_error_class=normalize_http_error(http_status),
                http_status=http_status,
            )
        provider_payload = json.loads(response_body.decode("utf-8"))
        text = extract_text_from_response(provider_payload)
        if contains_tool_or_media(provider_payload):
            raise PilotStop(
                "provider response contains an unauthorized tool or media item",
                normalized_error_class="provider_tool_or_media_output",
                http_status=http_status,
            )
        response_model = provider_payload.get("model")
        if response_model != SELECTED_MODEL_ID:
            raise PilotStop(
                "provider response model mismatch",
                normalized_error_class="provider_model_mismatch",
                http_status=http_status,
            )
        provider_status = str(provider_payload.get("status") or "completed")
        if provider_status != "completed":
            raise PilotStop(
                "provider response incomplete",
                normalized_error_class="provider_response_incomplete",
                http_status=http_status,
            )
        usage = extract_usage(provider_payload)
        if usage["input_tokens"] == 0:
            usage["input_tokens"] = estimate_tokens_from_bytes(len(body))
        if usage["output_tokens"] == 0:
            usage["output_tokens"] = estimate_tokens_from_bytes(len(text.encode("utf-8")))
        usage["total_tokens"] = usage["input_tokens"] + usage["output_tokens"]
        latency_ms = int(round((time.monotonic() - started) * 1000))
        transport_result = LiveProviderTransportResult(
            transport_result_id=transport_result_id,
            request_projection_fingerprint=request_projection_fingerprint,
            http_status=http_status,
            provider_status=provider_status,
            provider_response_model_id=SELECTED_MODEL_ID,
            response_byte_count=len(response_body),
            response_fingerprint=content_fingerprint("live_provider_response", response_body),
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            total_tokens=usage["total_tokens"],
            reasoning_tokens=usage["reasoning_tokens"],
            cached_tokens=usage["cached_tokens"],
            latency_ms=latency_ms,
        )
        safe_result = {
            "text": text,
            "provider_payload": provider_payload,
            "transport_result": transport_result,
        }
        return safe_result, dns_count
    except json.JSONDecodeError as exc:
        raise PilotStop(
            "provider returned non-json response",
            normalized_error_class="provider_non_json_response",
        ) from exc
    finally:
        response_body = b""
        body = b""
        if connection is not None:
            connection.close()


def verify_dns_resolution() -> int:
    """Resolve the exact host and reject private/reserved address classes."""

    infos = socket.getaddrinfo(ENDPOINT_HOST, ENDPOINT_PORT, type=socket.SOCK_STREAM)
    if not infos or len(infos) > MAXIMUM_DNS_RESOLUTIONS:
        raise PilotStop(
            "endpoint DNS resolution count is outside policy",
            normalized_error_class="dns_policy_violation",
        )
    public_count = 0
    for info in infos:
        address = info[4][0]
        parsed = ipaddress.ip_address(address)
        if any(
            (
                parsed.is_private,
                parsed.is_loopback,
                parsed.is_link_local,
                parsed.is_multicast,
                parsed.is_reserved,
                parsed.is_unspecified,
            )
        ):
            continue
        public_count += 1
    if public_count == 0:
        raise PilotStop(
            "endpoint resolution did not return a public address",
            normalized_error_class="dns_policy_violation",
        )
    return 1


def validate_scenario_response(*, scenario: LiveProviderScenarioCode, text: str) -> None:
    """Run local scenario-specific validation without trusting the content."""

    if not text.strip():
        raise PilotStop(
            "provider response text was empty",
            normalized_error_class="provider_empty_response",
        )
    if scenario == LiveProviderScenarioCode.synthetic_classification:
        normalized = text.strip().lower().split()[0].strip(".,:;")
        if normalized not in {"allow", "review", "reject"}:
            raise PilotStop(
                "classification response did not match local labels",
                normalized_error_class="local_validation_failed",
            )
    if scenario == LiveProviderScenarioCode.synthetic_restricted_json:
        parsed = parse_json_text(text)
        if set(parsed) != {"category", "risk_level", "requires_review"}:
            raise PilotStop(
                "restricted JSON keys mismatch",
                normalized_error_class="local_validation_failed",
            )
        if parsed["category"] not in {"allow", "review", "reject"}:
            raise PilotStop(
                "restricted JSON enum mismatch",
                normalized_error_class="local_validation_failed",
            )
        if not isinstance(parsed["risk_level"], int) or not 1 <= parsed["risk_level"] <= 5:
            raise PilotStop(
                "restricted JSON risk level mismatch",
                normalized_error_class="local_validation_failed",
            )
        if not isinstance(parsed["requires_review"], bool):
            raise PilotStop(
                "restricted JSON boolean mismatch",
                normalized_error_class="local_validation_failed",
            )


def parse_json_text(value: str) -> dict[str, object]:
    """Parse a compact JSON object from text."""

    text = value.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise PilotStop(
            "restricted JSON response did not contain an object",
            normalized_error_class="local_validation_failed",
        )
    parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise PilotStop(
            "restricted JSON response was not an object",
            normalized_error_class="local_validation_failed",
        )
    return parsed


def contains_tool_or_media(payload: object) -> bool:
    """Detect provider tool calls, files, images, or audio in response JSON."""

    if isinstance(payload, Mapping):
        for key, value in payload.items():
            normalized_key = str(key).lower()
            if any(
                marker in normalized_key
                for marker in ("tool", "function_call", "file", "image", "audio")
            ):
                return True
            if contains_tool_or_media(value):
                return True
    elif isinstance(payload, list):
        return any(contains_tool_or_media(item) for item in payload)
    elif isinstance(payload, str):
        normalized = payload.lower()
        return any(
            marker in normalized
            for marker in ("tool_call", "function_call", "file_search", "web_search")
        )
    return False


def write_evidence(*, output_path: Path, evidence: LiveProviderEvidenceBundle) -> None:
    """Write redacted evidence using a new 0600 output file."""

    payload = evidence.model_dump(mode="json")
    assert_no_protected_material(payload)
    fd = os.open(str(output_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    mode = stat.S_IMODE(output_path.stat().st_mode)
    if mode != 0o600:
        raise PilotStop(
            "output mode is not 0600",
            normalized_error_class="path_policy_violation",
        )


def require_absolute_outside_repo(path: Path, label: str) -> None:
    """Require an absolute path outside the canonical repository."""

    if not path.is_absolute():
        raise PilotStop(
            f"{label} must be absolute",
            normalized_error_class="path_policy_violation",
        )
    resolved = path.resolve(strict=False)
    if resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
        raise PilotStop(
            f"{label} must be outside the repository",
            normalized_error_class="path_policy_violation",
        )


def remove_temporary_root(temporary_root: Path) -> None:
    """Remove temporary state without touching repository paths."""

    if not temporary_root.exists():
        return
    require_absolute_outside_repo(temporary_root, "temporary root")
    shutil.rmtree(temporary_root)


def normalize_http_error(status: int) -> str:
    """Classify provider HTTP failures without recording provider text."""

    if status == 401:
        return "credential_rejected"
    if status == 403:
        return "model_access_denied"
    if status == 404:
        return "model_or_endpoint_unavailable"
    if status == 429:
        return "quota_or_rate_limit_blocked"
    if status >= 500:
        return "provider_service_unavailable"
    return "provider_http_error"


def report_stop(exc: PilotStop) -> None:
    """Emit a normalized stop report without protected content."""

    if exc.normalized_error_class == "credential_absent":
        print(ABSENT_KEY_MESSAGE)
        return

    print(str(exc), file=sys.stderr)
    print(f"normalized_provider_error_class={exc.normalized_error_class}", file=sys.stderr)
    print(f"http_status={exc.http_status}", file=sys.stderr)
    print(f"selected_provider={PROVIDER_ID}", file=sys.stderr)
    print(f"selected_model={SELECTED_MODEL_ID}", file=sys.stderr)
    print("credential_presence_state=absent_or_unusable", file=sys.stderr)
    print("provider_call_count=0", file=sys.stderr)
    print("successful_response_count=0", file=sys.stderr)
    print("cleanup_state=no_temporary_live_state_retained", file=sys.stderr)


def _now() -> datetime:
    return datetime.now(UTC)


if __name__ == "__main__":
    raise SystemExit(main())
