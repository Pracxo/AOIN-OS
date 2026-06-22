"""Deterministic Context Fusion Engine."""

from collections.abc import Iterable
from datetime import UTC, datetime

from aion_brain.contracts.retrieval import (
    ContextBundle,
    ContextFusionRequest,
    RetrievedContextItem,
)
from aion_brain.retrieval.scoring import content_hash_key


class ContextFusionEngine:
    """Fuse retrieval results into a reasoning-ready context bundle."""

    def fuse(self, request: ContextFusionRequest) -> ContextBundle:
        """Fuse retrieval items deterministically without summarization models."""
        selected = _select_items(
            request.retrieval_result.items,
            max_items=request.max_items,
            max_chars=request.max_chars,
        )
        return ContextBundle(
            bundle_id=f"bundle-{request.retrieval_result.retrieval_id}",
            retrieval_id=request.retrieval_result.retrieval_id,
            goal=request.goal,
            items=selected,
            fused_summary=_summary(request.goal, selected),
            memory_refs=_unique(
                item.source_id
                for item in selected
                if item.source in {"lexical_memory", "semantic_memory", "skill_registry"}
            ),
            capability_refs=_unique(
                item.capability_id or item.source_id
                for item in selected
                if item.source == "capability_registry"
            ),
            graph_node_refs=_unique(
                node_id for item in selected for node_id in item.graph_node_ids
            ),
            graph_edge_refs=_unique(
                edge_id for item in selected for edge_id in item.graph_edge_ids
            ),
            trace_refs=_unique(trace_id for item in selected for trace_id in item.trace_refs),
            evidence_refs=_unique(item.evidence_ref for item in selected),
            metadata={
                "evidence_refs": _unique(item.evidence_ref for item in selected),
            },
            constraints=request.retrieval_result.constraints,
            token_budget_hint=max(1, request.max_chars // 4),
            created_at=datetime.now(UTC),
        )


def _select_items(
    items: list[RetrievedContextItem],
    *,
    max_items: int,
    max_chars: int,
) -> list[RetrievedContextItem]:
    selected: list[RetrievedContextItem] = []
    seen_content: set[str] = set()
    used_chars = 0
    for item in sorted(
        items,
        key=lambda candidate: (-candidate.score, candidate.source, candidate.source_id),
    ):
        key = content_hash_key(item.content)
        if key in seen_content:
            continue
        next_size = len(item.content)
        if selected and used_chars + next_size > max_chars:
            continue
        if not selected and next_size > max_chars:
            item = item.model_copy(update={"content": item.content[:max_chars]})
            next_size = len(item.content)
        selected.append(item)
        seen_content.add(key)
        used_chars += next_size
        if len(selected) >= max_items:
            break
    return selected


def _summary(goal: str, items: list[RetrievedContextItem]) -> str:
    lines = [f"Retrieved context for goal: {goal}"]
    for index, item in enumerate(items, start=1):
        title = f"{item.title}: " if item.title else ""
        lines.append(f"{index}. [{item.source}] {title}{_snippet(item.content)}")
    return "\n".join(lines)


def _snippet(content: str, *, limit: int = 240) -> str:
    compact = " ".join(content.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."


def _unique(values: Iterable[str | None]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if isinstance(value, str) and value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
