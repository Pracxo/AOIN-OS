from aion234_test_support import capability_auth, load_harness


def test_capability_runtime_resource_limits_are_exact() -> None:
    h = load_harness()
    expected = dict(h.CAPABILITY_RESOURCE_LIMITS)
    for key in h.CAPABILITY_ZERO_RESOURCE_LIMITS:
        expected[key] = 0
    assert capability_auth()["resource_limits"] == expected
