from __future__ import annotations

from aion_brain.prompts.manifest import ModelInputManifestService
from tests.prompt_helpers import compile_request, compiler


def test_model_input_manifest_service_lists_created_manifest() -> None:
    prompt_compiler, repo, policy = compiler()
    result = prompt_compiler.compile(compile_request())
    service = ModelInputManifestService(repo, policy)

    manifests = service.list_manifests(
        ["workspace:main"],
        prompt_packet_id=result.prompt_packet.prompt_packet_id,
    )

    assert manifests
    assert manifests[0].input_hash == result.prompt_packet.rendered_hash
