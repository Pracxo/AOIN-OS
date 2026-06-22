"""Operating mode and risk ordering helpers for autonomy governance."""

_MODE_RANK = {
    "disabled": 0,
    "observe": 1,
    "assist": 2,
    "plan_only": 3,
    "dry_run": 4,
    "supervised_controlled": 5,
    "delegated_controlled": 6,
}

_RISK_RANK = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


def mode_rank(mode: str) -> int:
    """Return the strict ordering rank for one autonomy mode."""
    try:
        return _MODE_RANK[mode]
    except KeyError as exc:
        raise ValueError(f"unknown_autonomy_mode:{mode}") from exc


def min_mode(mode_a: str, mode_b: str) -> str:
    """Return the lower-permission mode."""
    return mode_a if mode_rank(mode_a) <= mode_rank(mode_b) else mode_b


def mode_allows(requested_mode: str, max_mode: str) -> bool:
    """Return whether a requested mode is inside the maximum mode envelope."""
    if max_mode == "disabled":
        return False
    return mode_rank(requested_mode) <= mode_rank(max_mode)


def risk_rank(risk_level: str) -> int:
    """Return the strict ordering rank for one risk level."""
    try:
        return _RISK_RANK[risk_level]
    except KeyError as exc:
        raise ValueError(f"unknown_risk_level:{risk_level}") from exc


def min_risk(risk_a: str, risk_b: str) -> str:
    """Return the stricter risk ceiling."""
    return risk_a if risk_rank(risk_a) <= risk_rank(risk_b) else risk_b


def risk_allows(requested_risk: str, max_risk: str) -> bool:
    """Return whether a requested risk is inside the maximum risk envelope."""
    return risk_rank(requested_risk) <= risk_rank(max_risk)


def mode_requires_approval(mode: str, approval_required_modes: list[str]) -> bool:
    """Return whether a mode is configured to require approval."""
    mode_rank(mode)
    return mode in set(approval_required_modes)
