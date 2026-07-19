"""Sandbox evidence for approval-bound rewrite candidates."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text
from aion_brain.contracts.self_improvement import utc_now
from aion_brain.self_improvement.diff_hash import canonical_json_hash
from aion_brain.self_improvement.worktree import REWRITE_AUTHORIZATION_TRANSACTION_ID

SandboxGateName = Literal[
    "regression_test",
    "focused_tests",
    "type_checks",
    "lint",
    "security_gates",
    "benchmark_comparison",
    "holdout_evaluation",
    "git_diff_check",
]

REQUIRED_SANDBOX_GATES: tuple[SandboxGateName, ...] = (
    "regression_test",
    "focused_tests",
    "type_checks",
    "lint",
    "security_gates",
    "benchmark_comparison",
    "holdout_evaluation",
    "git_diff_check",
)


class SandboxCommand(BaseModel):
    """One required command or synthetic gate inside an isolated worktree."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    gate_name: SandboxGateName
    command: tuple[str, ...] = Field(min_length=1)
    cwd: Path | None = None
    required: bool = True

    @field_validator("command")
    @classmethod
    def command_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "rewrite sandbox command")
        return value


class SandboxCommandResult(BaseModel):
    """Observed result for one sandbox gate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    gate_name: SandboxGateName
    command: tuple[str, ...] = Field(min_length=1)
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    evidence_ref: str | None = None

    @field_validator("stdout", "stderr")
    @classmethod
    def output_must_be_public(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "rewrite sandbox output")
        return value


class SandboxRunEvidence(BaseModel):
    """Evidence bundle assembled after all sandbox gates complete."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = REWRITE_AUTHORIZATION_TRANSACTION_ID
    proposal_id: str = Field(min_length=1)
    worktree_path: Path
    command_results: tuple[SandboxCommandResult, ...] = Field(min_length=1)
    benchmark_fingerprint: str
    holdout_fingerprint: str
    all_required_pass: bool
    evidence_bundle_id: str = Field(min_length=1)
    created_at: datetime

    @model_validator(mode="after")
    def evidence_must_include_all_required_gates(self) -> SandboxRunEvidence:
        if self.authorization_transaction_id != REWRITE_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("sandbox evidence must use the AION-171 rewrite authorization")
        observed = {result.gate_name for result in self.command_results}
        missing = set(REQUIRED_SANDBOX_GATES) - observed
        if missing:
            raise ValueError(f"missing sandbox gates: {sorted(missing)}")
        expected_pass = all(
            result.exit_code == 0
            for result in self.command_results
            if result.gate_name in REQUIRED_SANDBOX_GATES
        )
        if self.all_required_pass != expected_pass:
            raise ValueError("all_required_pass must reflect sandbox gate exits")
        return self


class SandboxRunner(Protocol):
    """Protocol seam for explicitly configured sandbox executors."""

    runner_id: str

    def run(self, command: SandboxCommand) -> SandboxCommandResult:
        """Run one sandbox command."""


class DisabledSandboxRunner:
    """Fail-closed runtime default; no sandbox execution is performed."""

    runner_id = "disabled-sandbox-runner"

    def run(self, command: SandboxCommand) -> SandboxCommandResult:  # noqa: ARG002
        raise RuntimeError("self-improvement sandbox execution is disabled")


class DeterministicTestSandboxRunner:
    """Deterministic test double that returns configured gate exits."""

    runner_id = "deterministic-test-sandbox-runner"

    def __init__(self, exit_codes: Mapping[SandboxGateName, int] | None = None) -> None:
        self._exit_codes = dict(exit_codes or {})

    def run(self, command: SandboxCommand) -> SandboxCommandResult:
        exit_code = self._exit_codes.get(command.gate_name, 0)
        return SandboxCommandResult(
            gate_name=command.gate_name,
            command=command.command,
            exit_code=exit_code,
            stdout=f"{command.gate_name} pass" if exit_code == 0 else "",
            stderr="" if exit_code == 0 else f"{command.gate_name} failed",
            evidence_ref=f"sandbox:{command.gate_name}",
        )


def build_sandbox_evidence(
    *,
    proposal_id: str,
    worktree_path: Path,
    command_results: tuple[SandboxCommandResult, ...],
) -> SandboxRunEvidence:
    """Build immutable sandbox evidence and fingerprints."""

    benchmark_fingerprint = canonical_json_hash(
        {
            "proposal_id": proposal_id,
            "gate": "benchmark_comparison",
            "exit_code": _exit_code_for(command_results, "benchmark_comparison"),
        }
    )
    holdout_fingerprint = canonical_json_hash(
        {
            "proposal_id": proposal_id,
            "gate": "holdout_evaluation",
            "exit_code": _exit_code_for(command_results, "holdout_evaluation"),
        }
    )
    return SandboxRunEvidence(
        proposal_id=proposal_id,
        worktree_path=worktree_path,
        command_results=command_results,
        benchmark_fingerprint=benchmark_fingerprint,
        holdout_fingerprint=holdout_fingerprint,
        all_required_pass=all(result.exit_code == 0 for result in command_results),
        evidence_bundle_id=f"{proposal_id}:sandbox:{benchmark_fingerprint[:12]}",
        created_at=utc_now(),
    )


def required_sandbox_commands() -> tuple[SandboxCommand, ...]:
    """Return the required rewrite gates as command specifications."""

    return tuple(
        SandboxCommand(gate_name=gate, command=("aion-self-improvement-gate", gate))
        for gate in REQUIRED_SANDBOX_GATES
    )


def _exit_code_for(
    command_results: tuple[SandboxCommandResult, ...],
    gate_name: SandboxGateName,
) -> int:
    for result in command_results:
        if result.gate_name == gate_name:
            return result.exit_code
    raise ValueError(f"missing sandbox gate: {gate_name}")


__all__ = [
    "REQUIRED_SANDBOX_GATES",
    "DeterministicTestSandboxRunner",
    "DisabledSandboxRunner",
    "SandboxCommand",
    "SandboxCommandResult",
    "SandboxGateName",
    "SandboxRunEvidence",
    "SandboxRunner",
    "build_sandbox_evidence",
    "required_sandbox_commands",
]
