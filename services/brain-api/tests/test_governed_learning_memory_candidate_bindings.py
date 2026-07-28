from __future__ import annotations

import pytest
from knowledge_verified_memory_test_helpers import fp
from test_governed_learning_memory_contracts import sample_transaction_context


def test_candidate_binding_is_read_only_and_redacted():
    context = sample_transaction_context()
    binding = context.planner.bind_candidates(
        context.request,
        (context.candidate,),
        memory_snapshot_id="memory-snapshot-binding",
        memory_snapshot_fingerprint=fp("memory-snapshot-binding"),
    )[0]

    assert binding.candidate_id == context.candidate.candidate_id
    assert binding.read_only is True
    assert binding.redacted is True
    assert binding.runtime_effect is False


def test_candidate_binding_rejects_unbound_candidate():
    context = sample_transaction_context()
    other = context.candidate.model_copy(update={"candidate_id": "candidate-unbound"})

    with pytest.raises(ValueError):
        context.planner.bind_candidates(
            context.request,
            (other,),
            memory_snapshot_id="memory-snapshot-binding",
            memory_snapshot_fingerprint=fp("memory-snapshot-binding"),
        )
