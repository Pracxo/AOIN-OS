from __future__ import annotations

from aion_brain.situations.normalizer import SituationNormalizer


def test_normalizer_maps_generic_sources_to_state_atoms() -> None:
    atoms = SituationNormalizer().normalize_sources(
        source_refs=[
            {
                "source_type": "dialogue",
                "source_id": "message-1",
                "status": "active",
                "title": "Message",
            }
        ],
        owner_scope=["workspace:main"],
        trace_id="trace-1",
    )

    assert atoms[0].atom_type == "dialogue_state"
    assert atoms[0].status == "current"
    assert atoms[0].source_id == "message-1"
