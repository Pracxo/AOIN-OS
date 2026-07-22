from knowledge_intelligence_test_helpers import PROGRAM_ID, ROADMAP_TASKS, read_text


def test_program_charter_contains_objective_roles_rule_and_invariant():
    text = read_text("docs/knowledge-intelligence/program-charter.md")
    for term in (
        PROGRAM_ID,
        "Build a governed epistemic intelligence fabric",
        "Research acquisition",
        "Source provenance",
        "Claim extraction",
        "Claim verification",
        "Temporal and jurisdictional reasoning",
        "Domain specialist reasoning",
        "Verified knowledge memory",
        "Information is evidence.",
        (
            "No web page, user statement, engagement signal, model output, or repeated "
            "claim is automatically factual truth."
        ),
        "does not provide verified public internet research",
        "does not promote unverified web content into cognitive memory",
        "Non-Destructive Invariant",
    ):
        assert term in text


def test_roadmap_lists_aion_204_through_aion_220():
    text = read_text("docs/knowledge-intelligence/architecture-roadmap.md")
    for task in ROADMAP_TASKS:
        assert task in text
    assert "AION-204 authorizes only AION-205" in text
    assert "No later task is automatically authorized" in text
