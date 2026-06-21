"""Model output repository tests."""

from __future__ import annotations

from aion_brain.contracts.model_outputs import ModelOutputRecord
from aion_brain.contracts.output_governance import ModelOutputQuery
from tests.model_outputs_fakes import repository


def test_repository_persists_and_queries_outputs() -> None:
    repo = repository()
    repo.save_output(
        ModelOutputRecord(
            model_output_id="output-1",
            trace_id="trace-1",
            status="received",
            output_type="text",
            raw_output_hash="hash",
            redacted_output="safe output",
            output_redacted=False,
            token_estimate=3,
            char_count=11,
            metadata={"owner_scope": ["workspace:main"]},
        )
    )

    fetched = repo.get_output("output-1")
    result = repo.query(ModelOutputQuery(scope=["workspace:main"], trace_id="trace-1"))

    assert fetched is not None
    assert fetched.redacted_output == "safe output"
    assert result.total_count == 1


def test_repository_soft_delete_excludes_default_query() -> None:
    repo = repository()
    repo.save_output(
        ModelOutputRecord(
            model_output_id="output-1",
            status="received",
            output_type="text",
            raw_output_hash="hash",
            redacted_output="safe output",
            output_redacted=False,
            token_estimate=3,
            char_count=11,
            metadata={"owner_scope": ["workspace:main"]},
        )
    )

    assert repo.soft_delete_output("output-1") is True

    result = repo.query(ModelOutputQuery(scope=["workspace:main"]))
    archived = repo.query(ModelOutputQuery(scope=["workspace:main"], include_deleted=True))

    assert result.total_count == 0
    assert archived.outputs[0].status == "archived"
