from aion234_test_support import report, scenario


def test_provider_and_model_manifests_are_closed() -> None:
    payload = report()
    provider = scenario(payload, "provider_manifest_registry_integrity")
    model = scenario(payload, "model_manifest_registry_integrity")
    assert provider["passed"] is True
    assert model["passed"] is True
    assert provider["evidence"]["provider_manifest_count"] == 1
    assert model["evidence"]["model_manifest_count"] == 2
