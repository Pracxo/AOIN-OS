"""Context fusion evidence tests."""

from aion_brain.contracts.retrieval import ContextFusionRequest
from aion_brain.retrieval.fusion import ContextFusionEngine
from tests.test_context_fusion import make_item, make_result


def test_context_fusion_preserves_evidence_ref() -> None:
    """Fused context records evidence references."""
    item = make_item("evidence-chunk-1", "alpha source", 0.9).model_copy(
        update={"source": "evidence_vault", "evidence_ref": "evidence-1"}
    )

    bundle = ContextFusionEngine().fuse(
        ContextFusionRequest(retrieval_result=make_result([item]), goal="alpha")
    )

    assert bundle.evidence_refs == ["evidence-1"]
    assert bundle.metadata["evidence_refs"] == ["evidence-1"]
