from aion234_test_support import capability_auth, load_harness
from capability_runtime_test_support import load_runtime


def test_closed_capability_registry_is_exact() -> None:
    h = load_harness()
    runtime = load_runtime()
    auth = capability_auth()
    registry = auth["capability_runtime_closed_registry"]
    assert len(registry) == 8
    assert [
        {
            "capability_id": item["capability_id"],
            "risk": item["risk"],
            "approval_required": item["approval_required"],
            "execution_kind": item["execution_kind"],
            "side_effect_class": item["side_effect_class"],
        }
        for item in registry
    ] == h.CAPABILITY_REGISTRY
    for item in registry:
        for key, expected in h.CAPABILITY_REGISTRY_REQUIRED_FLAGS.items():
            assert item[key] is expected
    assert [item.capability_id for item in runtime.CAPABILITY_MANIFESTS] == [
        item["capability_id"] for item in registry
    ]
