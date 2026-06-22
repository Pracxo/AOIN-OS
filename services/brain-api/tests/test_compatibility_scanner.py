"""Compatibility scanner tests."""

from __future__ import annotations

from aion_brain.contract_registry.compatibility import CompatibilityScanner
from aion_brain.contract_registry.migration_notes import MigrationNoteService
from aion_brain.contracts.compatibility import CompatibilityScanRequest
from tests.contract_registry_helpers import (
    SCOPE,
    AllowPolicy,
    FakeRuleService,
    FakeSnapshotService,
    contract_record,
    interface_record,
    repository,
    schema,
    snapshot,
)


def test_compatibility_scanner_detects_removed_route() -> None:
    scan = _scan(
        snapshot("baseline", interfaces=[interface_record()]),
        snapshot("candidate", interfaces=[]),
    )

    assert {finding.finding_type for finding in scan.findings} == {"removed_route"}
    assert scan.breaking_count == 1


def test_compatibility_scanner_detects_removed_sdk_method_and_policy_action() -> None:
    baseline = snapshot(
        "baseline",
        interfaces=[
            interface_record(
                "sdk.echo.ping",
                interface_type="sdk_method",
                path=None,
                method=None,
                source_system="aion_sdk",
                visibility="sdk",
            ),
            interface_record(
                "policy.contract_registry.resource.read",
                interface_type="policy_action",
                path=None,
                method=None,
                descriptor={"action": "contract_registry.resource.read"},
                source_system="opa",
            ),
        ],
    )
    candidate = snapshot("candidate", interfaces=[])

    scan = _scan(baseline, candidate)

    assert {finding.finding_type for finding in scan.findings} >= {
        "removed_sdk_method",
        "removed_policy_action",
    }


def test_compatibility_scanner_detects_added_required_field() -> None:
    old = contract_record(schema_payload=schema(required=[]))
    new = contract_record(schema_payload=schema(required=["name"]))

    scan = _scan(snapshot("baseline", contracts=[old]), snapshot("candidate", contracts=[new]))

    assert scan.findings[0].finding_type == "required_field_added"
    assert scan.findings[0].breaking is True


def test_compatibility_scanner_treats_added_optional_field_as_non_breaking() -> None:
    old = contract_record(schema_payload=schema(required=[]))
    new_schema = schema(
        required=[],
        extra={"properties": {"name": {"type": "string"}, "summary": {"type": "string"}}},
    )
    new = contract_record(schema_payload=new_schema)

    scan = _scan(snapshot("baseline", contracts=[old]), snapshot("candidate", contracts=[new]))

    assert scan.findings == []
    assert scan.breaking_count == 0


def test_compatibility_scanner_detects_missing_bindings() -> None:
    route = interface_record(
        "GET /brain/contracts/example",
        path="/brain/contracts/example",
        descriptor={"path": "/brain/contracts/example", "method": "GET"},
    )

    scan = _scan(
        snapshot("baseline", interfaces=[route]), snapshot("candidate", interfaces=[route])
    )

    assert {finding.finding_type for finding in scan.findings} >= {
        "missing_sdk_binding",
        "missing_cli_binding",
    }


def test_compatibility_scanner_dry_run_persists_no_findings() -> None:
    repo = repository()
    scanner = _scanner(
        repo,
        snapshot("baseline", interfaces=[interface_record()]),
        snapshot("candidate", interfaces=[]),
    )

    scan = scanner.scan(
        CompatibilityScanRequest(
            mode="dry_run",
            owner_scope=SCOPE,
            baseline_snapshot_id="baseline",
            candidate_snapshot_id="candidate",
        )
    )

    assert scan.findings_count == 1
    assert repo.list_findings() == []


def test_compatibility_scanner_controlled_persists_findings_and_notes_only() -> None:
    repo = repository()
    scanner = _scanner(
        repo,
        snapshot("baseline", interfaces=[interface_record()]),
        snapshot("candidate", interfaces=[]),
    )

    scan = scanner.scan(
        CompatibilityScanRequest(
            mode="controlled",
            owner_scope=SCOPE,
            baseline_snapshot_id="baseline",
            candidate_snapshot_id="candidate",
        )
    )

    assert scan.findings_count == 1
    assert repo.list_findings()[0].finding_type == "removed_route"
    assert repo.list_migration_notes()[0].finding_id == repo.list_findings()[0].drift_finding_id
    assert scan.result["source_mutated"] is False
    assert scan.result["code_generated"] is False


def _scan(baseline, candidate):
    repo = repository()
    return _scanner(repo, baseline, candidate).scan(
        CompatibilityScanRequest(
            owner_scope=SCOPE,
            baseline_snapshot_id=baseline.contract_snapshot_id,
            candidate_snapshot_id=candidate.contract_snapshot_id,
        )
    )


def _scanner(repo, baseline, candidate) -> CompatibilityScanner:
    return CompatibilityScanner(
        repo,
        FakeSnapshotService(baseline, candidate),
        FakeRuleService(),
        AllowPolicy(),
        migration_note_service=MigrationNoteService(repo, AllowPolicy()),
    )
