"""Freeze gate report helpers."""

from aion_brain.contracts.freeze import FreezeGateCheck


def build_freeze_report(checks: list[FreezeGateCheck]) -> dict[str, object]:
    """Build a deterministic freeze gate summary."""
    failures = [check for check in checks if check.status == "failed"]
    warnings = [check for check in checks if check.status == "warning"]
    return {
        "check_count": len(checks),
        "passed_count": sum(1 for check in checks if check.status == "passed"),
        "failed_count": len(failures),
        "warning_count": len(warnings),
        "skipped_count": sum(1 for check in checks if check.status == "skipped"),
        "failed_checks": [check.name for check in failures],
        "warning_checks": [check.name for check in warnings],
        "release_ready": not failures,
        "recommendations": _recommendations(failures, warnings),
    }


def _recommendations(
    failures: list[FreezeGateCheck],
    warnings: list[FreezeGateCheck],
) -> list[str]:
    recommendations: list[str] = []
    names = {check.name for check in failures}
    if "migration_baseline" in names:
        recommendations.append("review_migration_baseline")
    if "boundary_check" in names:
        recommendations.append("review_boundary_violations")
    if "no_domain_drift" in names:
        recommendations.append("remove_domain_specific_artifacts")
    if "release_baseline" in names:
        recommendations.append("review_release_baseline")
    if "no_raw_secrets" in names:
        recommendations.append("remove_secret_like_metadata")
    if "no_full_autonomy_default" in names:
        recommendations.append("disable_full_autonomy_default")
    if warnings:
        recommendations.append("review_freeze_warnings")
    return recommendations
