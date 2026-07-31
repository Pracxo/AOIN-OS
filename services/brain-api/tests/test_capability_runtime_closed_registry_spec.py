from aion234_test_support import capability_auth, load_harness


def test_closed_capability_registry_is_exact() -> None:
    h = load_harness()
    auth = capability_auth()
    assert auth["closed_capability_registry"] == h.CAPABILITY_REGISTRY
    assert len(auth["closed_capability_registry"]) == 8
