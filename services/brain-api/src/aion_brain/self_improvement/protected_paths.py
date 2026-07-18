"""Protected-core path classification for self-improvement proposals."""

from __future__ import annotations

from fnmatch import fnmatch

from aion_brain.contracts.self_improvement import ImprovementProtectedPathDecision

PROTECTED_CORE_PATTERNS: tuple[str, ...] = (
    ".github/workflows/",
    "scripts/*approval*",
    "scripts/*no-go*",
    "scripts/*release*",
    "scripts/lib/*authorization*",
    "services/brain-api/src/aion_brain/policy/",
    "services/brain-api/src/aion_brain/audit/",
    "services/brain-api/src/aion_brain/self_improvement/approval*",
    "services/brain-api/src/aion_brain/self_improvement/protected*",
    "docs/self-improvement/holdout/",
    "docs/self-improvement/policy/",
)


def normalize_repo_path(path: str) -> str:
    """Normalize a repository path for protected-core matching."""

    normalized = path.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.lstrip("/")


def matched_protected_pattern(path: str) -> str | None:
    """Return the matched protected-core pattern, if any."""

    normalized = normalize_repo_path(path)
    for pattern in PROTECTED_CORE_PATTERNS:
        if pattern.endswith("/") and normalized.startswith(pattern):
            return pattern
        if fnmatch(normalized, pattern):
            return pattern
    return None


def touches_protected_core(paths: list[str] | tuple[str, ...]) -> bool:
    """Return whether any path touches the protected core."""

    return any(matched_protected_pattern(path) is not None for path in paths)


def protected_path_decision(path: str) -> ImprovementProtectedPathDecision:
    """Classify one path for protected-core governance."""

    matched_pattern = matched_protected_pattern(path)
    protected = matched_pattern is not None
    return ImprovementProtectedPathDecision(
        path=normalize_repo_path(path),
        protected=protected,
        matched_pattern=matched_pattern,
        required_approver_count=2 if protected else 1,
        reason="protected core boundary match" if protected else "outside protected core",
    )


def protected_path_decisions(
    paths: list[str] | tuple[str, ...],
) -> tuple[ImprovementProtectedPathDecision, ...]:
    """Classify multiple paths for protected-core governance."""

    return tuple(protected_path_decision(path) for path in paths)
