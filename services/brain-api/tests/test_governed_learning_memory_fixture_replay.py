from __future__ import annotations

import json

from test_governed_learning_memory_contracts import REPO_ROOT, sample_transaction_context

from aion_brain.contracts import governed_learning_memory as glm


def test_explicit_local_fixture_replay_is_read_only(tmp_path):
    context = sample_transaction_context()
    fixture = glm.build_promotion_fixture_envelope(
        fixture_id="promotion-fixture-001",
        records=(context.record,),
    )
    path = tmp_path / "promotion-fixture.json"
    path.write_text(json.dumps(fixture.model_dump(mode="json"), sort_keys=True), encoding="utf-8")

    replayed = glm.ExplicitLocalPromotionFixtureReplay(
        repository_root=REPO_ROOT,
    ).replay_fixture(path)

    assert replayed.fixture_id == fixture.fixture_id
    assert replayed.record_count == 1
    assert replayed.read_only is True
    assert replayed.runtime_effect is False
