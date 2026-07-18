"""Change-budget evaluation for governed self-improvement."""

from __future__ import annotations

from dataclasses import dataclass

from aion_brain.contracts.self_improvement import ImprovementChangeBudget, utc_now


@dataclass(frozen=True)
class ChangeBudgetLimit:
    """Static limits for a governed self-improvement proposal."""

    max_files: int = 20
    max_insertions: int = 1_500
    max_deletions: int = 500
    max_dependency_changes: int = 0
    max_protected_paths: int = 0


DEFAULT_CHANGE_BUDGET = ChangeBudgetLimit()


def evaluate_change_budget(
    *,
    proposal_id: str,
    observed_files: int,
    observed_insertions: int,
    observed_deletions: int,
    dependency_changes: int = 0,
    protected_paths_touched: int = 0,
    limit: ChangeBudgetLimit = DEFAULT_CHANGE_BUDGET,
    evidence_refs: tuple[str, ...] = (),
) -> ImprovementChangeBudget:
    """Evaluate observed change size against a static governance budget."""

    within_budget = (
        observed_files <= limit.max_files
        and observed_insertions <= limit.max_insertions
        and observed_deletions <= limit.max_deletions
        and dependency_changes <= limit.max_dependency_changes
        and protected_paths_touched <= limit.max_protected_paths
    )
    return ImprovementChangeBudget(
        change_budget_id=f"{proposal_id}:budget",
        proposal_id=proposal_id,
        max_files=limit.max_files,
        max_insertions=limit.max_insertions,
        max_deletions=limit.max_deletions,
        max_dependency_changes=limit.max_dependency_changes,
        max_protected_paths=limit.max_protected_paths,
        observed_files=observed_files,
        observed_insertions=observed_insertions,
        observed_deletions=observed_deletions,
        dependency_changes=dependency_changes,
        protected_paths_touched=protected_paths_touched,
        within_budget=within_budget,
        evidence_refs=evidence_refs,
        created_at=utc_now(),
    )

