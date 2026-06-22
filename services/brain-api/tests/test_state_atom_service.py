from __future__ import annotations

from aion_brain.contracts.temporal_state import StateAtomCreateRequest
from tests.situation_helpers import bundle


def test_state_atom_service_create_list_supersede_and_delete() -> None:
    services = bundle()
    atom = services.state_atom_service.create(
        StateAtomCreateRequest(
            source_type="event",
            source_id="event-1",
            predicate="current_status",
            value={"status": "active"},
            owner_scope=["workspace:main"],
        )
    )

    assert services.state_atom_service.get(atom.state_atom_id, ["workspace:main"]) is not None
    listed = services.state_atom_service.list_atoms(scope=["workspace:main"])
    assert listed[0].state_atom_id == atom.state_atom_id
    superseded = services.state_atom_service.supersede(atom.state_atom_id, ["workspace:main"])
    assert superseded.status == "superseded"
    deleted = services.state_atom_service.soft_delete(atom.state_atom_id, ["workspace:main"])
    assert deleted.deleted_at is not None
    assert services.state_atom_service.get(atom.state_atom_id, ["workspace:main"]) is None


def test_state_atom_scope_filtering() -> None:
    services = bundle()
    atom = services.state_atom_service.create(
        StateAtomCreateRequest(
            source_id="source-1",
            predicate="status",
            value={"status": "active"},
            owner_scope=["workspace:main"],
        )
    )

    assert services.state_atom_service.get(atom.state_atom_id, ["workspace:other"]) is None
