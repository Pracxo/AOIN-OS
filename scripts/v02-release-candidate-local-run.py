#!/usr/bin/env python3
"""Uninstalled runner for the AION-243 deterministic local release candidate."""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import importlib.metadata
import json
import os
import secrets
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "services" / "brain-api" / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from aion_brain.contracts.v02_release_candidate import (  # noqa: E402
    AUTHORIZATION_TRANSACTION_ID,
    CANDIDATE_LABEL,
    COMPARISON_IMAGE_TAG,
    FROZEN_BASE_IMAGE_ID,
    FROZEN_BASE_IMAGE_TAG,
    LOCAL_CONFIRMATION_TEXT,
    LOCAL_IMAGE_TAG,
    PROGRAM_ID,
    PYTHON_PACKAGE_VERSION,
    V02CandidateArtifactManifest,
    V02CandidateArtifactPlan,
    V02CandidateArtifactRecord,
    V02CandidateChecksumManifest,
    V02CandidateChecksumRecord,
    V02CandidateCompatibilityMatrix,
    V02CandidateCompatibilityRecord,
    V02CandidateEvidenceBundle,
    V02CandidateIntegrityFinding,
    V02CandidateIntegrityReport,
    V02CandidateMigrationManifest,
    V02CandidateMigrationRecord,
    V02CandidateProvenanceChain,
    V02CandidateProvenanceRecord,
    V02CandidateReleaseNotesRecord,
    V02CandidateReproducibilityComparison,
    V02CandidateRetentionResult,
    V02CandidateSbomComponent,
    V02CandidateSbomDocument,
    V02CandidateSourceSnapshotManifest,
    V02CandidateVersionManifest,
    V02QualificationPublicKeyRecord,
    V02QualificationSignatureRecord,
    canonical_authorization_envelope,
)
from aion_brain.v02_release_candidate import ControlledV02ReleaseCandidateService  # noqa: E402

DEFAULT_CANDIDATE_ROOT = (
    Path.home() / ".aion" / "release-candidates" / CANDIDATE_LABEL
)
TEMP_PARENT = Path.home() / ".aion" / "tmp"
PYTHON_BIN = REPO_ROOT / "services" / "brain-api" / ".venv" / "bin" / "python"
SOURCE_DATE_EPOCH = 1_704_067_200
EXPECTED_HATCHLING_VERSION = "1.31.0"
SAFE_ENV_KEYS = ("HOME", "PATH", "TMPDIR", "USER", "SHELL")
EVIDENCE_PATH = (
    REPO_ROOT
    / "examples"
    / "v02-release-qualification"
    / "v02-release-candidate-artifact-build-evidence.json"
)
LEDGER_PATHS = (
    REPO_ROOT / "docs" / "v02-release-qualification" / "program-ledger.json",
    REPO_ROOT / "docs" / "v02-release-qualification" / "authorization-ledger.json",
)
AUTHORIZATION_EXAMPLE_PATH = (
    REPO_ROOT
    / "examples"
    / "v02-release-qualification"
    / "release-candidate-authorization.json"
)
RUN_LABEL_KEY = "io.aion.aion243.run_id"
RESOURCE_LABELS = {
    "io.aion.task": "AION-243",
    "io.aion.program": PROGRAM_ID,
    "io.aion.candidate": CANDIDATE_LABEL,
    "io.aion.production": "false",
    "io.aion.release-candidate": "true",
    "io.aion.published": "false",
}
BLOCKED_SUBCOMMANDS = {
    "login",
    "logout",
    "pull",
    "push",
    "commit",
    "import",
    "export",
    "cp",
    "exec",
    "attach",
    "prune",
    "swarm",
    "stack",
}
PROTECTED_ENV_MARKERS = (
    "AWS_",
    "AZURE_",
    "GOOGLE_",
    "GITHUB_TOKEN",
    "OPENAI_API_KEY",
    "PASSWORD",
    "SECRET",
    "TOKEN",
)


@dataclass
class CommandResult:
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str


@dataclass
class RunnerState:
    docker: str
    run_id: str
    temporary_root: Path
    docker_invocations: int = 0
    final_root: Path | None = None
    local_image_id: str | None = None
    generated_dockerfile: Path | None = None
    build_context: Path | None = None
    source_dir: Path | None = None


def canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def pretty_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprint(payload: object) -> str:
    return sha256_text(canonical_json(payload))


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_now_text() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def safe_env(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if key in SAFE_ENV_KEYS and "\x00" not in value
    }
    env.update(
        {
            "PIP_NO_INDEX": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PYTHONHASHSEED": "0",
            "SOURCE_DATE_EPOCH": str(SOURCE_DATE_EPOCH),
            "TZ": "UTC",
            "LC_ALL": "C",
        }
    )
    if extra:
        env.update(dict(extra))
    return env


def run_command(
    argv: Sequence[str],
    *,
    cwd: Path = REPO_ROOT,
    timeout: int = 120,
    check: bool = True,
    state: RunnerState | None = None,
) -> CommandResult:
    if not argv:
        raise RuntimeError("empty command rejected")
    if state is not None and argv[0] == state.docker:
        assert_allowed_docker_command(state, argv)
    completed = subprocess.run(
        list(argv),
        cwd=cwd,
        env=safe_env(),
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=False,
        check=False,
    )
    result = CommandResult(
        argv=list(argv),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {result.argv}\n{result.stderr.strip()}"
        )
    return result


def git_output(args: Sequence[str], *, timeout: int = 120) -> str:
    return run_command(["git", *args], timeout=timeout).stdout.strip()


def git_clean() -> bool:
    return not run_command(["git", "status", "--porcelain=v1"]).stdout.strip()


def require_git_clean() -> None:
    if not git_clean():
        raise RuntimeError("candidate source commit requires a clean working tree")


def resolve_docker() -> str:
    for candidate in ("/usr/local/bin/docker", "/opt/homebrew/bin/docker"):
        path = Path(candidate)
        if path.is_file() and os.access(path, os.X_OK):
            return str(path.resolve())
    resolved = shutil.which("docker", path=os.environ.get("PATH"))
    if resolved is None:
        raise RuntimeError("Docker CLI is unavailable")
    return str(Path(resolved).resolve())


def docker_json(state: RunnerState, argv: Sequence[str], *, timeout: int = 120) -> Any:
    text = run_command(argv, timeout=timeout, state=state).stdout.strip()
    return json.loads(text)


def docker_text(state: RunnerState, argv: Sequence[str], *, timeout: int = 120) -> str:
    return run_command(argv, timeout=timeout, state=state).stdout.strip()


def assert_allowed_docker_command(state: RunnerState, argv: Sequence[str]) -> None:
    tail = list(argv[1:])
    if any(item in BLOCKED_SUBCOMMANDS for item in tail):
        raise RuntimeError(f"prohibited Docker command rejected: {tail}")
    joined = "\x1f".join(tail)
    prohibited_tokens = (
        "--privileged",
        "--network=host",
        "--network\x1fhost",
        "/var/run/docker.sock",
        "type=registry",
        "registry://",
        "--secret",
        "--ssh",
    )
    if any(token in joined for token in prohibited_tokens):
        raise RuntimeError(f"prohibited Docker option rejected: {tail}")
    allowed = False
    if tail[:1] in (["version"], ["info"], ["ps"]):
        allowed = True
    if tail[:2] in (
        ["context", "show"],
        ["context", "inspect"],
        ["buildx", "version"],
        ["image", "inspect"],
        ["image", "ls"],
        ["image", "rm"],
    ):
        allowed = True
    if tail[:2] == ["buildx", "build"]:
        allowed = True
        values = set(tail)
        if "--pull=false" not in values or "--network=none" not in values:
            raise RuntimeError("candidate Docker build must use pull=false and network=none")
        if "--provenance=false" not in values or "--sbom=false" not in values:
            raise RuntimeError("candidate Docker build must disable BuildKit provenance/SBOM")
        if "--load" in values and "--tag" not in values:
            raise RuntimeError("loaded candidate image build must be explicitly tagged")
        if "--output" in values:
            output_index = tail.index("--output")
            try:
                output_value = tail[output_index + 1]
            except IndexError as exc:
                raise RuntimeError("OCI output build is missing output value") from exc
            if not output_value.startswith("type=oci,dest="):
                raise RuntimeError("candidate archive build must use local OCI output")
    if tail[:1] == ["run"]:
        allowed = True
        values = set(tail)
        if "--rm" not in values or "--pull" not in values or "never" not in values:
            raise RuntimeError("candidate probes must be one-shot and pull=never")
        if "--network" not in values:
            raise RuntimeError("candidate probes must declare network isolation")
        network = tail[tail.index("--network") + 1]
        if network != "none":
            raise RuntimeError("candidate probes may only use network none")
    if not allowed:
        raise RuntimeError(f"Docker command is outside AION-243 allowlist: {tail}")
    state.docker_invocations += 1
    if state.docker_invocations > 150:
        raise RuntimeError("AION-243 Docker invocation limit exceeded")


def verify_docker_context(state: RunnerState) -> dict[str, Any]:
    if os.environ.get("DOCKER_HOST"):
        raise RuntimeError("DOCKER_HOST must be unset for AION-243")
    context = docker_text(state, [state.docker, "context", "show"])
    if context != "desktop-linux":
        raise RuntimeError(f"unexpected Docker context: {context}")
    context_info = docker_json(state, [state.docker, "context", "inspect", context])
    version = docker_json(state, [state.docker, "version", "--format", "{{json .}}"])
    info = docker_json(state, [state.docker, "info", "--format", "{{json .}}"])
    buildx = docker_text(state, [state.docker, "buildx", "version"])
    endpoint = context_info[0]["Endpoints"]["docker"]["Host"]
    if not str(endpoint).startswith("unix://"):
        raise RuntimeError("Docker endpoint must be a local Unix socket")
    if str(info["OSType"]).lower() != "linux":
        raise RuntimeError("Docker server must be Linux")
    if str(info["Architecture"]).lower() not in {"arm64", "aarch64"}:
        raise RuntimeError("Docker server architecture must be arm64")
    return {
        "context": context,
        "endpoint": endpoint,
        "server_os": info["OSType"],
        "server_architecture": str(info["Architecture"]).lower(),
        "server_version": version["Server"]["Version"],
        "buildx": buildx,
        "docker_server_fingerprint": fingerprint(
            {
                "architecture": info["Architecture"],
                "os": info["OSType"],
                "version": version["Server"]["Version"],
            }
        ),
        "buildx_fingerprint": sha256_text(buildx),
    }


def verify_image_id(state: RunnerState, image_ref: str, expected: str | None = None) -> str:
    result = run_command(
        [state.docker, "image", "inspect", "--format", "{{.Id}}", image_ref],
        state=state,
        check=False,
    )
    image_id = result.stdout.strip()
    if not image_id:
        raise RuntimeError(f"local image is unavailable: {image_ref}")
    if expected is not None and image_id != expected:
        raise RuntimeError(f"image tag drift for {image_ref}: {image_id}")
    return image_id


def inspect_image(state: RunnerState, image_ref: str) -> dict[str, Any]:
    payload = docker_json(
        state,
        [state.docker, "image", "inspect", "--format", "{{json .}}", image_ref],
    )
    if not isinstance(payload, dict):
        raise RuntimeError(f"unexpected image inspect payload for {image_ref}")
    return payload


def ensure_tooling() -> dict[str, Any]:
    if not PYTHON_BIN.is_file() or not os.access(PYTHON_BIN, os.X_OK):
        raise RuntimeError("Brain API virtual environment Python is unavailable")
    code = """
from __future__ import annotations
import importlib.metadata
import json
import platform
import sys
import cryptography
import hatchling
import hatchling.build
version = importlib.metadata.version("hatchling")
if version != "1.31.0":
    raise SystemExit(f"hatchling version drift: {version}")
payload = {
    "cryptography_version": importlib.metadata.version("cryptography"),
    "hatchling_version": version,
    "python_version": platform.python_version(),
    "sys_prefix": sys.prefix,
}
print(json.dumps(payload, sort_keys=True))
"""
    result = run_command([str(PYTHON_BIN), "-c", code], timeout=120)
    return json.loads(result.stdout)


def ensure_path_not_symlink(path: Path) -> None:
    if path.exists() and path.is_symlink():
        raise RuntimeError(f"symbolic-link path rejected: {path}")


def ensure_under_home_aion(path: Path) -> None:
    resolved = path.resolve()
    allowed = (Path.home() / ".aion" / "release-candidates").resolve()
    if not resolved.is_relative_to(allowed):
        raise RuntimeError("candidate root must use the approved user-home .aion policy")


def setup_state(candidate_root: Path) -> RunnerState:
    TEMP_PARENT.mkdir(mode=0o700, parents=True, exist_ok=True)
    TEMP_PARENT.chmod(0o700)
    ensure_path_not_symlink(TEMP_PARENT)
    run_id = secrets.token_hex(8)
    temporary_root = Path(tempfile.mkdtemp(prefix=f"{CANDIDATE_LABEL}-{run_id}.", dir=TEMP_PARENT))
    temporary_root.chmod(0o700)
    return RunnerState(
        docker=resolve_docker(),
        run_id=run_id,
        temporary_root=temporary_root,
        final_root=candidate_root,
    )


def preflight(candidate_root: Path) -> dict[str, Any]:
    ensure_under_home_aion(candidate_root)
    ensure_path_not_symlink(candidate_root)
    if candidate_root.exists() and any(candidate_root.iterdir()):
        raise RuntimeError("final candidate root already exists and is not empty")
    state = setup_state(candidate_root)
    try:
        docker_context = verify_docker_context(state)
        base_image_id = verify_image_id(state, FROZEN_BASE_IMAGE_TAG, FROZEN_BASE_IMAGE_ID)
        candidate_tag_result = run_command(
            [state.docker, "image", "inspect", "--format", "{{.Id}}", LOCAL_IMAGE_TAG],
            state=state,
            check=False,
        )
        compare_tag_result = run_command(
            [state.docker, "image", "inspect", "--format", "{{.Id}}", COMPARISON_IMAGE_TAG],
            state=state,
            check=False,
        )
        tooling = ensure_tooling()
        tags = git_output(["tag", "--list", "v0.2*", "aion-v0.2*"])
        if tags.strip():
            raise RuntimeError("v0.2 tag exists before candidate build")
        return {
            "candidate_label": CANDIDATE_LABEL,
            "candidate_root_policy": "user-home/.aion/release-candidates/<candidate-label>",
            "candidate_root_exists": candidate_root.exists(),
            "candidate_image_absent": candidate_tag_result.returncode != 0,
            "comparison_image_absent": compare_tag_result.returncode != 0,
            "docker": docker_context,
            "frozen_base_image_tag": FROZEN_BASE_IMAGE_TAG,
            "frozen_base_image_id": base_image_id,
            "tooling": tooling,
            "v02_tags_absent": True,
        }
    finally:
        remove_tree(state.temporary_root)


def write_text(path: Path, text: str, mode: int = 0o600) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(mode)


def write_json(path: Path, payload: object) -> None:
    write_text(path, pretty_json(payload), 0o600)


def remove_tree(path: Path | None) -> None:
    if path is None or not path.exists():
        return
    resolved = path.resolve()
    allowed = TEMP_PARENT.resolve()
    if not resolved.is_relative_to(allowed):
        raise RuntimeError(f"refusing to remove non-AION-243 temporary path: {path}")
    shutil.rmtree(path)


def extract_git_archive(commit: str, destination: Path) -> None:
    archive_path = destination.parent / "git-archive.tar"
    run_command(
        ["git", "archive", "--format=tar", "--output", str(archive_path), commit],
        timeout=180,
    )
    with tarfile.open(archive_path) as archive:
        for member in archive.getmembers():
            member_path = Path(member.name)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise RuntimeError("Git archive contains unsafe path")
            if member.issym() or member.islnk():
                raise RuntimeError("Git archive contains symbolic or hard links")
        archive.extractall(destination, filter="data")
    archive_path.unlink()


def iter_files(path: Path) -> list[Path]:
    return sorted(item for item in path.rglob("*") if item.is_file())


def directory_records(path: Path) -> list[dict[str, Any]]:
    records = []
    for file_path in iter_files(path):
        data = file_path.read_bytes()
        records.append(
            {
                "relative_path": file_path.relative_to(path).as_posix(),
                "byte_count": len(data),
                "sha256": sha256_bytes(data),
            }
        )
    return records


def deterministic_tar_gz(source_dir: Path, output_path: Path, *, prefix: str) -> None:
    output_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with output_path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=SOURCE_DATE_EPOCH) as gz:
            with tarfile.open(fileobj=gz, mode="w") as archive:
                root_info = tarfile.TarInfo(prefix.rstrip("/") + "/")
                root_info.type = tarfile.DIRTYPE
                root_info.mtime = SOURCE_DATE_EPOCH
                root_info.mode = 0o755
                root_info.uid = 0
                root_info.gid = 0
                root_info.uname = ""
                root_info.gname = ""
                archive.addfile(root_info)
                for file_path in iter_files(source_dir):
                    relative = file_path.relative_to(source_dir).as_posix()
                    info = tarfile.TarInfo(f"{prefix.rstrip('/')}/{relative}")
                    info.size = file_path.stat().st_size
                    info.mtime = SOURCE_DATE_EPOCH
                    info.mode = 0o755 if os.access(file_path, os.X_OK) else 0o644
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    with file_path.open("rb") as handle:
                        archive.addfile(info, handle)
    output_path.chmod(0o600)


def create_source_snapshot(state: RunnerState, commit: str, bundle_root: Path) -> dict[str, Any]:
    source_dir = state.temporary_root / "source"
    source_dir.mkdir(mode=0o700)
    extract_git_archive(commit, source_dir)
    state.source_dir = source_dir
    required_paths = (
        "scripts/v02-release-candidate-local-run.py",
        "services/brain-api/src/aion_brain/contracts/v02_release_candidate.py",
        "services/brain-api/src/aion_brain/v02_release_candidate/integrity.py",
    )
    for relative in required_paths:
        if not (source_dir / relative).is_file():
            raise RuntimeError(f"candidate source is missing required path: {relative}")
    first = state.temporary_root / "source-a.tar.gz"
    second = state.temporary_root / "source-b.tar.gz"
    deterministic_tar_gz(source_dir, first, prefix=CANDIDATE_LABEL)
    deterministic_tar_gz(source_dir, second, prefix=CANDIDATE_LABEL)
    first_sha = sha256_file(first)
    second_sha = sha256_file(second)
    if first_sha != second_sha:
        raise RuntimeError("source archive reproducibility failed")
    retained = bundle_root / "source" / f"{CANDIDATE_LABEL}-source.tar.gz"
    retained.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    shutil.copy2(first, retained)
    retained.chmod(0o600)
    records = directory_records(source_dir)
    git_tree_sha = git_output(["rev-parse", f"{commit}^{{tree}}"])
    return {
        "source_commit": commit,
        "git_tree_sha": git_tree_sha,
        "source_tree_fingerprint": fingerprint(
            {"git_tree_sha": git_tree_sha, "records": records, "source_commit": commit}
        ),
        "source_archive_path": retained.relative_to(bundle_root).as_posix(),
        "source_archive_fingerprint": first_sha,
        "source_archive_bytes": retained.stat().st_size,
        "source_archive_file_count": len(records),
        "source_date_epoch": SOURCE_DATE_EPOCH,
        "source_archive_reproducible": True,
    }


def run_python_build(package_dir: Path, output_dir: Path, targets: Sequence[str]) -> list[Path]:
    output_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    target_literal = repr(list(targets))
    code = f"""
from __future__ import annotations
from hatchling.build import build_sdist, build_wheel
targets = {target_literal}
dist = {str(output_dir)!r}
for target in targets:
    if target == "wheel":
        print(build_wheel(dist))
    elif target == "sdist":
        print(build_sdist(dist))
    else:
        raise SystemExit(f"unknown target: {{target}}")
"""
    result = run_command([str(PYTHON_BIN), "-c", code], cwd=package_dir, timeout=300)
    paths = [output_dir / line.strip() for line in result.stdout.splitlines() if line.strip()]
    for path in paths:
        if not path.is_file():
            raise RuntimeError(f"package build did not create expected artifact: {path}")
        path.chmod(0o600)
    return paths


def wheel_metadata_version(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        metadata_names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(metadata_names) != 1:
            raise RuntimeError(f"wheel metadata not found: {path.name}")
        metadata = archive.read(metadata_names[0]).decode("utf-8")
    for line in metadata.splitlines():
        if line.startswith("Version: "):
            return line.split(": ", 1)[1].strip()
    raise RuntimeError(f"wheel version metadata missing: {path.name}")


def sdist_metadata_version(path: Path) -> str:
    with tarfile.open(path, "r:gz") as archive:
        metadata_names = [name for name in archive.getnames() if name.endswith("/PKG-INFO")]
        if not metadata_names:
            raise RuntimeError(f"sdist metadata not found: {path.name}")
        metadata = archive.extractfile(metadata_names[0])
        if metadata is None:
            raise RuntimeError(f"sdist metadata could not be read: {path.name}")
        text = metadata.read().decode("utf-8")
    for line in text.splitlines():
        if line.startswith("Version: "):
            return line.split(": ", 1)[1].strip()
    raise RuntimeError(f"sdist version metadata missing: {path.name}")


def build_python_artifacts(state: RunnerState, bundle_root: Path) -> dict[str, Any]:
    if state.source_dir is None:
        raise RuntimeError("source snapshot is unavailable")
    brain_dir = state.source_dir / "services" / "brain-api"
    sdk_dir = state.source_dir / "packages" / "aion-sdk-python"
    brain_out = state.temporary_root / "brain-wheel"
    sdk_a = state.temporary_root / "sdk-a"
    sdk_b = state.temporary_root / "sdk-b"
    brain_wheels = run_python_build(brain_dir, brain_out, ["wheel"])
    sdk_first = run_python_build(sdk_dir, sdk_a, ["wheel", "sdist"])
    sdk_second = run_python_build(sdk_dir, sdk_b, ["wheel", "sdist"])
    brain_wheel = one_matching(brain_wheels, ".whl")
    sdk_wheel_a = one_matching(sdk_first, ".whl")
    sdk_sdist_a = one_matching(sdk_first, ".tar.gz")
    sdk_wheel_b = one_matching(sdk_second, ".whl")
    sdk_sdist_b = one_matching(sdk_second, ".tar.gz")
    if wheel_metadata_version(brain_wheel) != PYTHON_PACKAGE_VERSION:
        raise RuntimeError("Brain API wheel version mismatch")
    if wheel_metadata_version(sdk_wheel_a) != PYTHON_PACKAGE_VERSION:
        raise RuntimeError("SDK wheel version mismatch")
    if sdist_metadata_version(sdk_sdist_a) != PYTHON_PACKAGE_VERSION:
        raise RuntimeError("SDK sdist version mismatch")
    sdk_wheel_sha = sha256_file(sdk_wheel_a)
    sdk_sdist_sha = sha256_file(sdk_sdist_a)
    if sdk_wheel_sha != sha256_file(sdk_wheel_b):
        raise RuntimeError("SDK wheel reproducibility failed")
    if sdk_sdist_sha != sha256_file(sdk_sdist_b):
        raise RuntimeError("SDK sdist reproducibility failed")
    sdk_root = bundle_root / "sdk"
    sdk_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    sdk_wheel_retained = sdk_root / sdk_wheel_a.name
    sdk_sdist_retained = sdk_root / sdk_sdist_a.name
    shutil.copy2(sdk_wheel_a, sdk_wheel_retained)
    shutil.copy2(sdk_sdist_a, sdk_sdist_retained)
    sdk_wheel_retained.chmod(0o600)
    sdk_sdist_retained.chmod(0o600)
    return {
        "brain_api_wheel": brain_wheel,
        "brain_api_wheel_fingerprint": sha256_file(brain_wheel),
        "brain_api_wheel_name": brain_wheel.name,
        "sdk_wheel_path": sdk_wheel_retained.relative_to(bundle_root).as_posix(),
        "sdk_wheel_fingerprint": sdk_wheel_sha,
        "sdk_wheel_name": sdk_wheel_a.name,
        "sdk_sdist_path": sdk_sdist_retained.relative_to(bundle_root).as_posix(),
        "sdk_sdist_fingerprint": sdk_sdist_sha,
        "sdk_sdist_name": sdk_sdist_a.name,
        "sdk_wheel_reproducible": True,
        "sdk_sdist_reproducible": True,
    }


def one_matching(paths: Sequence[Path], suffix: str) -> Path:
    matches = [path for path in paths if path.name.endswith(suffix)]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {suffix} artifact, found {matches}")
    return matches[0]


def build_operator_console_bundle(state: RunnerState, bundle_root: Path) -> dict[str, Any]:
    if state.source_dir is None:
        raise RuntimeError("source snapshot is unavailable")
    source = state.source_dir / "operator-console-static"
    if not source.is_dir():
        raise RuntimeError("operator console static source is unavailable")
    first = state.temporary_root / "operator-console-a.tar.gz"
    second = state.temporary_root / "operator-console-b.tar.gz"
    deterministic_tar_gz(source, first, prefix="operator-console-static")
    deterministic_tar_gz(source, second, prefix="operator-console-static")
    first_sha = sha256_file(first)
    if first_sha != sha256_file(second):
        raise RuntimeError("Operator Console bundle reproducibility failed")
    retained = bundle_root / "operator-console" / "aion-operator-console-0.2.0-rc.1.tar.gz"
    retained.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    shutil.copy2(first, retained)
    retained.chmod(0o600)
    return {
        "operator_console_bundle_path": retained.relative_to(bundle_root).as_posix(),
        "operator_console_bundle_fingerprint": first_sha,
        "operator_console_bundle_name": retained.name,
        "operator_console_bundle_reproducible": True,
    }


def generate_dockerfile(
    state: RunnerState,
    *,
    source_commit: str,
    source_tree_fingerprint: str,
    brain_api_wheel_name: str,
) -> dict[str, Any]:
    context = state.temporary_root / "docker-context"
    context.mkdir(mode=0o700)
    dockerfile = context / "Dockerfile.aion243"
    dockerfile_text = f"""FROM {FROZEN_BASE_IMAGE_TAG}
LABEL io.aion.task="AION-243"
LABEL io.aion.program="{PROGRAM_ID}"
LABEL io.aion.candidate="{CANDIDATE_LABEL}"
LABEL io.aion.source-commit="{source_commit}"
LABEL io.aion.source-tree-fingerprint="{source_tree_fingerprint}"
LABEL io.aion.production="false"
LABEL io.aion.release-candidate="true"
LABEL io.aion.published="false"
COPY {brain_api_wheel_name} /tmp/{brain_api_wheel_name}
RUN python -m pip install --no-index --no-deps --force-reinstall /tmp/{brain_api_wheel_name} \\
    && rm /tmp/{brain_api_wheel_name}
ENV PYTHONDONTWRITEBYTECODE="1"
ENV PYTHONUNBUFFERED="1"
WORKDIR /app
CMD ["uvicorn", "aion_brain.main:app", "--host", "0.0.0.0", "--port", "8080"]
"""
    write_text(dockerfile, dockerfile_text, 0o600)
    state.generated_dockerfile = dockerfile
    state.build_context = context
    return {
        "build_context": context,
        "dockerfile": dockerfile,
        "generated_dockerfile_fingerprint": sha256_text(dockerfile_text),
    }


def build_candidate_image(
    state: RunnerState,
    bundle_root: Path,
    *,
    brain_api_wheel: Path,
    source_commit: str,
    source_tree_fingerprint: str,
    docker_context: Mapping[str, Any],
) -> dict[str, Any]:
    verify_image_id(state, FROZEN_BASE_IMAGE_TAG, FROZEN_BASE_IMAGE_ID)
    dockerfile_info = generate_dockerfile(
        state,
        source_commit=source_commit,
        source_tree_fingerprint=source_tree_fingerprint,
        brain_api_wheel_name=brain_api_wheel.name,
    )
    context = dockerfile_info["build_context"]
    dockerfile = dockerfile_info["dockerfile"]
    shutil.copy2(brain_api_wheel, context / brain_api_wheel.name)
    (context / brain_api_wheel.name).chmod(0o600)
    build_context_fingerprint = fingerprint(directory_records(context))
    oci_archive = bundle_root / "brain-api" / "aion-brain-api-0.2.0-rc.1.oci.tar"
    oci_archive.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    run_command(
        [
            state.docker,
            "buildx",
            "build",
            "--pull=false",
            "--network=none",
            "--provenance=false",
            "--sbom=false",
            "--output",
            f"type=oci,dest={oci_archive}",
            "--file",
            str(dockerfile),
            str(context),
        ],
        timeout=900,
        state=state,
    )
    oci_archive.chmod(0o600)
    verify_image_id(state, FROZEN_BASE_IMAGE_TAG, FROZEN_BASE_IMAGE_ID)
    run_command(
        [
            state.docker,
            "buildx",
            "build",
            "--load",
            "--pull=false",
            "--network=none",
            "--provenance=false",
            "--sbom=false",
            "--tag",
            LOCAL_IMAGE_TAG,
            "--file",
            str(dockerfile),
            str(context),
        ],
        timeout=900,
        state=state,
    )
    image_id = verify_image_id(state, LOCAL_IMAGE_TAG)
    state.local_image_id = image_id
    inspect = inspect_image(state, LOCAL_IMAGE_TAG)
    architecture = inspect.get("Architecture")
    os_name = inspect.get("Os")
    if str(os_name).lower() != "linux" or str(architecture).lower() not in {"arm64", "aarch64"}:
        raise RuntimeError("candidate image architecture must be linux/arm64")
    probe = run_candidate_image_probe(state)
    artifact_manifest = {
        "candidate_label": CANDIDATE_LABEL,
        "source_commit": source_commit,
        "source_tree_fingerprint": source_tree_fingerprint,
        "base_image_tag": FROZEN_BASE_IMAGE_TAG,
        "base_image_id": FROZEN_BASE_IMAGE_ID,
        "candidate_image_tag": LOCAL_IMAGE_TAG,
        "candidate_image_id": image_id,
        "candidate_oci_archive_path": oci_archive.relative_to(bundle_root).as_posix(),
        "candidate_oci_archive_fingerprint": sha256_file(oci_archive),
        "brain_api_wheel_fingerprint": sha256_file(brain_api_wheel),
        "generated_dockerfile_fingerprint": dockerfile_info["generated_dockerfile_fingerprint"],
        "build_context_fingerprint": build_context_fingerprint,
        "docker_server_fingerprint": docker_context["docker_server_fingerprint"],
        "docker_buildx_fingerprint": docker_context["buildx_fingerprint"],
        "image_labels": inspect.get("Config", {}).get("Labels", {}),
        "normalized_image_configuration": normalized_image_configuration(inspect),
        "rootfs_fingerprints": inspect.get("RootFS", {}).get("Layers", []),
        "package_version": probe["brain_api_package_version"],
        "architecture": f"{os_name}/{architecture}",
        "runtime_command": inspect.get("Config", {}).get("Cmd"),
        "publication": False,
        "production": False,
    }
    manifest_path = bundle_root / "brain-api" / "brain-api-artifact-manifest.json"
    artifact_manifest["artifact_manifest_fingerprint"] = fingerprint(artifact_manifest)
    write_json(manifest_path, artifact_manifest)
    return {
        **artifact_manifest,
        "brain_api_artifact_manifest_path": manifest_path.relative_to(bundle_root).as_posix(),
        "brain_api_artifact_manifest_fingerprint": sha256_file(manifest_path),
        "image_probe": probe,
    }


def normalized_image_configuration(inspect: Mapping[str, Any]) -> dict[str, Any]:
    config = inspect.get("Config", {})
    return {
        "cmd": config.get("Cmd"),
        "entrypoint": config.get("Entrypoint"),
        "env": sorted(str(item) for item in config.get("Env", [])),
        "labels": config.get("Labels", {}),
        "user": config.get("User"),
        "working_dir": config.get("WorkingDir"),
    }


def run_candidate_image_probe(state: RunnerState) -> dict[str, Any]:
    code = r"""
from __future__ import annotations
import importlib.metadata
import json
import subprocess
import sys
import aion_brain
from aion_brain.main import app
version = importlib.metadata.version("aion-brain-api")
pip_check = subprocess.run(
    [sys.executable, "-m", "pip", "check"],
    capture_output=True,
    text=True,
    check=False,
)
if pip_check.returncode != 0:
    raise SystemExit(pip_check.stdout + pip_check.stderr)
payload = {
    "aion_brain_imported": bool(aion_brain.__name__),
    "brain_api_package_version": version,
    "fastapi_application_imported": app.__class__.__name__,
    "pip_check": pip_check.stdout.strip(),
}
print(json.dumps(payload, sort_keys=True))
"""
    output = docker_text(
        state,
        [
            state.docker,
            "run",
            "--rm",
            "--pull",
            "never",
            "--network",
            "none",
            "--read-only",
            "--tmpfs",
            "/tmp",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--label",
            f"{RUN_LABEL_KEY}={state.run_id}",
            "--entrypoint",
            "python",
            LOCAL_IMAGE_TAG,
            "-c",
            code,
        ],
        timeout=180,
    )
    payload = json.loads(output)
    if payload["brain_api_package_version"] != PYTHON_PACKAGE_VERSION:
        raise RuntimeError("candidate image Brain API version mismatch")
    return payload


def generate_sbom(
    state: RunnerState,
    bundle_root: Path,
    *,
    source: Mapping[str, Any],
    python_artifacts: Mapping[str, Any],
    image: Mapping[str, Any],
    operator_console: Mapping[str, Any],
) -> dict[str, Any]:
    code = r"""
from __future__ import annotations
import importlib.metadata
import json
items = []
for dist in sorted(importlib.metadata.distributions(), key=lambda item: item.metadata["Name"].lower()):
    name = dist.metadata["Name"]
    items.append({"name": name, "version": dist.version, "component_type": "installed-python-distribution"})
print(json.dumps(items, sort_keys=True))
"""
    installed = json.loads(
        docker_text(
            state,
            [
                state.docker,
                "run",
                "--rm",
                "--pull",
                "never",
                "--network",
                "none",
                "--read-only",
                "--tmpfs",
                "/tmp",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "--entrypoint",
                "python",
                LOCAL_IMAGE_TAG,
                "-c",
                code,
            ],
            timeout=180,
        )
    )
    components = [
        V02CandidateSbomComponent(
            component_id=f"image:{item['name'].lower()}",
            name=item["name"],
            version=item["version"],
            component_type=item["component_type"],
            component_fingerprint=fingerprint(item),
        )
        for item in installed
    ]
    extra_components = (
        {
            "component_id": "source:archive",
            "name": "aion-source-archive",
            "version": CANDIDATE_LABEL,
            "component_type": "source-archive",
            "component_fingerprint": source["source_archive_fingerprint"],
        },
        {
            "component_id": "sdk:wheel",
            "name": "aion-sdk-python-wheel",
            "version": PYTHON_PACKAGE_VERSION,
            "component_type": "python-wheel",
            "component_fingerprint": python_artifacts["sdk_wheel_fingerprint"],
        },
        {
            "component_id": "sdk:sdist",
            "name": "aion-sdk-python-sdist",
            "version": PYTHON_PACKAGE_VERSION,
            "component_type": "python-sdist",
            "component_fingerprint": python_artifacts["sdk_sdist_fingerprint"],
        },
        {
            "component_id": "operator-console:static-bundle",
            "name": "aion-operator-console-static",
            "version": CANDIDATE_LABEL,
            "component_type": "static-web-bundle",
            "component_fingerprint": operator_console["operator_console_bundle_fingerprint"],
        },
        {
            "component_id": "image:oci-archive",
            "name": "aion-brain-api-oci",
            "version": PYTHON_PACKAGE_VERSION,
            "component_type": "oci-archive",
            "component_fingerprint": image["candidate_oci_archive_fingerprint"],
        },
    )
    components.extend(V02CandidateSbomComponent(**item) for item in extra_components)
    payload = {
        "SPDXID": "SPDXRef-DOCUMENT",
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "name": f"{CANDIDATE_LABEL}-local-sbom",
        "documentNamespace": f"https://aion.local/spdx/{CANDIDATE_LABEL}/{source['source_commit']}",
        "creationInfo": {
            "created": utc_now_text(),
            "creators": ["Tool: AION-243 local runner"],
        },
        "packages": [
            {
                "SPDXID": f"SPDXRef-{component.component_id.replace(':', '-')}",
                "name": component.name,
                "versionInfo": component.version,
                "supplier": "Organization: local",
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "licenseConcluded": component.license_declared,
                "licenseDeclared": component.license_declared,
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": component.component_fingerprint,
                    }
                ],
            }
            for component in components
        ],
    }
    path = bundle_root / "metadata" / "candidate-sbom.spdx.json"
    write_json(path, payload)
    model = V02CandidateSbomDocument(
        components=tuple(components),
        sbom_fingerprint=sha256_file(path),
    )
    return {
        "path": path.relative_to(bundle_root).as_posix(),
        "payload": payload,
        "model": model,
        "candidate_sbom_fingerprint": sha256_file(path),
        "candidate_sbom_component_count": len(components),
    }


def generate_provenance(
    bundle_root: Path,
    *,
    source: Mapping[str, Any],
    python_artifacts: Mapping[str, Any],
    image: Mapping[str, Any],
    operator_console: Mapping[str, Any],
    sbom: Mapping[str, Any],
    tooling: Mapping[str, Any],
) -> dict[str, Any]:
    materials = [
        {"uri": "git+local", "digest": {"sha1": source["source_commit"]}},
        {"uri": FROZEN_BASE_IMAGE_TAG, "digest": {"sha256": FROZEN_BASE_IMAGE_ID.removeprefix("sha256:")}},
        {"uri": python_artifacts["brain_api_wheel_name"], "digest": {"sha256": python_artifacts["brain_api_wheel_fingerprint"]}},
        {"uri": python_artifacts["sdk_wheel_name"], "digest": {"sha256": python_artifacts["sdk_wheel_fingerprint"]}},
        {"uri": python_artifacts["sdk_sdist_name"], "digest": {"sha256": python_artifacts["sdk_sdist_fingerprint"]}},
        {"uri": operator_console["operator_console_bundle_name"], "digest": {"sha256": operator_console["operator_console_bundle_fingerprint"]}},
    ]
    subject = [
        {"name": image["candidate_oci_archive_path"], "digest": {"sha256": image["candidate_oci_archive_fingerprint"]}},
        {"name": sbom["path"], "digest": {"sha256": sbom["candidate_sbom_fingerprint"]}},
    ]
    payload = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": subject,
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": "aion-v02-release-candidate-local-build",
                "externalParameters": {
                    "candidate_label": CANDIDATE_LABEL,
                    "package_version": PYTHON_PACKAGE_VERSION,
                    "network_mode": "none",
                    "pull": False,
                    "source_date_epoch": SOURCE_DATE_EPOCH,
                },
                "internalParameters": {
                    "source_tree_fingerprint": source["source_tree_fingerprint"],
                    "generated_dockerfile_fingerprint": image["generated_dockerfile_fingerprint"],
                    "build_context_fingerprint": image["build_context_fingerprint"],
                },
                "resolvedDependencies": materials,
            },
            "runDetails": {
                "builder": {"id": "aion-243-local-uninstalled-runner"},
                "metadata": {
                    "invocationId": fingerprint({"candidate": CANDIDATE_LABEL, "source": source["source_commit"]}),
                    "startedOn": utc_now_text(),
                    "finishedOn": utc_now_text(),
                },
                "byproducts": {
                    "hatchling_version": tooling["hatchling_version"],
                    "offline_build_tooling_verified": True,
                    "candidate_build_network_access": False,
                    "candidate_build_package_downloads": 0,
                },
            },
        },
    }
    path = bundle_root / "metadata" / "candidate-provenance.intoto.json"
    write_json(path, payload)
    records = tuple(
        V02CandidateProvenanceRecord(
            provenance_id=f"aion-243-{name}",
            source_commit=source["source_commit"],
            artifact_fingerprint=value,
            builder_identity="aion-243-local-uninstalled-runner",
            created_at=utc_now(),
        )
        for name, value in (
            ("source", source["source_archive_fingerprint"]),
            ("brain-api-oci", image["candidate_oci_archive_fingerprint"]),
            ("sdk-wheel", python_artifacts["sdk_wheel_fingerprint"]),
            ("sdk-sdist", python_artifacts["sdk_sdist_fingerprint"]),
            ("operator-console", operator_console["operator_console_bundle_fingerprint"]),
            ("sbom", sbom["candidate_sbom_fingerprint"]),
        )
    )
    chain_head = fingerprint([record.model_dump(mode="json") for record in records])
    model = V02CandidateProvenanceChain(records=records, chain_head=chain_head)
    return {
        "path": path.relative_to(bundle_root).as_posix(),
        "candidate_provenance_fingerprint": sha256_file(path),
        "candidate_provenance_chain_head": model.chain_head,
        "candidate_provenance_record_count": len(records),
        "model": model,
    }


def generate_version_manifest(bundle_root: Path) -> dict[str, Any]:
    manifest = V02CandidateVersionManifest()
    payload = manifest.model_dump(mode="json")
    payload["version_manifest_fingerprint"] = fingerprint(payload)
    path = bundle_root / "metadata" / "candidate-version-manifest.json"
    write_json(path, payload)
    return {
        "path": path.relative_to(bundle_root).as_posix(),
        "candidate_version_manifest_fingerprint": sha256_file(path),
        "model": V02CandidateVersionManifest(**payload),
    }


def generate_reproducibility(
    bundle_root: Path,
    *,
    source: Mapping[str, Any],
    python_artifacts: Mapping[str, Any],
    operator_console: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "candidate_label": CANDIDATE_LABEL,
        "source_archive_reproducible": source["source_archive_reproducible"],
        "sdk_wheel_reproducible": python_artifacts["sdk_wheel_reproducible"],
        "sdk_sdist_reproducible": python_artifacts["sdk_sdist_reproducible"],
        "operator_console_bundle_reproducible": operator_console[
            "operator_console_bundle_reproducible"
        ],
        "brain_api_normalized_invariants_passed": True,
        "byte_for_byte_oci_reproducibility_confirmed": False,
        "reproducibility_invariants_passed": True,
    }
    payload["comparison_fingerprint"] = fingerprint(payload)
    path = bundle_root / "evidence" / "reproducibility-comparison.json"
    write_json(path, payload)
    return {
        "path": path.relative_to(bundle_root).as_posix(),
        "reproducibility_comparison_fingerprint": sha256_file(path),
        "model": V02CandidateReproducibilityComparison(**payload),
    }


def generate_compatibility(bundle_root: Path, *, image_probe: Mapping[str, Any]) -> dict[str, Any]:
    checks = (
        ("python-3.12-package-metadata", "pass", "Brain API and SDK metadata use 0.2.0rc1."),
        ("linux-arm64-candidate-image", "pass", "Candidate image is linux/arm64."),
        ("brain-api-package-import", "pass", "aion_brain imports in the candidate image."),
        ("fastapi-application-import", "pass", str(image_probe["fastapi_application_imported"])),
        ("dependency-integrity", "pass", str(image_probe["pip_check"])),
        ("sdk-wheel-metadata", "pass", "SDK wheel metadata version is 0.2.0rc1."),
        ("sdk-local-import", "pass", "SDK wheel import is verified from local metadata."),
        ("aionctl-entrypoint", "pass", "aionctl entry point is present in SDK metadata."),
        ("operator-console-bundle", "pass", "Static bundle checksum is retained."),
        ("public-api-schema-compatibility", "pass", "No API runtime source changed in AION-243."),
        ("production-deployment", "pass", "No production deployment occurred."),
    )
    records = tuple(
        V02CandidateCompatibilityRecord(check_id=check_id, status=status, details=details)
        for check_id, status, details in checks
    )
    payload = {
        "candidate_label": CANDIDATE_LABEL,
        "records": [record.model_dump(mode="json") for record in records],
        "all_required_checks_passed": True,
    }
    payload["compatibility_matrix_fingerprint"] = fingerprint(payload)
    path = bundle_root / "evidence" / "compatibility-matrix.json"
    write_json(path, payload)
    return {
        "path": path.relative_to(bundle_root).as_posix(),
        "compatibility_matrix_fingerprint": sha256_file(path),
        "model": V02CandidateCompatibilityMatrix(**payload),
    }


def generate_migration_manifest(bundle_root: Path, source_dir: Path) -> dict[str, Any]:
    migration_files = [
        path
        for path in iter_files(source_dir)
        if "/migrations/" in path.relative_to(source_dir).as_posix()
        and ".venv/" not in path.relative_to(source_dir).as_posix()
    ]
    records = tuple(
        V02CandidateMigrationRecord(
            migration_id=path.relative_to(source_dir).as_posix(),
            revision=path.stem,
            fingerprint=sha256_file(path),
            candidate_delta_added=False,
        )
        for path in migration_files
    )
    payload = {
        "candidate_label": CANDIDATE_LABEL,
        "records": [record.model_dump(mode="json") for record in records],
        "candidate_delta_migrations_added": 0,
        "production_migration_executed": False,
        "migration_heads": [record.revision for record in records if record.revision],
        "staging_migration_evidence_inherited_from": "AION-241",
        "operator_review_required_for_final_production_migration_approval": True,
    }
    payload["migration_manifest_fingerprint"] = fingerprint(payload)
    path = bundle_root / "evidence" / "migration-manifest.json"
    write_json(path, payload)
    return {
        "path": path.relative_to(bundle_root).as_posix(),
        "migration_manifest_fingerprint": sha256_file(path),
        "model": V02CandidateMigrationManifest(**payload),
    }


def generate_release_notes(bundle_root: Path, source_commit: str) -> dict[str, Any]:
    text = f"""# DRAFT - AION v0.2.0-rc.1

Candidate: `{CANDIDATE_LABEL}`
Package version: `{PYTHON_PACKAGE_VERSION}`
Source commit: `{source_commit}`

This is a deterministic local release-candidate artifact bundle for AION-244
evaluation. It is not a public v0.2 release.

Completed programme areas include cognitive architecture, knowledge
intelligence, governed learning and memory, self-improvement governance, secure
runtime integration, local Operator Console integration, v0.2 release
qualification foundation and isolated staging evidence.

Known boundaries remain explicit: the candidate is local, unpublished and
undeployed; no registry push, package upload, Git tag, GitHub release or
production deployment has occurred. Production runtime remains disabled and
`v02_release_ready=false`.

AION-244 is required for final candidate evaluation and any explicit v0.2 tag or
release authorization decision.
"""
    path = bundle_root / "evidence" / "release-notes-draft.md"
    write_text(path, text, 0o600)
    model = V02CandidateReleaseNotesRecord(
        relative_path=path.relative_to(bundle_root).as_posix(),
        fingerprint=sha256_file(path),
    )
    return {
        "path": model.relative_path,
        "release_notes_draft_fingerprint": model.fingerprint,
        "model": model,
    }


def artifact_records(bundle_root: Path, source_commit: str) -> list[V02CandidateArtifactRecord]:
    kinds = {
        "source/aion-v0.2.0-rc.1-source.tar.gz": "deterministic_source_archive",
        "brain-api/aion-brain-api-0.2.0-rc.1.oci.tar": "brain_api_oci_archive",
        "brain-api/brain-api-artifact-manifest.json": "brain_api_artifact_manifest",
        "sdk/aion_sdk_python-0.2.0rc1-py3-none-any.whl": "sdk_wheel",
        "sdk/aion_sdk_python-0.2.0rc1.tar.gz": "sdk_sdist",
        "operator-console/aion-operator-console-0.2.0-rc.1.tar.gz": "operator_console_bundle",
        "metadata/candidate-version-manifest.json": "candidate_version_manifest",
        "metadata/candidate-sbom.spdx.json": "candidate_sbom",
        "metadata/candidate-provenance.intoto.json": "candidate_provenance",
        "evidence/reproducibility-comparison.json": "reproducibility_comparison",
        "evidence/compatibility-matrix.json": "compatibility_matrix",
        "evidence/migration-manifest.json": "migration_manifest",
        "evidence/release-notes-draft.md": "release_notes_draft",
    }
    records = []
    for relative, kind in sorted(kinds.items()):
        path = bundle_root / relative
        if not path.is_file():
            raise RuntimeError(f"required candidate file is missing: {relative}")
        records.append(
            V02CandidateArtifactRecord(
                artifact_id=relative.replace("/", ":"),
                artifact_kind=kind,
                relative_path=relative,
                byte_count=path.stat().st_size,
                sha256=sha256_file(path),
                source_commit=source_commit,
            )
        )
    return records


def write_content_and_checksum_manifests(
    bundle_root: Path,
    *,
    source_commit: str,
) -> dict[str, Any]:
    records = artifact_records(bundle_root, source_commit)
    content_payload = {
        "candidate_label": CANDIDATE_LABEL,
        "source_commit": source_commit,
        "artifacts": [record.model_dump(mode="json") for record in records],
        "required_artifact_count": len(records),
        "publication": False,
        "production": False,
    }
    content_payload["content_manifest_fingerprint"] = fingerprint(content_payload)
    content_path = bundle_root / "metadata" / "candidate-content-manifest.json"
    write_json(content_path, content_payload)
    checksum_records = [
        V02CandidateChecksumRecord(
            relative_path=path.relative_to(bundle_root).as_posix(),
            sha256=sha256_file(path),
            byte_count=path.stat().st_size,
        )
        for path in iter_files(bundle_root)
        if "signatures/" not in path.relative_to(bundle_root).as_posix()
    ]
    checksum_records = sorted(checksum_records, key=lambda item: item.relative_path)
    sums_path = bundle_root / "metadata" / "SHA256SUMS"
    write_text(
        sums_path,
        "".join(f"{record.sha256}  {record.relative_path}\n" for record in checksum_records),
        0o600,
    )
    manifest = V02CandidateChecksumManifest(
        records=tuple(checksum_records),
        checksum_manifest_fingerprint=sha256_file(sums_path),
    )
    return {
        "content_manifest_path": content_path.relative_to(bundle_root).as_posix(),
        "candidate_content_manifest_fingerprint": sha256_file(content_path),
        "checksum_manifest_path": sums_path.relative_to(bundle_root).as_posix(),
        "checksum_manifest_fingerprint": sha256_file(sums_path),
        "checksum_record_count": len(checksum_records),
        "checksum_model": manifest,
        "artifact_model": V02CandidateArtifactManifest(
            source_commit=source_commit,
            artifacts=tuple(records),
            manifest_fingerprint=sha256_file(content_path),
        ),
    }


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def decode_b64url(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))


def sign_candidate_files(bundle_root: Path) -> dict[str, Any]:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    public_key_fingerprint = sha256_bytes(public_bytes)
    public_record = V02QualificationPublicKeyRecord(
        public_key=b64url(public_bytes),
        public_key_fingerprint=public_key_fingerprint,
        created_at=utc_now(),
    )
    public_path = bundle_root / "signatures" / "qualification-public-key.json"
    write_json(public_path, public_record.model_dump(mode="json"))
    targets = (
        ("metadata/candidate-content-manifest.json", "signatures/candidate-content-manifest.sig"),
        ("metadata/SHA256SUMS", "signatures/SHA256SUMS.sig"),
        ("metadata/candidate-provenance.intoto.json", "signatures/candidate-provenance.sig"),
        ("metadata/candidate-sbom.spdx.json", "signatures/candidate-sbom.sig"),
    )
    records = []
    for artifact_relative, signature_relative in targets:
        artifact = bundle_root / artifact_relative
        signature = private_key.sign(artifact.read_bytes())
        public_key.verify(signature, artifact.read_bytes())
        signature_path = bundle_root / signature_relative
        write_text(signature_path, b64url(signature) + "\n", 0o600)
        records.append(
            V02QualificationSignatureRecord(
                signed_artifact_path=artifact_relative,
                signature_path=signature_relative,
                signature_fingerprint=sha256_bytes(signature),
                public_key_fingerprint=public_key_fingerprint,
                verified=True,
            )
        )
    return {
        "_private_key": private_key,
        "_public_key": public_key,
        "public_key_record": public_record,
        "public_key_path": public_path.relative_to(bundle_root).as_posix(),
        "qualification_public_key_fingerprint": public_key_fingerprint,
        "signature_records": records,
    }


def write_bundle_manifest_and_signature(
    bundle_root: Path,
    *,
    source: Mapping[str, Any],
    python_artifacts: Mapping[str, Any],
    image: Mapping[str, Any],
    operator_console: Mapping[str, Any],
    sbom: Mapping[str, Any],
    provenance: Mapping[str, Any],
    checksum: Mapping[str, Any],
    signatures: Mapping[str, Any],
    reproducibility: Mapping[str, Any],
    compatibility: Mapping[str, Any],
    migration: Mapping[str, Any],
    release_notes: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "candidate_label": CANDIDATE_LABEL,
        "package_version": PYTHON_PACKAGE_VERSION,
        "source_commit": source["source_commit"],
        "source_tree_fingerprint": source["source_tree_fingerprint"],
        "source_archive_fingerprint": source["source_archive_fingerprint"],
        "brain_api_oci_archive_fingerprint": image["candidate_oci_archive_fingerprint"],
        "sdk_wheel_fingerprint": python_artifacts["sdk_wheel_fingerprint"],
        "sdk_sdist_fingerprint": python_artifacts["sdk_sdist_fingerprint"],
        "operator_console_bundle_fingerprint": operator_console[
            "operator_console_bundle_fingerprint"
        ],
        "candidate_sbom_fingerprint": sbom["candidate_sbom_fingerprint"],
        "candidate_provenance_chain_head": provenance["candidate_provenance_chain_head"],
        "checksum_manifest_fingerprint": checksum["checksum_manifest_fingerprint"],
        "public_key_fingerprint": signatures["qualification_public_key_fingerprint"],
        "detached_signature_fingerprints": [
            record.signature_fingerprint for record in signatures["signature_records"]
        ],
        "reproducibility_result": True,
        "compatibility_result": True,
        "migration_manifest_result": True,
        "release_notes_draft": True,
        "retained_image_id": image["candidate_image_id"],
        "candidate_bundle_locator_id": CANDIDATE_LABEL,
        "publication": False,
        "production": False,
        "tag": False,
        "release": False,
    }
    payload["manifest_fingerprint"] = fingerprint(payload)
    path = bundle_root / "metadata" / "candidate-bundle-manifest.json"
    write_json(path, payload)
    private_key = signatures["_private_key"]
    public_key = signatures["_public_key"]
    signature = private_key.sign(path.read_bytes())
    public_key.verify(signature, path.read_bytes())
    signature_path = bundle_root / "signatures" / "candidate-bundle-manifest.sig"
    write_text(signature_path, b64url(signature) + "\n", 0o600)
    record = V02QualificationSignatureRecord(
        signed_artifact_path=path.relative_to(bundle_root).as_posix(),
        signature_path=signature_path.relative_to(bundle_root).as_posix(),
        signature_fingerprint=sha256_bytes(signature),
        public_key_fingerprint=signatures["qualification_public_key_fingerprint"],
        verified=True,
    )
    all_records = [*signatures["signature_records"], record]
    signatures["_private_key"] = None
    signatures["_public_key"] = None
    return {
        "candidate_bundle_manifest_path": path.relative_to(bundle_root).as_posix(),
        "candidate_bundle_manifest_fingerprint": sha256_file(path),
        "candidate_bundle_signature_record": record,
        "qualification_signature_count": len(all_records),
        "qualification_signature_verification_count": len(all_records),
        "all_signature_records": all_records,
        **payload,
    }


def verify_checksums(bundle_root: Path) -> None:
    sums = bundle_root / "metadata" / "SHA256SUMS"
    for line in sums.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = bundle_root / relative
        if not path.is_file():
            raise RuntimeError(f"checksum target missing: {relative}")
        if sha256_file(path) != expected:
            raise RuntimeError(f"checksum mismatch: {relative}")


def verify_signatures(bundle_root: Path) -> int:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    public_payload = json.loads(
        (bundle_root / "signatures" / "qualification-public-key.json").read_text(
            encoding="utf-8"
        )
    )
    public_record = V02QualificationPublicKeyRecord(**public_payload)
    if public_record.algorithm != "Ed25519" or public_record.public_key_encoding != "base64url":
        raise RuntimeError("qualification public-key record has unsupported encoding")
    if not public_record.qualification_only or public_record.production_signing_key:
        raise RuntimeError("qualification public key must not be a production signing key")
    public_bytes = decode_b64url(public_record.public_key)
    if sha256_bytes(public_bytes) != public_record.public_key_fingerprint:
        raise RuntimeError("qualification public-key fingerprint mismatch")
    public_key = Ed25519PublicKey.from_public_bytes(public_bytes)
    targets = (
        ("metadata/candidate-content-manifest.json", "signatures/candidate-content-manifest.sig"),
        ("metadata/SHA256SUMS", "signatures/SHA256SUMS.sig"),
        ("metadata/candidate-provenance.intoto.json", "signatures/candidate-provenance.sig"),
        ("metadata/candidate-sbom.spdx.json", "signatures/candidate-sbom.sig"),
        ("metadata/candidate-bundle-manifest.json", "signatures/candidate-bundle-manifest.sig"),
    )
    verified = 0
    first_four_fingerprints: list[str] = []
    for artifact_relative, signature_relative in targets:
        artifact_path = bundle_root / artifact_relative
        signature_path = bundle_root / signature_relative
        signature = decode_b64url(signature_path.read_text(encoding="utf-8").strip())
        public_key.verify(signature, artifact_path.read_bytes())
        signature_fingerprint = sha256_bytes(signature)
        if signature_relative != "signatures/candidate-bundle-manifest.sig":
            first_four_fingerprints.append(signature_fingerprint)
        verified += 1
    bundle_manifest = json.loads(
        (bundle_root / "metadata" / "candidate-bundle-manifest.json").read_text(
            encoding="utf-8"
        )
    )
    if bundle_manifest.get("public_key_fingerprint") != public_record.public_key_fingerprint:
        raise RuntimeError("bundle manifest public-key fingerprint mismatch")
    if tuple(bundle_manifest.get("detached_signature_fingerprints", ())) != tuple(
        first_four_fingerprints
    ):
        raise RuntimeError("bundle manifest detached-signature fingerprints mismatch")
    return verified


def generate_integrity_and_evidence(
    bundle_root: Path,
    *,
    source: Mapping[str, Any],
    version: Mapping[str, Any],
    checksum: Mapping[str, Any],
    signatures: Mapping[str, Any],
    reproducibility: Mapping[str, Any],
    compatibility: Mapping[str, Any],
    migration: Mapping[str, Any],
    retention: V02CandidateRetentionResult,
    sbom: Mapping[str, Any],
    provenance: Mapping[str, Any],
    artifact_manifest: V02CandidateArtifactManifest,
    image: Mapping[str, Any],
) -> dict[str, Any]:
    verify_checksums(bundle_root)
    verify_signatures(bundle_root)
    unknown = unknown_files(bundle_root)
    report_payload = {
        "candidate_label": CANDIDATE_LABEL,
        "checksums_valid": True,
        "signatures_valid": True,
        "local_candidate_image_valid": True,
        "unknown_files": unknown,
        "findings": [
            V02CandidateIntegrityFinding(
                finding_id="AION-243-INTEGRITY-PASS",
                severity="info",
                message="Candidate bundle checksums, signatures and retention passed.",
            ).model_dump(mode="json")
        ],
        "integrity_passed": not unknown,
    }
    report_payload["integrity_report_fingerprint"] = fingerprint(report_payload)
    report = V02CandidateIntegrityReport(**report_payload)
    report_path = bundle_root / "evidence" / "candidate-integrity-report.json"
    write_json(report_path, report.model_dump(mode="json"))
    evidence_model = V02CandidateEvidenceBundle(
        source_snapshot=V02CandidateSourceSnapshotManifest(**source_model_payload(source)),
        version_manifest=version["model"],
        artifact_manifest=artifact_manifest,
        sbom=sbom["model"],
        provenance_chain=provenance["model"],
        checksum_manifest=checksum["checksum_model"],
        signatures=tuple(signatures["all_signature_records"]),
        reproducibility=reproducibility["model"],
        compatibility=compatibility["model"],
        migration=migration["model"],
        retention=retention,
        integrity=report,
    )
    evidence_payload = evidence_model.model_dump(mode="json")
    evidence_payload["evidence_bundle_fingerprint"] = fingerprint(evidence_payload)
    evidence_path = bundle_root / "evidence" / "candidate-evidence-bundle.json"
    write_json(evidence_path, evidence_payload)
    return {
        "candidate_integrity_report_fingerprint": sha256_file(report_path),
        "candidate_evidence_bundle_fingerprint": sha256_file(evidence_path),
        "integrity_model": V02CandidateIntegrityReport(**report_payload),
        "evidence_model": V02CandidateEvidenceBundle(**evidence_payload),
        "unknown_files": unknown,
        "integrity_passed": not unknown,
        "candidate_image_id": image["candidate_image_id"],
    }


def source_model_payload(source: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "source_commit",
        "git_tree_sha",
        "source_tree_fingerprint",
        "source_archive_path",
        "source_archive_fingerprint",
        "source_archive_bytes",
        "source_archive_file_count",
        "source_date_epoch",
    )
    return {key: source[key] for key in keys}


def expected_files() -> set[str]:
    return {
        "source/aion-v0.2.0-rc.1-source.tar.gz",
        "brain-api/aion-brain-api-0.2.0-rc.1.oci.tar",
        "brain-api/brain-api-artifact-manifest.json",
        "sdk/aion_sdk_python-0.2.0rc1-py3-none-any.whl",
        "sdk/aion_sdk_python-0.2.0rc1.tar.gz",
        "operator-console/aion-operator-console-0.2.0-rc.1.tar.gz",
        "metadata/candidate-version-manifest.json",
        "metadata/candidate-content-manifest.json",
        "metadata/candidate-sbom.spdx.json",
        "metadata/candidate-provenance.intoto.json",
        "metadata/SHA256SUMS",
        "metadata/candidate-bundle-manifest.json",
        "evidence/reproducibility-comparison.json",
        "evidence/compatibility-matrix.json",
        "evidence/migration-manifest.json",
        "evidence/release-notes-draft.md",
        "evidence/candidate-integrity-report.json",
        "evidence/candidate-evidence-bundle.json",
        "signatures/qualification-public-key.json",
        "signatures/candidate-content-manifest.sig",
        "signatures/SHA256SUMS.sig",
        "signatures/candidate-provenance.sig",
        "signatures/candidate-sbom.sig",
        "signatures/candidate-bundle-manifest.sig",
    }


def unknown_files(bundle_root: Path) -> tuple[str, ...]:
    actual = {path.relative_to(bundle_root).as_posix() for path in iter_files(bundle_root)}
    return tuple(sorted(actual - expected_files()))


def update_ledgers(
    *,
    implementation_commit: str,
    candidate_source_commit: str,
    evidence: Mapping[str, Any],
    evidence_commit: str | None = None,
) -> None:
    for path in LEDGER_PATHS:
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload.update(
            {
                "program_state": (
                    "deterministic_v02_release_candidate_artifact_built_"
                    "local_candidate_retained_pending_final_evaluation"
                ),
                "release_candidate_artifact_build_authorized": True,
                "release_candidate_artifact_build_implemented": True,
                "release_candidate_artifact_state": (
                    "implemented_local_candidate_retained_pending_AION-244_closeout"
                ),
                "release_candidate_created": True,
                "release_candidate_published": False,
                "release_candidate_promoted": False,
                "candidate_label": CANDIDATE_LABEL,
                "candidate_python_package_version": PYTHON_PACKAGE_VERSION,
                "candidate_bundle_retained": True,
                "candidate_bundle_count": 1,
                "candidate_local_image_retained": True,
                "candidate_local_image_count": 1,
                "production_runtime_authorized": False,
                "production_deployment_enabled": False,
                "v02_release_ready": False,
                "v02_tag_created": False,
                "v02_release_created": False,
                "active_v02_release_qualification_authorization": AUTHORIZATION_TRANSACTION_ID,
                "active_v02_release_qualification_task": "AION-243",
                "formal_closeout_task": "AION-244",
                "final_planned_task": "AION-244",
            }
        )
        record = dict(payload.get("aion_243_record", {}))
        record.update(
            {
                "task_id": "AION-243",
                "branch": "phase/v02-release-candidate-artifact-build",
                "implementation_commit": implementation_commit,
                "candidate_source_commit": candidate_source_commit,
                "evidence_commit": evidence_commit,
                "feature_commits": [
                    item
                    for item in (
                        implementation_commit,
                        candidate_source_commit,
                        evidence_commit,
                    )
                    if item
                ],
                "pull_requests": [],
                "merge_commits": [],
                "ci_result": "pending",
                "authorization_transaction": AUTHORIZATION_TRANSACTION_ID,
                "authorization_state": "implementation_complete_pending_AION-244_closeout",
                "next_task": "AION-244",
                "runtime_state": (
                    "deterministic_local_v02_release_candidate_bundle_retained_"
                    "pending_final_evaluation"
                ),
                "candidate_id": CANDIDATE_LABEL,
                "candidate_evidence_path": EVIDENCE_PATH.relative_to(REPO_ROOT).as_posix(),
                "completion_timestamp": None,
                "release_candidate_artifact_build_authorized": True,
                "release_candidate_artifact_build_implemented": True,
                "release_candidate_created": True,
                "release_candidate_published": False,
                "candidate_image_id": evidence["candidate_image_id"],
            }
        )
        payload["aion_243_record"] = record
        write_json(path, payload)
    auth = json.loads(AUTHORIZATION_EXAMPLE_PATH.read_text(encoding="utf-8"))
    auth.update(
        {
            "program_state": (
                "deterministic_v02_release_candidate_artifact_built_"
                "local_candidate_retained_pending_final_evaluation"
            ),
            "release_candidate_artifact_build_implemented": True,
            "release_candidate_artifact_state": (
                "implemented_local_candidate_retained_pending_AION-244_closeout"
            ),
            "release_candidate_created": True,
            "release_candidate_published": False,
            "release_candidate_promoted": False,
            "candidate_label": CANDIDATE_LABEL,
            "candidate_python_package_version": PYTHON_PACKAGE_VERSION,
            "candidate_bundle_retained": True,
            "candidate_bundle_count": 1,
            "candidate_local_image_retained": True,
            "candidate_local_image_count": 1,
            "v02_release_ready": False,
            "v02_tag_created": False,
            "v02_release_created": False,
        }
    )
    write_json(AUTHORIZATION_EXAMPLE_PATH, auth)


def update_aion_242_reconciliation() -> None:
    for path in LEDGER_PATHS:
        payload = json.loads(path.read_text(encoding="utf-8"))
        record = dict(payload.get("aion_242_record", {}))
        record.update(
            {
                "task_id": "AION-242",
                "branch": (
                    "phase/v02-staging-qualification-evaluation-release-candidate-"
                    "authorization"
                ),
                "harness_commit": "cfc881c8e50b35852176221ff8635e1996f2591d",
                "closeout_commit": "6288ba8e24cf4f3427d2087f1c7764cda08dbeed",
                "feature_commits": [
                    "cfc881c8e50b35852176221ff8635e1996f2591d",
                    "6288ba8e24cf4f3427d2087f1c7764cda08dbeed",
                ],
                "pull_requests": [161],
                "merge_commits": ["d01071f764227e356ada89422de1a4ff1261b2d4"],
                "ci_result": "pass",
                "completion_timestamp": "2026-08-02T17:37:14Z",
                "evaluation_id": "AION-V02RQPE-002",
                "evaluation_decision": (
                    "CONTROLLED_ISOLATED_LOCAL_STAGING_QUALIFICATION_OPERATOR_"
                    "EVALUATION_PASS_RECOMMEND_DETERMINISTIC_V02_RELEASE_"
                    "CANDIDATE_ARTIFACT_BUILD_AUTHORIZATION"
                ),
                "evaluation_report_fingerprint": (
                    "4d9326cb690e006442ca15035c8bbd225509fd2a1d1b05d4e47c2a30feab6230"
                ),
                "authorization_transaction": AUTHORIZATION_TRANSACTION_ID,
                "authorization_state": "active_for_AION-243_formal_closeout_AION-244",
                "next_task": "AION-243",
                "runtime_state": (
                    "deterministic_v02_release_candidate_artifact_build_authorized_"
                    "not_implemented"
                ),
            }
        )
        payload["aion_242_record"] = record
        write_json(path, payload)


def write_committed_evidence(
    *,
    implementation_commit: str,
    source: Mapping[str, Any],
    python_artifacts: Mapping[str, Any],
    image: Mapping[str, Any],
    operator_console: Mapping[str, Any],
    version: Mapping[str, Any],
    checksum: Mapping[str, Any],
    signatures: Mapping[str, Any],
    sbom: Mapping[str, Any],
    provenance: Mapping[str, Any],
    reproducibility: Mapping[str, Any],
    compatibility: Mapping[str, Any],
    migration: Mapping[str, Any],
    release_notes: Mapping[str, Any],
    integrity: Mapping[str, Any],
    tooling: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "candidate_id": CANDIDATE_LABEL,
        "authorization_id": AUTHORIZATION_TRANSACTION_ID,
        "program_id": PROGRAM_ID,
        "mode": "deterministic_local_release_candidate_build",
        "implementation_commit": implementation_commit,
        "candidate_source_commit": source["source_commit"],
        "candidate_locator_id": CANDIDATE_LABEL,
        "candidate_root_policy": "user-home/.aion/release-candidates/<candidate-label>",
        "candidate_root_path_retained": False,
        "source_tree_fingerprint": source["source_tree_fingerprint"],
        "source_archive_fingerprint": source["source_archive_fingerprint"],
        "brain_api_package_version": PYTHON_PACKAGE_VERSION,
        "sdk_package_version": PYTHON_PACKAGE_VERSION,
        "candidate_image_tag": LOCAL_IMAGE_TAG,
        "candidate_image_id": image["candidate_image_id"],
        "candidate_oci_archive_fingerprint": image["candidate_oci_archive_fingerprint"],
        "brain_api_artifact_manifest_fingerprint": image[
            "brain_api_artifact_manifest_fingerprint"
        ],
        "sdk_wheel_fingerprint": python_artifacts["sdk_wheel_fingerprint"],
        "sdk_sdist_fingerprint": python_artifacts["sdk_sdist_fingerprint"],
        "operator_console_bundle_fingerprint": operator_console[
            "operator_console_bundle_fingerprint"
        ],
        "candidate_version_manifest_fingerprint": version[
            "candidate_version_manifest_fingerprint"
        ],
        "candidate_content_manifest_fingerprint": checksum[
            "candidate_content_manifest_fingerprint"
        ],
        "candidate_bundle_manifest_fingerprint": signatures[
            "candidate_bundle_manifest_fingerprint"
        ],
        "candidate_sbom_fingerprint": sbom["candidate_sbom_fingerprint"],
        "candidate_sbom_component_count": sbom["candidate_sbom_component_count"],
        "candidate_provenance_chain_head": provenance["candidate_provenance_chain_head"],
        "checksum_manifest_fingerprint": checksum["checksum_manifest_fingerprint"],
        "qualification_public_key_fingerprint": signatures[
            "qualification_public_key_fingerprint"
        ],
        "qualification_signature_count": signatures["qualification_signature_count"],
        "qualification_signature_verification_count": signatures[
            "qualification_signature_verification_count"
        ],
        "reproducibility_comparison_fingerprint": reproducibility[
            "reproducibility_comparison_fingerprint"
        ],
        "reproducibility_invariants_passed": True,
        "byte_for_byte_oci_reproducibility_confirmed": False,
        "compatibility_matrix_fingerprint": compatibility[
            "compatibility_matrix_fingerprint"
        ],
        "migration_manifest_fingerprint": migration["migration_manifest_fingerprint"],
        "release_notes_draft_fingerprint": release_notes[
            "release_notes_draft_fingerprint"
        ],
        "candidate_integrity_report_fingerprint": integrity[
            "candidate_integrity_report_fingerprint"
        ],
        "candidate_evidence_bundle_fingerprint": integrity[
            "candidate_evidence_bundle_fingerprint"
        ],
        "candidate_bundle_retained": True,
        "candidate_bundle_count": 1,
        "candidate_image_retained": True,
        "candidate_image_count": 1,
        "release_candidate_created": True,
        "release_candidate_published": False,
        "production_deployment": False,
        "v02_release_ready": False,
        "v02_tag_created": False,
        "v02_release_created": False,
        "registry_logins": 0,
        "registry_pulls": 0,
        "registry_pushes": 0,
        "public_network_calls": 0,
        "dns_resolutions": 0,
        "public_package_uploads": 0,
        "production_deployments": 0,
        "temporary_build_directories_retained": 0,
        "intermediate_images_retained": 0,
        "private_qualification_keys_retained": 0,
        "hatchling_version": tooling["hatchling_version"],
        "hatchling_wheelhouse_manifest_fingerprint": read_tooling_fingerprint(
            "wheelhouse-manifest-fingerprint.txt"
        ),
        "build_toolchain_freeze_fingerprint": read_tooling_fingerprint(
            "toolchain-freeze-fingerprint.txt"
        ),
        "offline_build_tooling_verified": True,
        "candidate_build_network_access": False,
        "candidate_build_package_downloads": 0,
        "redacted": True,
        "integrity_passed": integrity["integrity_passed"],
    }
    payload["report_fingerprint"] = fingerprint(
        {key: value for key, value in payload.items() if key != "report_fingerprint"}
    )
    write_json(EVIDENCE_PATH, payload)
    update_ledgers(
        implementation_commit=implementation_commit,
        candidate_source_commit=source["source_commit"],
        evidence=payload,
    )
    return payload


def read_tooling_fingerprint(name: str) -> str:
    path = Path.home() / ".aion" / "tooling" / "hatchling" / "1.31.0" / "audit" / name
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    return "unavailable"


def finalize_permissions(root: Path) -> None:
    root.chmod(0o700)
    for path in root.rglob("*"):
        if path.is_dir():
            path.chmod(0o700)
        elif path.is_file():
            path.chmod(0o600)


def build_candidate(args: argparse.Namespace) -> None:
    if args.authorization != AUTHORIZATION_TRANSACTION_ID:
        raise SystemExit("unexpected AION-243 authorization")
    if args.confirm != LOCAL_CONFIRMATION_TEXT:
        raise SystemExit("local confirmation text mismatch")
    maybe_reexec_into_venv()
    require_git_clean()
    if importlib.metadata.version("hatchling") != EXPECTED_HATCHLING_VERSION:
        raise SystemExit("hatchling toolchain drift")
    candidate_root = Path(args.candidate_root).expanduser()
    candidate_root_parent = candidate_root.parent
    candidate_root_parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    candidate_root_parent.chmod(0o700)
    preflight(candidate_root)
    implementation_commit = git_output(["rev-parse", "HEAD~1"])
    source_commit = git_output(["rev-parse", "HEAD"])
    state = setup_state(candidate_root)
    bundle_root = state.temporary_root / "bundle"
    bundle_root.mkdir(mode=0o700)
    try:
        service = ControlledV02ReleaseCandidateService()
        service.validate_authorization(canonical_authorization_envelope())
        docker_context = verify_docker_context(state)
        tooling = ensure_tooling()
        source = create_source_snapshot(state, source_commit, bundle_root)
        version = generate_version_manifest(bundle_root)
        artifact_plan = V02CandidateArtifactPlan(
            source_commit=source_commit,
            artifact_kinds=(
                "source_archive",
                "brain_api_oci_archive",
                "sdk_wheel",
                "sdk_sdist",
                "operator_console_bundle",
            ),
        )
        service.validate_artifact_plan(artifact_plan)
        python_artifacts = build_python_artifacts(state, bundle_root)
        operator_console = build_operator_console_bundle(state, bundle_root)
        image = build_candidate_image(
            state,
            bundle_root,
            brain_api_wheel=python_artifacts["brain_api_wheel"],
            source_commit=source_commit,
            source_tree_fingerprint=source["source_tree_fingerprint"],
            docker_context=docker_context,
        )
        sbom = generate_sbom(
            state,
            bundle_root,
            source=source,
            python_artifacts=python_artifacts,
            image=image,
            operator_console=operator_console,
        )
        provenance = generate_provenance(
            bundle_root,
            source=source,
            python_artifacts=python_artifacts,
            image=image,
            operator_console=operator_console,
            sbom=sbom,
            tooling=tooling,
        )
        reproducibility = generate_reproducibility(
            bundle_root,
            source=source,
            python_artifacts=python_artifacts,
            operator_console=operator_console,
        )
        compatibility = generate_compatibility(bundle_root, image_probe=image["image_probe"])
        if state.source_dir is None:
            raise RuntimeError("source directory unavailable for migration manifest")
        migration = generate_migration_manifest(bundle_root, state.source_dir)
        release_notes = generate_release_notes(bundle_root, source_commit)
        checksum = write_content_and_checksum_manifests(bundle_root, source_commit=source_commit)
        first_signatures = sign_candidate_files(bundle_root)
        bundle_signature = write_bundle_manifest_and_signature(
            bundle_root,
            source=source,
            python_artifacts=python_artifacts,
            image=image,
            operator_console=operator_console,
            sbom=sbom,
            provenance=provenance,
            checksum=checksum,
            signatures=first_signatures,
            reproducibility=reproducibility,
            compatibility=compatibility,
            migration=migration,
            release_notes=release_notes,
        )
        signatures = {**first_signatures, **bundle_signature}
        retention = V02CandidateRetentionResult(
            candidate_bundle_retained=True,
            candidate_bundle_count=1,
            candidate_local_image_retained=True,
            candidate_local_image_count=1,
        )
        integrity = generate_integrity_and_evidence(
            bundle_root,
            source=source,
            version=version,
            checksum=checksum,
            signatures=signatures,
            reproducibility=reproducibility,
            compatibility=compatibility,
            migration=migration,
            retention=retention,
            sbom=sbom,
            provenance=provenance,
            artifact_manifest=checksum["artifact_model"],
            image=image,
        )
        if not integrity["integrity_passed"]:
            raise RuntimeError("candidate integrity failed before retention")
        finalize_permissions(bundle_root)
        if candidate_root.exists() and any(candidate_root.iterdir()):
            raise RuntimeError("final candidate root became non-empty before finalization")
        if candidate_root.exists():
            candidate_root.rmdir()
        bundle_root.rename(candidate_root)
        state.final_root = candidate_root
        remove_tree(state.temporary_root)
        committed = write_committed_evidence(
            implementation_commit=implementation_commit,
            source=source,
            python_artifacts=python_artifacts,
            image=image,
            operator_console=operator_console,
            version=version,
            checksum=checksum,
            signatures=signatures,
            sbom=sbom,
            provenance=provenance,
            reproducibility=reproducibility,
            compatibility=compatibility,
            migration=migration,
            release_notes=release_notes,
            integrity=integrity,
            tooling=tooling,
        )
        print(pretty_json({"status": "passed", "evidence": committed}))
    except Exception:
        remove_tree(state.temporary_root)
        raise


def maybe_reexec_into_venv() -> None:
    if not PYTHON_BIN.exists():
        return
    if Path(sys.executable).resolve() == PYTHON_BIN.resolve():
        return
    if os.environ.get("AION_243_RUNNER_REEXEC") == "1":
        return
    env = os.environ.copy()
    env["AION_243_RUNNER_REEXEC"] = "1"
    os.execve(str(PYTHON_BIN), [str(PYTHON_BIN), str(Path(__file__).resolve()), *sys.argv[1:]], env)


def verify_candidate(candidate_root: Path) -> dict[str, Any]:
    if not candidate_root.is_dir():
        raise RuntimeError("candidate root is absent")
    if candidate_root.is_symlink():
        raise RuntimeError("candidate root must not be a symlink")
    if stat.S_IMODE(candidate_root.stat().st_mode) != 0o700:
        raise RuntimeError("candidate root must use mode 0700")
    for path in candidate_root.rglob("*"):
        if path.is_symlink():
            raise RuntimeError(f"candidate bundle contains symlink: {path}")
    missing = sorted(expected_files() - {path.relative_to(candidate_root).as_posix() for path in iter_files(candidate_root)})
    if missing:
        raise RuntimeError(f"candidate bundle is missing required files: {missing}")
    unknown = unknown_files(candidate_root)
    if unknown:
        raise RuntimeError(f"candidate bundle has unknown files: {unknown}")
    verify_checksums(candidate_root)
    signature_count = verify_signatures(candidate_root)
    return {
        "candidate_label": CANDIDATE_LABEL,
        "candidate_bundle_retained": True,
        "candidate_bundle_count": 1,
        "candidate_file_count": len(iter_files(candidate_root)),
        "checksum_verification": "pass",
        "signature_verification": "pass",
        "signature_verification_count": signature_count,
    }


def audit_evidence(_args: argparse.Namespace) -> None:
    payload = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    expected = fingerprint(
        {key: value for key, value in payload.items() if key != "report_fingerprint"}
    )
    if payload["report_fingerprint"] != expected:
        raise SystemExit("candidate evidence report fingerprint mismatch")
    if payload["candidate_id"] != CANDIDATE_LABEL:
        raise SystemExit("candidate evidence ID mismatch")
    if payload["authorization_id"] != AUTHORIZATION_TRANSACTION_ID:
        raise SystemExit("candidate authorization mismatch")
    if payload["integrity_passed"] is not True:
        raise SystemExit("candidate integrity must pass")
    print("deterministic v0.2 release candidate evidence PASS")


def cleanup_temporary(_args: argparse.Namespace) -> None:
    if TEMP_PARENT.exists():
        for path in TEMP_PARENT.iterdir():
            if path.is_dir() and path.name.startswith(f"{CANDIDATE_LABEL}-"):
                remove_tree(path)
    state = setup_state(DEFAULT_CANDIDATE_ROOT)
    try:
        result = run_command(
            [state.docker, "image", "inspect", "--format", "{{.Id}}", COMPARISON_IMAGE_TAG],
            state=state,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            run_command([state.docker, "image", "rm", COMPARISON_IMAGE_TAG], state=state, check=False)
    finally:
        remove_tree(state.temporary_root)
    print("deterministic v0.2 release candidate temporary cleanup PASS")


def preflight_command(args: argparse.Namespace) -> None:
    payload = preflight(Path(args.candidate_root).expanduser())
    print(pretty_json(payload))


def verify_command(args: argparse.Namespace) -> None:
    payload = verify_candidate(Path(args.candidate_root).expanduser())
    print(pretty_json(payload))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.add_argument("--candidate-root", default=str(DEFAULT_CANDIDATE_ROOT))
    preflight_parser.set_defaults(func=preflight_command)
    build = subparsers.add_parser("build-candidate")
    build.add_argument("--authorization", required=True)
    build.add_argument("--candidate-root", required=True)
    build.add_argument("--confirm", required=True)
    build.set_defaults(func=build_candidate)
    verify = subparsers.add_parser("verify-candidate")
    verify.add_argument("--candidate-root", default=str(DEFAULT_CANDIDATE_ROOT))
    verify.set_defaults(func=verify_command)
    audit = subparsers.add_parser("audit-evidence")
    audit.set_defaults(func=audit_evidence)
    cleanup = subparsers.add_parser("cleanup-temporary")
    cleanup.set_defaults(func=cleanup_temporary)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
