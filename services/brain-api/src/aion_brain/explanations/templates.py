"""Generic deterministic explanation templates."""

from __future__ import annotations

EXPLANATION_TEMPLATES: dict[str, str] = {
    "policy_blocked": (
        "The action was blocked by policy. The relevant policy decision is linked below."
    ),
    "autonomy_blocked": "The current autonomy mode does not allow this action.",
    "approval_required": "This action requires approval before it can continue.",
    "low_confidence": (
        "The answer has limited support. More evidence or clarification may be needed."
    ),
    "ungrounded_response": "The response lacks evidence references.",
    "capability_unavailable": (
        "This capability is disabled, unavailable, or optional in the current configuration."
    ),
    "decision_recommendation": (
        "The recommendation was based on the available options, risk, autonomy, policy, "
        "and evidence constraints."
    ),
    "retrieval_choice": (
        "This context was selected because it matched the query and passed governance filters."
    ),
    "outcome_partial": "The outcome was partial because some expected effects were missing.",
    "generic": "AION built this explanation from observable local records.",
}


def explanation_template(name: str) -> str:
    """Return a generic template by name."""

    return EXPLANATION_TEMPLATES.get(name, EXPLANATION_TEMPLATES["generic"])


__all__ = ["EXPLANATION_TEMPLATES", "explanation_template"]
