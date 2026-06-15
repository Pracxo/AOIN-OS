"""Module developer kit contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.capabilities import CapabilityManifest

ModulePackageStatus = Literal["draft", "submitted", "certified", "rejected", "disabled"]
CertificationCheckCategory = Literal[
    "schema",
    "risk",
    "permissions",
    "memory_scope",
    "policy",
    "autonomy",
    "runtime",
    "dry_run",
    "audit",
    "documentation",
    "boundary",
]
CertificationCheckStatus = Literal["passed", "failed", "warning", "skipped"]
CertificationSeverity = Literal["low", "medium", "high", "critical"]
CertificationStatus = Literal["passed", "failed", "warning"]
ContractTestType = Literal[
    "schema_validation",
    "dry_run_invocation",
    "policy_gate",
    "risk_gate",
    "autonomy_gate",
    "audit_trace",
    "error_contract",
]
ContractTestStatus = Literal["active", "disabled"]
ScaffoldOutputFormat = Literal["files", "json"]

SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
}
DOMAIN_PREFIXES = {
    "finance",
    "trading",
    "legal",
    "healthcare",
    "hr",
    "procurement",
    "it",
    "security",
    "medical",
    "payments",
}
ALLOWED_MODULE_PREFIXES = ("test", "generic", "aion.example", "aion.internal")


class ModulePackage(BaseModel):
    """A submitted module package and its governance manifest."""

    model_config = ConfigDict(extra="forbid")

    module_package_id: str
    module_id: str
    version: str
    package_name: str
    display_name: str
    description: str
    status: ModulePackageStatus
    manifest: CapabilityManifest
    compatibility: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("module_id")
    @classmethod
    def validate_module_id(cls, value: str) -> str:
        """Require generic module identifiers."""
        return validate_module_id(value)

    @field_validator("version", "package_name", "display_name", "description")
    @classmethod
    def text_cannot_be_empty(cls, value: str) -> str:
        """Reject blank package text."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value

    @field_validator("metadata", "compatibility")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like package metadata."""
        reject_secret_like_keys(value)
        return value


class ModulePackageCreateRequest(BaseModel):
    """Request to submit or draft a module package."""

    model_config = ConfigDict(extra="forbid")

    module_package_id: str | None = None
    module_id: str
    version: str
    package_name: str
    display_name: str
    description: str
    manifest: CapabilityManifest
    compatibility: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    submit: bool = True

    @field_validator("module_id")
    @classmethod
    def validate_module_id(cls, value: str) -> str:
        return validate_module_id(value)

    @field_validator("version", "package_name", "display_name", "description")
    @classmethod
    def text_cannot_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value

    @field_validator("metadata", "compatibility")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class CapabilityCertificationCheck(BaseModel):
    """One deterministic certification check."""

    model_config = ConfigDict(extra="forbid")

    check_id: str
    name: str
    category: CertificationCheckCategory
    status: CertificationCheckStatus
    severity: CertificationSeverity
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class CapabilityCertification(BaseModel):
    """Certification result for one capability."""

    model_config = ConfigDict(extra="forbid")

    certification_id: str
    module_package_id: str
    module_id: str
    version: str
    capability_id: str
    status: CertificationStatus
    score: float = Field(ge=0.0, le=1.0)
    checks: list[CapabilityCertificationCheck]
    failures: list[dict[str, Any]]
    warnings: list[dict[str, Any]]
    certified_by: str | None = None
    created_at: datetime | None = None


class ModuleCertificationRun(BaseModel):
    """Certification run summary for one module package."""

    model_config = ConfigDict(extra="forbid")

    certification_run_id: str
    module_package_id: str
    module_id: str
    version: str
    status: CertificationStatus
    total_checks: int = Field(ge=0)
    passed_checks: int = Field(ge=0)
    failed_checks: int = Field(ge=0)
    warning_checks: int = Field(ge=0)
    score: float = Field(ge=0.0, le=1.0)
    report: dict[str, Any]
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class ModuleCertificationRequest(BaseModel):
    """Request to run deterministic module certification."""

    model_config = ConfigDict(extra="forbid")

    module_package_id: str
    dry_run: bool = True
    include_policy_check: bool = True
    include_autonomy_check: bool = True
    include_runtime_check: bool = True
    include_dry_run_invocation: bool = True
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)


class ModuleCompatibilityReport(BaseModel):
    """Compatibility report for one module package."""

    model_config = ConfigDict(extra="forbid")

    report_id: str
    module_id: str
    version: str
    compatible: bool
    aion_version: str
    required_aion_version: str | None = None
    issues: list[dict[str, Any]]
    warnings: list[dict[str, Any]]
    checked_at: datetime


class ModuleContractTestCase(BaseModel):
    """Static contract test case for a module package."""

    model_config = ConfigDict(extra="forbid")

    test_case_id: str
    module_package_id: str | None = None
    capability_id: str | None = None
    test_type: ContractTestType
    name: str
    description: str
    input: dict[str, Any]
    expected: dict[str, Any]
    status: ContractTestStatus
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("metadata", "input", "expected")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class ModuleScaffoldRequest(BaseModel):
    """Request to generate generic module package starter files."""

    model_config = ConfigDict(extra="forbid")

    module_id: str
    package_name: str
    capability_count: int = Field(default=1, ge=1, le=10)
    output_format: ScaffoldOutputFormat = "files"
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("module_id")
    @classmethod
    def validate_module_id(cls, value: str) -> str:
        return validate_module_id(value)

    @field_validator("package_name")
    @classmethod
    def package_name_cannot_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("package_name cannot be empty")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class ModuleScaffold(BaseModel):
    """Generated generic module scaffold."""

    model_config = ConfigDict(extra="forbid")

    module_id: str
    package_name: str
    files: dict[str, str]
    manifest: CapabilityManifest
    readme: str
    created_at: datetime


def validate_module_id(value: str) -> str:
    """Validate a module id against v0.1 generic package rules."""
    stripped = value.strip()
    if not stripped:
        raise ValueError("module_id cannot be empty")
    first_segment = stripped.split(".", maxsplit=1)[0].lower()
    if first_segment in DOMAIN_PREFIXES:
        raise ValueError("module_id must not use a domain-specific prefix")
    if not any(stripped.startswith(prefix) for prefix in ALLOWED_MODULE_PREFIXES):
        raise ValueError("module_id must use a generic v0.1 prefix")
    return stripped


def reject_secret_like_keys(value: object) -> None:
    """Reject secret-like keys in nested payloads."""
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in SECRET_KEY_PARTS):
                raise ValueError("metadata must not contain secret-like keys")
            reject_secret_like_keys(nested)
    elif isinstance(value, list):
        for item in value:
            reject_secret_like_keys(item)

