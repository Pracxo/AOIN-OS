from __future__ import annotations

from capability_runtime_operator_evaluation_test_support import assert_scenario_passes


def test_execution_receipt_chain_and_provenance_verified():
    item = assert_scenario_passes("execution_receipt_chain_and_provenance")

    assert {check["name"] for check in item["checks"]} >= {
        "eight_receipts",
        "first_receipt_zero_prior",
        "receipt_chain_contiguous",
        "authorization_lineage_exact",
    }
