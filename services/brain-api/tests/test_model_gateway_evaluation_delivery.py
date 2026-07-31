from aion234_test_support import load_harness, report


def test_aion233_delivery_and_ci_integrity_recorded() -> None:
    h = load_harness()
    payload = report()
    result = next(
        item
        for item in payload["scenario_results"]
        if item["scenario_id"] == "aion_233_delivery_and_ci_integrity"
    )
    assert result["passed"] is True
    assert payload["implementation_prs"] == [151, 152]
    assert payload["implementation_feature_commits"] == list(h.IMPLEMENTATION_FEATURE_COMMITS)
    assert payload["implementation_merge_commits"] == list(h.IMPLEMENTATION_MERGE_COMMITS)
