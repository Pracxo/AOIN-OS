from aion234_test_support import REPO_ROOT, capability_auth, load_harness
from capability_runtime_test_support import load_runtime


def test_authorized_aion235_source_scope_is_recorded_and_implemented() -> None:
    h = load_harness()
    runtime = load_runtime()
    assert capability_auth()["future_source_scope"] == list(h.FUTURE_AION235_SOURCE_SCOPE)
    for path in h.FUTURE_AION235_SOURCE_SCOPE:
        assert (REPO_ROOT / path).exists()
    assert runtime.AUTHORIZATION_TRANSACTION_ID == "AION-234-SRI-0003"
    assert runtime.IMPLEMENTATION_TASK == "AION-235"
    assert runtime.FORMAL_CLOSEOUT_TASK == "AION-236"
