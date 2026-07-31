from aion234_test_support import capability_auth, load_harness


def test_every_capability_runtime_prohibited_field_is_false() -> None:
    h = load_harness()
    auth = capability_auth()
    assert set(auth["prohibited_capabilities"]) == set(h.PROHIBITED_CAPABILITY_FLAGS)
    assert all(
        auth["prohibited_capabilities"][key] is False
        for key in h.PROHIBITED_CAPABILITY_FLAGS
    )
