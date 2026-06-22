"""Deterministic local secret scanner."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.security_baseline import (
    SecretScanFinding,
    SecurityScanRequest,
    SecurityScanRun,
)
from aion_brain.policy.base import PolicyAdapter
from aion_brain.security_baseline.repository import SecurityBaselineRepository
from aion_brain.versioning.compatibility import emit_versioning_telemetry

DEFAULT_SCAN_TARGETS = (
    "services/brain-api/src",
    "packages/aion-sdk-python/src",
    "docs",
    "scripts",
    "examples",
    ".github",
    "README.md",
    "AGENTS.md",
    "docker-compose.yml",
    ".env.example",
)
EXCLUDED_PARTS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "artifacts",
    ".aion_objects",
    ".aion_indexes",
    "dist",
    "build",
    ".venv",
    "venv",
}
TEXT_SUFFIXES = {
    ".env",
    ".example",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
IGNORE_COMMENT = "AION_SECRET_SCAN_IGNORE"
_API_KEY_ASSIGNMENT = re.compile(
    r"(?i)\b(api[_-]?key|apikey)\b\s*[:=]\s*[\"']?([A-Za-z0-9][A-Za-z0-9._~+/=-]{9,})"
)
_TOKEN_ASSIGNMENT = re.compile(
    r"(?i)\b(token|access_token|refresh_token)\b\s*[:=]\s*[\"']?"
    r"([A-Za-z0-9][A-Za-z0-9._~+/=-]{15,})"
)
_PASSWORD_ASSIGNMENT = re.compile(r"(?i)\b(password|passwd)\b\s*[:=]\s*[\"']?([^\"'\s]{8,})")
_BEARER = re.compile(r"(?i)\bbearer\s+([A-Za-z0-9._~+/=-]{16,})")
_PRIVATE_KEY = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
_RAW_SECRET_VALUE = re.compile(r"\b(sk-[A-Za-z0-9_-]{10,})\b")
_PLACEHOLDER_WORDS = {
    "",
    "changeme",
    "change_me",
    "example",
    "placeholder",
    "replace_me",
    "your_api_key",
    "your-token",
    "not-set",
    "none",
}


class SecretScanner:
    """Scan local files for obvious raw secret leakage."""

    def __init__(
        self,
        repository: SecurityBaselineRepository | None = None,
        policy_adapter: PolicyAdapter | None = None,
        *,
        settings: Settings | None = None,
        telemetry_service: object | None = None,
        root_dir: Path | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._settings = settings or get_settings()
        self._telemetry_service = telemetry_service
        self._root_dir = root_dir or Path(__file__).parents[5]

    def scan(self, request: SecurityScanRequest) -> SecurityScanRun:
        """Run a local deterministic scan and persist the result when possible."""
        self._authorize(request)
        scan_id = request.security_scan_id or f"security-scan-{uuid4().hex}"
        started = datetime.now(UTC)
        self._emit(
            "security_scan_started",
            scan_id,
            request.owner_scope,
            0.5,
            {"scan_type": request.scan_type},
        )
        if not self._settings.secret_scanner_enabled:
            run = SecurityScanRun(
                security_scan_id=scan_id,
                scan_type=request.scan_type,
                status="warning",
                owner_scope=request.owner_scope,
                checks=[
                    _check(
                        "secret_scanner_enabled",
                        "warning",
                        "Secret scanner is disabled by configuration.",
                    )
                ],
                findings=[],
                failures=[],
                warnings=[
                    _check(
                        "secret_scanner_disabled",
                        "warning",
                        "Secret scanner is disabled by configuration.",
                    )
                ],
                report={"external_calls": False, "scanner": "local"},
                created_by=request.created_by,
                created_at=started,
                completed_at=datetime.now(UTC),
            )
            return self._save(run)

        targets = self._resolve_targets(request)
        findings = self.scan_paths(targets, request, scan_id=scan_id)
        failures = [
            finding.model_dump(mode="json")
            for finding in findings
            if finding.severity in {"high", "critical"}
        ]
        warnings = [
            finding.model_dump(mode="json")
            for finding in findings
            if finding.severity in {"low", "medium"}
        ]
        status = "failed" if failures else ("warning" if warnings else "passed")
        checks = [
            _check(
                "local_secret_scan",
                status,
                "Local secret scan completed.",
                {"target_count": len(targets), "finding_count": len(findings)},
            )
        ]
        run = SecurityScanRun(
            security_scan_id=scan_id,
            scan_type=request.scan_type,
            status=cast(Any, status),
            owner_scope=request.owner_scope,
            checks=checks,
            findings=findings,
            failures=failures,
            warnings=warnings,
            report={
                "external_calls": False,
                "scanner": "local",
                "target_count": len(targets),
                "finding_count": len(findings),
            },
            created_by=request.created_by,
            created_at=started,
            completed_at=datetime.now(UTC),
        )
        saved = self._save(run)
        self._emit(
            "security_scan_completed",
            saved.security_scan_id,
            saved.owner_scope,
            0.8 if saved.status == "passed" else 1.0,
            {"status": saved.status, "finding_count": len(saved.findings)},
        )
        for finding in saved.findings:
            self._emit(
                "security_finding_detected",
                finding.finding_id,
                saved.owner_scope,
                1.0 if finding.severity in {"high", "critical"} else 0.6,
                {"finding_type": finding.finding_type, "severity": finding.severity},
            )
        return saved

    def scan_paths(
        self,
        paths: list[Path],
        request: SecurityScanRequest,
        *,
        scan_id: str | None = None,
    ) -> list[SecretScanFinding]:
        """Scan explicit paths and return redacted findings."""
        effective_scan_id = scan_id or request.security_scan_id or f"security-scan-{uuid4().hex}"
        findings: list[SecretScanFinding] = []
        max_bytes = request.max_file_size_mb * 1024 * 1024
        for target in paths:
            for path in _iter_files(target):
                if _excluded(path) or not _looks_textual(path):
                    continue
                if not request.include_docs and path.suffix == ".md":
                    continue
                if not request.include_examples and "examples" in path.parts:
                    continue
                if not request.include_tests and "tests" in path.parts:
                    continue
                try:
                    if path.stat().st_size > max_bytes:
                        continue
                except OSError:
                    continue
                findings.extend(self._scan_file(path, request, effective_scan_id))
        return findings

    def _scan_file(
        self,
        path: Path,
        request: SecurityScanRequest,
        scan_id: str,
    ) -> list[SecretScanFinding]:
        relative = _relative_path(path, self._root_dir)
        findings: list[SecretScanFinding] = []
        if _is_env_file(path):
            findings.append(
                _finding(
                    scan_id,
                    relative,
                    None,
                    "env_file",
                    "high",
                    f"{path.name}: [redacted]",
                    "raw environment file detected",
                )
            )
        if _is_credential_named(path):
            findings.append(
                _finding(
                    scan_id,
                    relative,
                    None,
                    "credential_file",
                    "medium",
                    f"{path.name}: [redacted]",
                    "credential-named file detected",
                )
            )
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            return findings
        for lineno, line in enumerate(lines, start=1):
            if request.metadata.get("allow_ignore_comments", True) and IGNORE_COMMENT in line:
                continue
            if self._settings.security_allow_secret_scan_ignore_comments and IGNORE_COMMENT in line:
                continue
            findings.extend(_line_findings(scan_id, relative, lineno, line, path.name))
        return findings

    def _resolve_targets(self, request: SecurityScanRequest) -> list[Path]:
        raw_paths = request.paths or list(DEFAULT_SCAN_TARGETS)
        targets: list[Path] = []
        for item in raw_paths:
            path = Path(item)
            if not path.is_absolute():
                path = self._root_dir / path
            if path.exists():
                targets.append(path)
        return targets

    def _save(self, run: SecurityScanRun) -> SecurityScanRun:
        if self._repository is None:
            return run
        return self._repository.save_scan(run)

    def _authorize(self, request: SecurityScanRequest) -> None:
        if self._policy_adapter is None:
            return
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"security.scan.run-{uuid4().hex}",
                trace_id=None,
                actor_id=request.created_by,
                workspace_id=None,
                action_type="security.scan.run",
                resource_type="security_scan",
                resource_id=request.security_scan_id,
                risk_level="medium",
                approval_present=True,
                requested_permissions=["security.scan.run"],
                security_scope=request.owner_scope,
                context={"scan_type": request.scan_type, **request.metadata},
            )
        )
        if not decision.allow:
            raise AIONPolicyDeniedException(decision.reason)

    def _emit(
        self,
        event_type: str,
        node_id: str,
        scope: list[str],
        intensity: float,
        payload: dict[str, Any],
    ) -> None:
        node_type = "finding" if event_type == "security_finding_detected" else "security"
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type=node_type,
            node_id=node_id,
            intensity=intensity,
            scope=scope,
            payload=payload,
        )


def _line_findings(
    scan_id: str,
    relative: str,
    lineno: int,
    line: str,
    file_name: str,
) -> list[SecretScanFinding]:
    findings: list[SecretScanFinding] = []
    patterns = [
        ("api_key_like", "high", _API_KEY_ASSIGNMENT),
        ("bearer_token_like", "high", _BEARER),
        ("private_key_like", "critical", _PRIVATE_KEY),
        ("password_like", "high", _PASSWORD_ASSIGNMENT),
        ("api_key_like", "high", _RAW_SECRET_VALUE),
        ("api_key_like", "high", _TOKEN_ASSIGNMENT),
    ]
    for finding_type, severity, pattern in patterns:
        for match in pattern.finditer(line):
            if finding_type == "private_key_like" and _is_detector_pattern_line(relative, line):
                continue
            secret = match.group(match.lastindex or 0)
            if _placeholder(secret) or (file_name == ".env.example" and _placeholder(secret)):
                continue
            findings.append(
                _finding(
                    scan_id,
                    relative,
                    lineno,
                    finding_type,
                    severity,
                    _redact_match(line, secret),
                    None,
                )
            )
    return findings


def _finding(
    scan_id: str,
    file_path: str,
    line_number: int | None,
    finding_type: str,
    severity: str,
    redacted_match: str,
    reason: str | None,
) -> SecretScanFinding:
    return SecretScanFinding(
        finding_id=f"secret-finding-{uuid4().hex}",
        scan_id=scan_id,
        file_path=file_path,
        line_number=line_number,
        finding_type=cast(Any, finding_type),
        severity=cast(Any, severity),
        redacted_match=redacted_match,
        status="open",
        reason=reason,
        created_at=datetime.now(UTC),
    )


def _check(
    name: str,
    status: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "message": message,
        "details": details or {},
    }


def _iter_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if path.is_dir():
        return [child for child in path.rglob("*") if child.is_file()]
    return []


def _excluded(path: Path) -> bool:
    return bool(set(path.parts) & EXCLUDED_PARTS)


def _looks_textual(path: Path) -> bool:
    return path.name in {
        ".env",
        ".env.example",
        "README.md",
        "AGENTS.md",
        "docker-compose.yml",
    } or (path.suffix in TEXT_SUFFIXES)


def _is_env_file(path: Path) -> bool:
    return path.name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example")


def _is_credential_named(path: Path) -> bool:
    lowered = path.name.lower()
    has_credential_name = any(name in lowered for name in ("credential", "credentials", "secret"))
    config_like_suffixes = {".env", ".json", ".yaml", ".yml", ".toml", ".ini", ".txt"}
    return (
        has_credential_name
        and path.name != ".env.example"
        and (path.suffix.lower() in config_like_suffixes or path.name.startswith(".env."))
    )


def _is_detector_pattern_line(relative: str, line: str) -> bool:
    lowered_path = relative.lower()
    if not lowered_path.endswith(("redaction.py", "secret_scanner.py")):
        return False
    return "private key" in line.lower() and ("re.compile" in line or ".*?" in line)


def _placeholder(value: str) -> bool:
    clean = value.strip().strip("\"'").lower()
    if clean in _PLACEHOLDER_WORDS or clean.startswith("${") or clean.startswith("your_"):
        return True
    return any(word in clean for word in ("example", "placeholder", "changeme", "replace"))


def _redact_match(line: str, secret: str) -> str:
    redacted = _redact(secret)
    return line.replace(secret, redacted).strip()[:240]


def _redact(value: str) -> str:
    clean = value.strip().strip("\"'")
    if len(clean) <= 8:
        return "[redacted]"
    return f"{clean[:4]}***{clean[-4:]}"


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
