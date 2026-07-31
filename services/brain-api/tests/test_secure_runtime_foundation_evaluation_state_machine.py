from secure_runtime_aion232_test_helpers import scenario


def test_state_machine_receipts_and_repository_boundaries_pass() -> None:
    state = scenario("closed_state_machine")["requirements"]
    assert state["allowed_state_sequence_exact"] is True
    assert state["stage_skipping_rejected"] is True
    assert state["transition_after_expiry_rejected"] is True
    assert state["transition_after_kill_rejected"] is True
    assert state["transition_after_close_rejected"] is True
    receipts = scenario("stage_receipt_sequence_and_hash_chain")["requirements"]
    assert receipts["sequence_contiguous"] is True
    assert receipts["missing_receipt_detected"] is True
    assert receipts["reordered_receipt_detected"] is True
    assert receipts["changed_receipt_detected"] is True
    repo = scenario("in_memory_session_repository_and_concurrency")["requirements"]
    assert repo["no_database"] is True
    assert repo["no_global_singleton"] is True
    assert repo["session_close_releases_request_reference"] is True
