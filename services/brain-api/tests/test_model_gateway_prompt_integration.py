from __future__ import annotations

from types import SimpleNamespace

from tests.model_gateway_fakes import gateway_request, model_gateway_service


class BlockingPromptGovernance:
    def compile(self, request: object) -> object:
        packet = SimpleNamespace(
            prompt_packet_id="prompt-packet-1",
            boundary_check_id="boundary-1",
        )
        manifest = SimpleNamespace(model_input_manifest_id="manifest-1")
        return SimpleNamespace(blocked=True, prompt_packet=packet, model_input_manifest=manifest)


class AllowingPromptGovernance:
    def __init__(self) -> None:
        self.requests: list[object] = []

    def compile(self, request: object) -> object:
        self.requests.append(request)
        packet = SimpleNamespace(
            prompt_packet_id="prompt-packet-1",
            boundary_check_id="boundary-1",
        )
        manifest = SimpleNamespace(model_input_manifest_id="manifest-1")
        return SimpleNamespace(blocked=False, prompt_packet=packet, model_input_manifest=manifest)


def test_model_gateway_refuses_blocked_prompt_packet() -> None:
    service, _, _, _ = model_gateway_service()
    service.set_prompt_governance_service(BlockingPromptGovernance())

    response = service.complete(gateway_request())

    assert response.status == "blocked_by_policy"
    assert response.reason == "prompt_boundary_blocked"


def test_model_gateway_records_prompt_manifest_metadata() -> None:
    prompt_governance = AllowingPromptGovernance()
    service, _, _, _ = model_gateway_service()
    service.set_prompt_governance_service(prompt_governance)
    request = gateway_request()

    response = service.complete(request)

    assert response.status == "completed"
    assert prompt_governance.requests
    assert request.metadata["prompt_packet_id"] == "prompt-packet-1"
    assert request.metadata["model_input_manifest_id"] == "manifest-1"
