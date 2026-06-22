"""Migration note service tests."""

from __future__ import annotations

from aion_brain.contract_registry.migration_notes import MigrationNoteService
from tests.contract_registry_helpers import SCOPE, AllowPolicy, drift_finding, repository


def test_migration_note_service_creates_and_archives_note() -> None:
    service = MigrationNoteService(repository(), AllowPolicy())

    note = service.create_from_finding(drift_finding(), SCOPE, created_by="tester")
    archived = service.archive_note(note.migration_note_id, "tester", "done")

    assert note.note_type == "breaking_change"
    assert service.list_notes(SCOPE)[0].migration_note_id == note.migration_note_id
    assert archived.status == "archived"
