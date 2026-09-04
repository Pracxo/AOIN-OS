from __future__ import annotations

import ast
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aion_brain.contracts.live_provider_pilot import (
    ENDPOINT_HOST,
    ENDPOINT_PATH,
    ENDPOINT_SCHEME,
    HTTP_METHOD,
    PILOT_CONFIRMATION_TEXT,
    SELECTED_MODEL_ID,
    LiveProviderScenarioCode,
    LiveProviderTransportResult,
    content_fingerprint,
    default_required_counters,
    default_zero_counters,
    evidence_report_fingerprint,
    validate_responses_payload,
    validate_selected_model,
)
from aion_brain.live_provider_pilot import ControlledLiveProviderPilotService
from aion_brain.live_provider_pilot.endpoint_policy import reject_proxy, reject_redirect
from aion_brain.live_provider_pilot.evidence import create_evidence_bundle
from aion_brain.live_provider_pilot.openai_responses_adapter import (
    build_responses_payload,
    extract_text_from_response,
    extract_usage,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ROOT = REPO_ROOT / "services/brain-api/src/aion_brain/live_provider_pilot"
CONTRACT = REPO_ROOT / "services/brain-api/src/aion_brain/contracts/live_provider_pilot.py"
RUNNER = REPO_ROOT / "scripts/live-provider-pilot-local-run.py"
EXPECTED_ABSENT_KEY_MESSAGE = (
    "The AION-248 implementation is ready, but the authorized live pilot has not started. "
    "Make one OpenAI API key available to the Codex process through the OPENAI_API_KEY "
    "environment variable. Do not paste the key into chat, source, configuration files, "
    "GitHub, Docker images or committed evidence."
)


def test_absent_openai_key_stop_message_is_exact(tmp_path: Path) -> None:
    tree = ast.parse(RUNNER.read_text(encoding="utf-8"), filename=str(RUNNER))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if "ABSENT_KEY_MESSAGE" in names:
                assert ast.literal_eval(node.value) == EXPECTED_ABSENT_KEY_MESSAGE
                break
    else:
        raise AssertionError("ABSENT_KEY_MESSAGE constant not found")

    temporary_root = tmp_path / "live-provider-temp"
    output_path = tmp_path / "live-provider-evidence.json"
    env = os.environ.copy()
    env.pop("OPENAI_API_KEY", None)
    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "run-pilot",
            "--authorization",
            "AION-247-AI-0002",
            "--model",
            "gpt-5.6-terra",
            "--temporary-root",
            str(temporary_root),
            "--output",
            str(output_path),
            "--confirm",
            "RUN_SINGLE_OPENAI_RESPONSES_API_SYNTHETIC_LIVE_PROVIDER_PILOT",
            "--implementation-commit",
            "0" * 40,
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert result.stdout == f"{EXPECTED_ABSENT_KEY_MESSAGE}\n"
    assert result.stderr == ""
    assert not temporary_root.exists()
    assert not output_path.exists()


def test_authorization_model_endpoint_and_confirmation_are_exact() -> None:
    now = datetime.now(UTC)
    service = ControlledLiveProviderPilotService()

    authorization = service.create_authorization()
    selection = service.select_exact_model(
        selection_id="aion-248-selection",
        model_id=SELECTED_MODEL_ID,
        created_at=now,
    )
    approval = service.approve_operator_run(
        approval_id="aion-248-approval",
        confirmation_text=PILOT_CONFIRMATION_TEXT,
        selection=selection,
        created_at=now,
    )
    endpoint = service.create_endpoint_policy(policy_id="aion-248-endpoint", created_at=now)

    assert authorization.authorization_transaction_id == "AION-247-AI-0002"
    assert authorization.authorization_fingerprint
    assert selection.selected_model_id == "gpt-5.6-terra"
    assert approval.approval_fingerprint
    assert endpoint.host == "api.openai.com"
    assert endpoint.path == "/v1/responses"

    with pytest.raises(ValueError, match="exact AION-248 model"):
        validate_selected_model("gpt-5.6")
    with pytest.raises(ValueError, match="model switch"):
        service.select_exact_model(
            selection_id="aion-248-selection-2",
            model_id="gpt-5.6-sol",
            created_at=now,
        )
    with pytest.raises(ValueError, match="endpoint"):
        service.validate_endpoint_policy(
            scheme=ENDPOINT_SCHEME,
            host="example.invalid",
            path=ENDPOINT_PATH,
            method=HTTP_METHOD,
        )


def test_responses_payload_is_store_background_stream_false_and_tool_free() -> None:
    payload = build_responses_payload(
        prompt="Synthetic pilot prompt.",
        maximum_output_tokens=128,
    )

    assert payload["model"] == SELECTED_MODEL_ID
    assert payload["store"] is False
    assert payload["background"] is False
    assert payload["stream"] is False
    assert "tools" not in payload
    assert "files" not in payload
    assert "previous_response_id" not in payload
    validate_responses_payload(payload)

    bad_payload = {**payload, "tools": []}
    with pytest.raises(ValueError, match="forbidden field"):
        validate_responses_payload(bad_payload)
    with pytest.raises(ValueError, match="model mismatch"):
        validate_responses_payload({**payload, "model": "gpt-5.6"})
    with pytest.raises(ValueError, match="redirect"):
        reject_redirect("https://example.invalid")
    with pytest.raises(ValueError, match="proxy use"):
        reject_proxy(True)


def test_fake_transport_flow_projects_response_usage_trust_and_replay() -> None:
    now = datetime.now(UTC)
    service = ControlledLiveProviderPilotService()
    endpoint = service.create_endpoint_policy(policy_id="aion-248-endpoint", created_at=now)
    service.select_exact_model(
        selection_id="aion-248-selection",
        model_id=SELECTED_MODEL_ID,
        created_at=now,
    )
    service.start_session()
    payload = build_responses_payload(
        prompt="Classify this invented event as allow, review, or reject.",
        maximum_output_tokens=128,
    )
    request = service.project_request(
        request_id="aion-248-request-1",
        scenario_code=LiveProviderScenarioCode.synthetic_classification,
        prompt_text=str(payload["input"]),
        payload=payload,
        maximum_output_tokens=128,
        endpoint_policy=endpoint,
        created_at=now,
    )
    text = "review"
    transport_result = LiveProviderTransportResult(
        transport_result_id="aion-248-transport-1",
        request_projection_fingerprint=request.projection_fingerprint or "",
        http_status=200,
        provider_status="completed",
        response_byte_count=len(text.encode("utf-8")),
        response_fingerprint=content_fingerprint("live_provider_response", text),
        input_tokens=30,
        output_tokens=5,
        total_tokens=35,
        reasoning_tokens=0,
        cached_tokens=0,
        latency_ms=123,
    )

    response = service.project_response(
        response_projection_id="aion-248-response-1",
        request=request,
        transport_result=transport_result,
        created_at=now,
    )
    usage = service.create_usage(
        usage_id="aion-248-usage-1",
        request=request,
        response=response,
        transport_result=transport_result,
        created_at=now,
    )
    trust = service.assess_trust(
        trust_id="aion-248-trust-1",
        response=response,
        schema_validated=False,
        created_at=now,
    )
    uncertainty = service.project_uncertainty(
        uncertainty_id="aion-248-uncertainty-1",
        response=response,
        confidence_score=0.5,
        created_at=now,
    )
    exact_replay = service.exact_replay(request=request, created_at=now)
    changed_replay = service.changed_replay(request=request, created_at=now)
    service.close_session()

    assert response.raw_response_retained is False
    assert response.output_text_retained is False
    assert usage.total_tokens == 35
    assert trust.provider_output_promoted_to_knowledge is False
    assert uncertainty.uncertainty_fingerprint
    assert exact_replay.additional_provider_call_performed is False
    assert changed_replay.outcome.value == "changed_replay_rejected"


def test_evidence_bundle_fingerprint_and_zero_effects_are_valid() -> None:
    fingerprint = content_fingerprint("test", "safe")
    counters = default_required_counters()
    zero_counters = default_zero_counters()
    payload = {
        "implementation_commit": "a" * 40,
        "selected_model_fingerprint": fingerprint,
        "endpoint_policy_fingerprint": fingerprint,
        "transport_policy_fingerprint": fingerprint,
        "operator_approval_fingerprint": fingerprint,
        "external_cognition_component_binding_fingerprint": fingerprint,
        "existing_model_gateway_component_binding_fingerprint": fingerprint,
        "request_projection_fingerprints": tuple([fingerprint] * 6),
        "response_projection_fingerprints": tuple([fingerprint] * 6),
        "usage_record_fingerprints": tuple([fingerprint] * 6),
        "trust_assessment_fingerprints": tuple([fingerprint] * 6),
        "uncertainty_projection_fingerprints": tuple([fingerprint] * 6),
        "audit_chain_head": fingerprint,
        "observability_fingerprint": fingerprint,
        "integrity_report_fingerprint": fingerprint,
        "counters": counters,
        "zero_counters": zero_counters,
        "total_input_tokens": 60,
        "total_output_tokens": 30,
        "total_tokens": 90,
        "latency_summary": {"mean": 10, "p50": 10, "p95": 10, "maximum": 10},
    }

    evidence = create_evidence_bundle(**payload)

    assert evidence.report_fingerprint == evidence_report_fingerprint(
        evidence.model_dump(mode="json")
    )
    assert evidence.provider_id == "openai"
    assert evidence.selected_model_id == "gpt-5.6-terra"
    assert all(value == 0 for value in evidence.zero_counters.values())


def test_openai_adapter_extracts_text_and_usage_without_transport() -> None:
    response = {
        "model": SELECTED_MODEL_ID,
        "status": "completed",
        "output": [
            {
                "type": "message",
                "content": [{"type": "output_text", "text": "synthetic result"}],
            }
        ],
        "usage": {
            "input_tokens": 10,
            "output_tokens": 4,
            "total_tokens": 14,
            "output_tokens_details": {"reasoning_tokens": 1},
            "input_tokens_details": {"cached_tokens": 2},
        },
    }

    assert extract_text_from_response(response) == "synthetic result"
    assert extract_usage(response) == {
        "input_tokens": 10,
        "output_tokens": 4,
        "total_tokens": 14,
        "reasoning_tokens": 1,
        "cached_tokens": 2,
    }


def test_installed_live_provider_package_has_no_network_or_environment_access() -> None:
    prohibited_imports = {
        "aiohttp",
        "http",
        "http.client",
        "httpx",
        "openai",
        "os",
        "requests",
        "socket",
        "ssl",
        "subprocess",
        "urllib",
        "urllib.request",
    }
    files = [CONTRACT, *sorted(PACKAGE_ROOT.glob("*.py"))]
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = {alias.name for alias in node.names}
                assert not names.intersection(prohibited_imports), path
            if isinstance(node, ast.ImportFrom):
                assert (node.module or "") not in prohibited_imports, path
            if isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name) and node.value.id == "os":
                    assert node.attr != "environ", path


def test_endpoint_identity_constants_are_exact() -> None:
    assert (ENDPOINT_SCHEME, ENDPOINT_HOST, ENDPOINT_PATH, HTTP_METHOD) == (
        "https",
        "api.openai.com",
        "/v1/responses",
        "POST",
    )
