from aion234_test_support import capability_auth, load_harness


def test_every_capability_runtime_authorized_field_is_true() -> None:
    h = load_harness()
    auth = capability_auth()
    assert set(auth["authorized_capabilities"]) == set(h.AUTHORIZED_CAPABILITY_FLAGS)
    assert all(
        auth["authorized_capabilities"][key] is True
        for key in h.AUTHORIZED_CAPABILITY_FLAGS
    )
