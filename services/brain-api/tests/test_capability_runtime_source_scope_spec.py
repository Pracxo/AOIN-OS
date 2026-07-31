from aion234_test_support import REPO_ROOT, capability_auth, load_harness


def test_future_source_scope_is_recorded_but_absent() -> None:
    h = load_harness()
    assert capability_auth()["future_source_scope"] == list(h.FUTURE_AION235_SOURCE_SCOPE)
    for path in h.FUTURE_AION235_SOURCE_SCOPE:
        assert not (REPO_ROOT / path).exists()
