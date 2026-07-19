"""Immutable outcome ledger for AION-174 self-improvement."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.self_improvement import freeze_evidence_payload, utc_now
from aion_brain.self_improvement.canary_contracts import (
    CANARY_AUTHORIZATION_TRANSACTION_ID,
    ImprovementOutcome,
    OutcomeValue,
    safe_text,
)

LearningLedgerRecordKind = Literal[
    "proposal",
    "experiment",
    "approval",
    "pr",
    "merge",
    "canary",
    "rollback",
    "final_outcome",
    "survival_review",
]


class LearningLedgerRecord(BaseModel):
    """Synthetic data-only record for improvement learning outcomes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = CANARY_AUTHORIZATION_TRANSACTION_ID
    record_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    record_kind: LearningLedgerRecordKind
    outcome_value: OutcomeValue | None = None
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict, validate_default=True)
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("record_id", "proposal_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        return safe_text(value, "learning ledger text")

    @field_validator("evidence_refs")
    @classmethod
    def evidence_refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            safe_text(item, "learning ledger evidence ref")
        return value

    @field_validator("metadata", mode="before")
    @classmethod
    def metadata_must_be_frozen(cls, value: Any) -> dict[str, Any]:
        if value is None:
            value = {}
        frozen = freeze_evidence_payload(value)
        if not isinstance(frozen, dict):
            raise ValueError("metadata must be a mapping")
        return frozen

    @model_validator(mode="after")
    def record_must_be_data_only(self) -> LearningLedgerRecord:
        if self.authorization_transaction_id != CANARY_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("learning ledger must use the AION-173 authorization")
        object.__setattr__(self, "metadata", freeze_evidence_payload(self.metadata))
        return self


class ImprovementOutcomeLedger(BaseModel):
    """Append-only immutable outcome ledger."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ledger_id: str = Field(min_length=1)
    records: tuple[LearningLedgerRecord, ...] = Field(default_factory=tuple)

    @field_validator("ledger_id")
    @classmethod
    def ledger_id_must_be_safe(cls, value: str) -> str:
        return safe_text(value, "learning ledger id")

    def append(self, record: LearningLedgerRecord) -> ImprovementOutcomeLedger:
        """Return a new ledger with one appended record."""

        if any(existing.record_id == record.record_id for existing in self.records):
            raise ValueError("learning ledger record IDs must be unique")
        return self.model_copy(update={"records": (*self.records, record)})

    def record_outcome(self, outcome: ImprovementOutcome) -> ImprovementOutcomeLedger:
        """Append a final outcome record."""

        return self.append(
            LearningLedgerRecord(
                record_id=f"outcome-{outcome.outcome_id}",
                proposal_id=outcome.proposal_id,
                record_kind="final_outcome",
                outcome_value=outcome.outcome_value,
                evidence_refs=outcome.evidence_refs,
                metadata={
                    "canary_state": outcome.canary_state,
                    "review_window_days": outcome.review_window_days,
                    "promoted": outcome.promoted,
                    "rolled_back": outcome.rolled_back,
                },
            )
        )

    def outcomes(self) -> tuple[LearningLedgerRecord, ...]:
        """Return final outcome records only."""

        return tuple(record for record in self.records if record.record_kind == "final_outcome")


__all__ = [
    "ImprovementOutcomeLedger",
    "LearningLedgerRecord",
    "LearningLedgerRecordKind",
]
