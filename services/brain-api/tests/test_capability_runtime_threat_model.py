from aion234_test_support import capability_auth, load_harness


def test_threat_model_records_required_items() -> None:
    h = load_harness()
    assert capability_auth()["threat_model"] == list(h.THREAT_MODEL_ITEMS)
