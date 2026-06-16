"""Evidence link helpers."""

from aion_brain.contracts.evidence import EvidenceLink


def has_contradicting_link(links: list[EvidenceLink]) -> bool:
    """Return true when selected evidence explicitly contradicts a target."""
    return any(link.relation_type == "contradicts" for link in links)


def unique_evidence_refs(links: list[EvidenceLink]) -> list[str]:
    """Return stable unique evidence IDs from links."""
    seen: set[str] = set()
    refs: list[str] = []
    for link in links:
        if link.evidence_id not in seen:
            seen.add(link.evidence_id)
            refs.append(link.evidence_id)
    return refs
