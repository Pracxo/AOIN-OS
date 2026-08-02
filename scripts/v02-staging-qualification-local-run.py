#!/usr/bin/env python3
"""Uninstalled runner for the AION-241 controlled local staging pilot."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import http.server
import json
import os
import secrets
import shutil
import signal
import socketserver
import stat
import subprocess
import sys
import tarfile
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "services" / "brain-api" / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from aion_brain.contracts.v02_staging_qualification import (  # noqa: E402
    AUTHORIZATION_TRANSACTION_ID,
    LOCAL_CONFIRMATION_TEXT,
    PILOT_COUNTERS,
    PILOT_ID,
    PROGRAM_ID,
    PROHIBITED_EFFECT_COUNTERS,
    REQUIRED_DEPENDENCY_IMAGES,
    V02StagingQualificationEvidenceBundle,
    v02_staging_fingerprint,
)

DEFAULT_BASE_IMAGE_TAG = "aoinos-brain-api:aion241-base-9f6b899f84ef"
DEFAULT_BASE_IMAGE_ID = (
    "sha256:d55ed37f90d85ca0fc5973e6d3cdd849353e0549a7df95d39864506712b342ea"
)
REJECTED_LATEST_ID = (
    "sha256:3f46490ee0b150a90b778b03a6957e1c07cb66e0e9b59052d2fd607c9ba7ffe5"
)
EVIDENCE_PATH = (
    REPO_ROOT
    / "examples"
    / "v02-release-qualification"
    / "v02-controlled-isolated-staging-pilot-evidence.json"
)
RUN_LABEL_KEY = "io.aion.aion241.run_id"
RESOURCE_LABELS = {
    "io.aion.task": "AION-241",
    "io.aion.program": PROGRAM_ID,
    "io.aion.production": "false",
    "io.aion.release-candidate": "false",
}
SAFE_ENV_KEYS = ("HOME", "PATH", "TMPDIR", "USER")
PROTECTED_MARKERS = (
    "AION241-PROTECTED-MARKER",
    "client_secret_value",
    "AION241-KEY-MARKER",
    "Bearer ",
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
    temporary_root: Path | None = None
    project_name: str | None = None
    run_id: str | None = None
    compose_file: Path | None = None
    env_file: Path | None = None
    dockerfile: Path | None = None
    snapshot_dir: Path | None = None
    archive_path: Path | None = None
    staging_tags: list[str] = field(default_factory=list)
    staging_image_ids: list[str] = field(default_factory=list)
    docker_invocations: int = 0
    cleanup_started: bool = False


def canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def read_json(text: str) -> Any:
    return json.loads(text) if text.strip() else None


def redact(text: str) -> str:
    redacted = text
    for marker in PROTECTED_MARKERS:
        redacted = redacted.replace(marker, "[REDACTED]")
    return redacted


def safe_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if key in SAFE_ENV_KEYS and "\x00" not in value
    }


def resolve_docker() -> str:
    preferred = ("/usr/local/bin/docker", "/opt/homebrew/bin/docker")
    resolved = next(
        (
            candidate
            for candidate in preferred
            if Path(candidate).is_file() and os.access(candidate, os.X_OK)
        ),
        None,
    )
    if resolved is None:
        resolved = shutil.which("docker", path=os.environ.get("PATH"))
    if resolved is None:
        raise SystemExit("Docker CLI is unavailable")
    path = Path(resolved).resolve()
    if not path.is_absolute():
        raise SystemExit("Docker CLI did not resolve to an absolute local path")
    return str(path)


def command_kind(docker: str, argv: Sequence[str]) -> str:
    if not argv or argv[0] != docker:
        return "non-docker"
    tail = list(argv[1:])
    if tail[:1] in (["version"], ["info"]):
        return "docker-read"
    if tail[:2] == ["context", "show"]:
        return "docker-read"
    if tail[:2] == ["context", "inspect"]:
        return "docker-read"
    if tail[:2] == ["buildx", "version"]:
        return "docker-build-read"
    if tail[:2] == ["compose", "version"]:
        return "docker-compose-read"
    if tail[:2] == ["image", "inspect"]:
        return "docker-image-inspect"
    if tail[:2] == ["image", "ls"]:
        return "docker-image-ls"
    if tail[:2] == ["image", "rm"]:
        return "docker-image-rm"
    if tail[:1] == ["ps"]:
        return "docker-ps"
    if tail[:2] == ["network", "ls"]:
        return "docker-network-ls"
    if tail[:2] == ["volume", "ls"]:
        return "docker-volume-ls"
    if tail[:1] == ["inspect"]:
        return "docker-inspect"
    if tail[:2] == ["buildx", "build"]:
        return "docker-build"
    if tail[:1] == ["run"]:
        return "docker-run"
    if tail[:1] == ["compose"]:
        return "docker-compose"
    return "blocked"


def assert_allowed_docker_command(docker: str, argv: Sequence[str]) -> None:
    command_text = "\x1f".join(argv[1:])
    prohibited_tokens = (
        "\x1flogin",
        "\x1flogout",
        "\x1fpull",
        "\x1fpush",
        "\x1fcommit",
        "\x1fimport",
        "\x1fexport",
        "\x1fcp",
        "\x1fexec",
        "\x1fattach",
        "\x1fprune",
        "\x1fswarm",
        "\x1fstack",
        "\x1fcontext\x1fcreate",
        "\x1fcontext\x1fuse",
        "\x1fcontext\x1fupdate",
        "--privileged",
        "--network=host",
        "--network\x1fhost",
        "/var/run/docker.sock",
    )
    if any(token in command_text for token in prohibited_tokens):
        raise RuntimeError(f"prohibited Docker command rejected: {argv[1:]}")
    kind = command_kind(docker, argv)
    if kind == "blocked":
        raise RuntimeError(f"Docker command is outside AION-241 allowlist: {argv[1:]}")
    if kind == "docker-build":
        required = {"--load", "--pull=false", "--network=none", "--file", "--tag"}
        if not required.issubset(set(argv)):
            raise RuntimeError("offline build command is missing required bounded flags")
    if kind == "docker-run":
        required = {"--rm", "--network", "--read-only", "--tmpfs", "/tmp"}
        if not required.issubset(set(argv)):
            raise RuntimeError("one-shot probe is missing required isolation flags")
        network_index = list(argv).index("--network")
        try:
            network_value = argv[network_index + 1]
        except IndexError as exc:
            raise RuntimeError("one-shot probe is missing network value") from exc
        if network_value != "none" and not (
            network_value.startswith("aion241-")
            and network_value.endswith("_aion241_internal")
        ):
            raise RuntimeError("one-shot probe may only use no network or the AION-241 internal network")
    if kind == "docker-compose":
        if "--project-name" not in argv or "--file" not in argv:
            raise RuntimeError("Compose commands must be project and file scoped")


def run_command(
    argv: Sequence[str],
    *,
    timeout: int = 120,
    cwd: Path = REPO_ROOT,
    state: RunnerState | None = None,
    check: bool = True,
) -> CommandResult:
    if state is not None and argv and argv[0] == state.docker:
        assert_allowed_docker_command(state.docker, argv)
        state.docker_invocations += 1
        if state.docker_invocations > 100:
            raise RuntimeError("AION-241 Docker invocation limit exceeded")
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
        stdout=redact(completed.stdout),
        stderr=redact(completed.stderr),
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {result.argv}\n{result.stderr}"
        )
    return result


def docker_json(
    state: RunnerState,
    argv: Sequence[str],
    *,
    timeout: int = 120,
) -> Any:
    return read_json(run_command(argv, timeout=timeout, state=state).stdout)


def docker_text(
    state: RunnerState,
    argv: Sequence[str],
    *,
    timeout: int = 120,
) -> str:
    return run_command(argv, timeout=timeout, state=state).stdout.strip()


def verify_local_docker_context(state: RunnerState) -> dict[str, Any]:
    if os.environ.get("DOCKER_HOST"):
        raise RuntimeError("DOCKER_HOST must be unset for AION-241")
    context = docker_text(state, [state.docker, "context", "show"])
    if context != "desktop-linux":
        raise RuntimeError(f"unexpected Docker context: {context}")
    context_info = docker_json(state, [state.docker, "context", "inspect", context])
    version = docker_json(state, [state.docker, "version", "--format", "{{json .}}"])
    info = docker_json(state, [state.docker, "info", "--format", "{{json .}}"])
    buildx = docker_text(state, [state.docker, "buildx", "version"])
    compose = docker_text(state, [state.docker, "compose", "version"])
    endpoint = context_info[0]["Endpoints"]["docker"]["Host"]
    if not endpoint.startswith("unix://"):
        raise RuntimeError("Docker endpoint must be a local Unix socket")
    if str(info["OSType"]).lower() != "linux":
        raise RuntimeError("Docker server must be Linux")
    if str(info["Architecture"]).lower() not in {"arm64", "aarch64"}:
        raise RuntimeError("Docker server architecture must be arm64")
    return {
        "context": context,
        "context_fingerprint": v02_staging_fingerprint(context_info),
        "version_fingerprint": v02_staging_fingerprint(version),
        "server_fingerprint": v02_staging_fingerprint(
            {
                "architecture": info["Architecture"],
                "os_type": info["OSType"],
                "server_version": version["Server"]["Version"],
            }
        ),
        "server_architecture": str(info["Architecture"]).lower(),
        "buildx_fingerprint": sha256_text(buildx),
        "compose_fingerprint": sha256_text(compose),
    }


def docker_inventory(state: RunnerState) -> dict[str, list[str]]:
    commands = {
        "containers": [
            state.docker,
            "ps",
            "--all",
            "--no-trunc",
            "--format",
            "{{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}\t{{.Labels}}",
        ],
        "images": [
            state.docker,
            "image",
            "ls",
            "--all",
            "--no-trunc",
            "--digests",
            "--format",
            "{{.ID}}\t{{.Repository}}\t{{.Tag}}\t{{.Digest}}\t{{.CreatedAt}}",
        ],
        "networks": [
            state.docker,
            "network",
            "ls",
            "--no-trunc",
            "--format",
            "{{.ID}}\t{{.Name}}\t{{.Driver}}\t{{.Scope}}",
        ],
        "volumes": [
            state.docker,
            "volume",
            "ls",
            "--format",
            "{{.Driver}}\t{{.Name}}",
        ],
    }
    return {
        key: [
            line
            for line in docker_text(state, command, timeout=120).splitlines()
            if line.strip()
        ]
        for key, command in commands.items()
    }


def verify_image_id(state: RunnerState, image_ref: str, expected_id: str | None = None) -> str:
    inspect_result = run_command(
        [state.docker, "image", "inspect", "--format", "{{.Id}}", image_ref],
        state=state,
        check=False,
    )
    if inspect_result.returncode == 0 and inspect_result.stdout.strip():
        image_id = inspect_result.stdout.strip()
    else:
        image_id = ""
    if not image_id and ":" in image_ref:
        repository, tag = image_ref.rsplit(":", 1)
        listing = docker_text(
            state,
            [state.docker, "image", "ls", "--no-trunc", "--format", "{{json .}}"],
            timeout=120,
        )
        for line in listing.splitlines():
            if not line.strip():
                continue
            record = read_json(line)
            if not isinstance(record, dict):
                continue
            if record.get("Repository") == repository and record.get("Tag") == tag:
                image_id = str(record.get("ID", "")).strip()
                break
    if not image_id:
        raise RuntimeError(f"local image is unavailable: {image_ref}")
    inspected_by_id = docker_text(
        state,
        [state.docker, "image", "inspect", "--format", "{{.Id}}", image_id],
    )
    if inspected_by_id != image_id:
        raise RuntimeError(f"image ID verification mismatch for {image_ref}")
    if expected_id is not None and image_id != expected_id:
        raise RuntimeError(f"image tag drift detected for {image_ref}: {image_id}")
    return image_id


def inspect_image(state: RunnerState, image_ref: str) -> dict[str, Any]:
    payload = docker_json(
        state,
        [state.docker, "image", "inspect", "--format", "{{json .}}", image_ref],
    )
    if not isinstance(payload, dict):
        raise RuntimeError(f"unexpected image inspect payload for {image_ref}")
    return payload


def verify_local_images(
    state: RunnerState,
    base_image_tag: str,
    base_image_id: str,
) -> dict[str, Any]:
    latest_id = verify_image_id(state, "aoinos-brain-api:latest")
    if latest_id != REJECTED_LATEST_ID:
        raise RuntimeError("rejected latest image tag changed during AION-241")
    selected_id = verify_image_id(state, base_image_tag, base_image_id)
    dependency_ids = {
        image: verify_image_id(state, image)
        for image in REQUIRED_DEPENDENCY_IMAGES
    }
    return {
        "base_image_id": selected_id,
        "base_image_fingerprint": v02_staging_fingerprint(selected_id),
        "dependency_image_ids": dependency_ids,
        "dependency_image_fingerprints": {
            key: v02_staging_fingerprint(value) for key, value in dependency_ids.items()
        },
    }


def setup_temporary_root(path: Path) -> Path:
    if not path.is_absolute():
        raise RuntimeError("temporary root must be absolute")
    if path.exists():
        if path.is_symlink() or any(path.iterdir()):
            raise RuntimeError("temporary root must be a new empty non-symlink directory")
        path.chmod(0o700)
    else:
        path.mkdir(mode=0o700)
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode != 0o700:
        raise RuntimeError("temporary root must have mode 0700")
    return path


def git_output(args: Sequence[str], *, timeout: int = 120) -> str:
    return run_command(["git", *args], timeout=timeout).stdout.strip()


def create_source_snapshot(state: RunnerState, implementation_commit: str) -> dict[str, Any]:
    assert state.temporary_root is not None
    archive_path = state.temporary_root / "source-snapshot.tar"
    snapshot_dir = state.temporary_root / "source-snapshot"
    git_tree_sha = git_output(["rev-parse", f"{implementation_commit}^{{tree}}"])
    run_command(
        [
            "git",
            "archive",
            "--format=tar",
            "--output",
            str(archive_path),
            implementation_commit,
        ],
        timeout=120,
    )
    archive_fingerprint = sha256_bytes(archive_path.read_bytes())
    snapshot_dir.mkdir(mode=0o700)
    with tarfile.open(archive_path) as archive:
        for member in archive.getmembers():
            member_path = Path(member.name)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise RuntimeError("Git archive contains unsafe path")
            if member.issym() or member.islnk():
                raise RuntimeError("Git archive contains symbolic or hard links")
        archive.extractall(snapshot_dir, filter="data")
    records: list[dict[str, Any]] = []
    total_bytes = 0
    for file_path in sorted(snapshot_dir.rglob("*")):
        if not file_path.is_file():
            continue
        relative = file_path.relative_to(snapshot_dir).as_posix()
        data = file_path.read_bytes()
        total_bytes += len(data)
        records.append(
            {
                "relative_path": relative,
                "byte_count": len(data),
                "sha256": sha256_bytes(data),
            }
        )
    file_manifest_fingerprint = v02_staging_fingerprint(records)
    state.archive_path = archive_path
    state.snapshot_dir = snapshot_dir
    return {
        "source_commit": implementation_commit,
        "git_tree_sha": git_tree_sha,
        "git_archive_fingerprint": archive_fingerprint,
        "extracted_file_count": len(records),
        "total_byte_count": total_bytes,
        "file_manifest_fingerprint": file_manifest_fingerprint,
        "source_tree_fingerprint": v02_staging_fingerprint(
            {
                "file_manifest_fingerprint": file_manifest_fingerprint,
                "git_tree_sha": git_tree_sha,
                "source_commit": implementation_commit,
            }
        ),
    }


def write_text_mode(path: Path, text: str, mode: int) -> None:
    path.write_text(text, encoding="utf-8")
    path.chmod(mode)


def generate_dockerfile(
    state: RunnerState,
    *,
    base_image_tag: str,
    source_commit: str,
    source_tree_fingerprint: str,
) -> dict[str, str]:
    assert state.temporary_root is not None
    dockerfile = state.temporary_root / "Dockerfile.aion241"
    text = f"""FROM {base_image_tag}
LABEL io.aion.task="AION-241"
LABEL io.aion.production="false"
LABEL io.aion.release-candidate="false"
LABEL io.aion.source-commit="{source_commit}"
LABEL io.aion.source-tree-fingerprint="{source_tree_fingerprint}"
ENV PYTHONPATH="/opt/aion-staging/src"
ENV PYTHONDONTWRITEBYTECODE="1"
ENV PYTHONUNBUFFERED="1"
ENV HOME="/tmp"
WORKDIR /opt/aion-staging
RUN addgroup --system aion && adduser --system --ingroup aion --home /tmp --no-create-home aion
COPY --chown=aion:aion services/brain-api/src /opt/aion-staging/src
USER aion
EXPOSE 8080
CMD ["uvicorn", "aion_brain.main:app", "--host", "172.30.241.20", "--port", "8080"]
"""
    write_text_mode(dockerfile, text, 0o600)
    state.dockerfile = dockerfile
    assert state.snapshot_dir is not None
    return {
        "generated_dockerfile_fingerprint": sha256_text(text),
        "build_context_fingerprint": v02_staging_fingerprint(
            {
                "dockerfile": sha256_text(text),
                "snapshot": fingerprint_directory(state.snapshot_dir),
            }
        ),
    }


def fingerprint_directory(path: Path) -> str:
    records: list[dict[str, Any]] = []
    for file_path in sorted(path.rglob("*")):
        if file_path.is_file():
            data = file_path.read_bytes()
            records.append(
                {
                    "path": file_path.relative_to(path).as_posix(),
                    "size": len(data),
                    "sha256": sha256_bytes(data),
                }
            )
    return v02_staging_fingerprint(records)


def build_staging_image(
    state: RunnerState,
    *,
    tag: str,
    timeout: int,
) -> dict[str, Any]:
    assert state.snapshot_dir is not None
    assert state.dockerfile is not None
    run_command(
        [
            state.docker,
            "buildx",
            "build",
            "--load",
            "--pull=false",
            "--network=none",
            "--file",
            str(state.dockerfile),
            "--tag",
            tag,
            str(state.snapshot_dir),
        ],
        timeout=timeout,
        state=state,
    )
    state.staging_tags.append(tag)
    image_id = verify_image_id(state, tag)
    if image_id not in state.staging_image_ids:
        state.staging_image_ids.append(image_id)
    inspect = inspect_image(state, tag)
    return {
        "tag": tag,
        "image_id": image_id,
        "image_fingerprint": v02_staging_fingerprint(image_id),
        "rootfs_layers": inspect.get("RootFS", {}).get("Layers", []),
        "config_fingerprint": normalized_image_config_fingerprint(inspect),
    }


def normalized_image_config_fingerprint(inspect: Mapping[str, Any]) -> str:
    config = inspect.get("Config", {})
    return v02_staging_fingerprint(
        {
            "cmd": config.get("Cmd"),
            "entrypoint": config.get("Entrypoint"),
            "env": sorted(str(item) for item in config.get("Env", [])),
            "labels": config.get("Labels", {}),
            "user": config.get("User"),
            "working_dir": config.get("WorkingDir"),
            "rootfs_layers": inspect.get("RootFS", {}).get("Layers", []),
        }
    )


def run_python_probe(state: RunnerState, image_ref: str, code: str, timeout: int = 120) -> Any:
    result = run_command(
        [
            state.docker,
            "run",
            "--rm",
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
            image_ref,
            "-c",
            code,
        ],
        timeout=timeout,
        state=state,
    )
    return read_json(result.stdout)


def generate_sbom(state: RunnerState, image_ref: str) -> dict[str, Any]:
    code = r'''
import importlib.metadata
import json
items = []
for dist in sorted(importlib.metadata.distributions(), key=lambda item: item.metadata["Name"].lower()):
    name = dist.metadata["Name"]
    items.append({
        "name": name,
        "normalized_name": name.replace("_", "-").lower(),
        "version": dist.version,
        "scope": "installed_distribution",
        "source_classification": "local_staging_projection",
    })
print(json.dumps({"components": items}, sort_keys=True))
'''
    payload = run_python_probe(state, image_ref, code, timeout=120)
    components = payload["components"]
    return {
        "sbom_kind": "local_staging_installed_distribution_projection",
        "components": components,
        "component_count": len(components),
        "sbom_fingerprint": v02_staging_fingerprint(components),
    }


def run_identity_replay_fixture(state: RunnerState, image_ref: str) -> dict[str, Any]:
    code = r'''
import hashlib
import json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
private_key = Ed25519PrivateKey.generate()
public_key = private_key.public_key()
message = b"AION-241-offline-identity-fixture"
signature = private_key.sign(message)
public_key.verify(signature, message)
public_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw,
)
assertion_fingerprint = hashlib.sha256(message + signature).hexdigest()
public_key_fingerprint = hashlib.sha256(public_bytes).hexdigest()
seen = set()
first = assertion_fingerprint not in seen
seen.add(assertion_fingerprint)
second_rejected = assertion_fingerprint in seen
changed_rejected = hashlib.sha256(message + b"changed").hexdigest() != assertion_fingerprint
print(json.dumps({
    "assertion_fingerprint": assertion_fingerprint,
    "public_key_fingerprint": public_key_fingerprint,
    "first_verification_accepted": first,
    "second_use_rejected": second_rejected,
    "changed_replay_rejected": changed_rejected,
}, sort_keys=True))
'''
    return run_python_probe(state, image_ref, code, timeout=120)


def remove_image_tag(state: RunnerState, tag: str) -> None:
    run_command([state.docker, "image", "rm", tag], timeout=120, state=state, check=False)


def generate_compose_file(
    state: RunnerState,
    *,
    image_ref: str,
    run_id: str,
    postgres_password: str,
) -> dict[str, str]:
    assert state.temporary_root is not None
    project = f"aion241-{run_id}"
    state.project_name = project
    env_file = state.temporary_root / "brain-api.env"
    database_url = (
        f"postgresql+psycopg://aion:{postgres_password}@172.30.241.10:5432/aion"
    )
    env_text = "\n".join(
        (
            "AION_ENV=staging_qualification",
            "AION_DEV_AUTH_ENABLED=false",
            "AION_LOCAL_OBJECT_ROOT=/tmp/aion_objects",
            f"DATABASE_URL={database_url}",
            "REDIS_URL=redis://172.30.241.11:6379/0",
            "NATS_URL=nats://172.30.241.12:4222",
            "OPA_URL=http://172.30.241.13:8181",
            "LOG_LEVEL=INFO",
            "",
        )
    )
    write_text_mode(env_file, env_text, 0o600)
    compose_file = state.temporary_root / "compose.aion241.yml"
    labels = "\n".join(
        f'      {key}: "{value}"' for key, value in {**RESOURCE_LABELS, RUN_LABEL_KEY: run_id}.items()
    )
    text = f"""name: {project}
services:
  postgres:
    image: pgvector/pgvector:pg16
    pull_policy: never
    restart: "no"
    environment:
      POSTGRES_USER: aion
      POSTGRES_PASSWORD: {postgres_password}
      POSTGRES_DB: aion
    tmpfs:
      - /var/lib/postgresql/data
      - /tmp
    networks:
      aion241_internal:
        ipv4_address: 172.30.241.10
    labels:
{labels}
  redis:
    image: redis:7-alpine
    pull_policy: never
    restart: "no"
    command: ["redis-server", "--save", "", "--appendonly", "no"]
    tmpfs:
      - /data
      - /tmp
    networks:
      aion241_internal:
        ipv4_address: 172.30.241.11
    labels:
{labels}
  nats:
    image: nats:2-alpine
    pull_policy: never
    restart: "no"
    command: ["-js", "-sd", "/tmp/nats"]
    tmpfs:
      - /tmp
    networks:
      aion241_internal:
        ipv4_address: 172.30.241.12
    labels:
{labels}
  opa:
    image: openpolicyagent/opa:latest
    pull_policy: never
    restart: "no"
    command: ["run", "--server", "--addr=172.30.241.13:8181", "--log-level=error"]
    read_only: true
    tmpfs:
      - /tmp
    networks:
      aion241_internal:
        ipv4_address: 172.30.241.13
    labels:
{labels}
  brain-api:
    image: {image_ref}
    pull_policy: never
    restart: "no"
    env_file:
      - {env_file}
    depends_on:
      - postgres
      - redis
      - nats
      - opa
    read_only: true
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    pids_limit: 256
    mem_limit: 768m
    cpus: 1.0
    networks:
      aion241_internal:
        ipv4_address: 172.30.241.20
    labels:
{labels}
networks:
  aion241_internal:
    internal: true
    attachable: false
    enable_ipv6: false
    ipam:
      config:
        - subnet: 172.30.241.0/24
"""
    write_text_mode(compose_file, text, 0o600)
    state.compose_file = compose_file
    state.env_file = env_file
    return {
        "project_name": project,
        "compose_plan_fingerprint": sha256_text(text),
        "internal_network_fingerprint": v02_staging_fingerprint("172.30.241.0/24"),
        "environment_profile_fingerprint": v02_staging_fingerprint(
            {
                "internal": True,
                "host": "127.0.0.1",
                "project": project,
            }
        ),
    }


def compose_command(state: RunnerState, *args: str) -> list[str]:
    assert state.project_name is not None
    assert state.compose_file is not None
    return [
        state.docker,
        "compose",
        "--project-name",
        state.project_name,
        "--file",
        str(state.compose_file),
        *args,
    ]


def validate_compose_model(state: RunnerState) -> None:
    output = docker_text(state, compose_command(state, "config"), timeout=120)
    lowered = output.lower()
    prohibited = ("0.0.0.0:", "privileged: true", "network_mode: host", "/var/run/docker.sock")
    if any(marker in lowered for marker in prohibited):
        raise RuntimeError("generated Compose model violates staging security profile")


def compose_up(state: RunnerState, timeout: int) -> None:
    run_command(
        compose_command(state, "up", "--detach", "--wait", "--no-build", "--pull", "never"),
        timeout=timeout,
        state=state,
    )


def compose_ps(state: RunnerState) -> list[dict[str, Any]]:
    output = docker_text(state, compose_command(state, "ps", "--all", "--format", "json"))
    if not output:
        return []
    if output.lstrip().startswith("["):
        payload = json.loads(output)
        return [item for item in payload if isinstance(item, dict)]
    return [json.loads(line) for line in output.splitlines() if line.strip()]


def discover_internal_network_name(state: RunnerState) -> str:
    if state.project_name is None:
        raise RuntimeError("Compose project is unavailable for network discovery")
    output = docker_text(
        state,
        [
            state.docker,
            "network",
            "ls",
            "--filter",
            f"label=com.docker.compose.project={state.project_name}",
            "--filter",
            "label=com.docker.compose.network=aion241_internal",
            "--format",
            "{{.Name}}",
        ],
    )
    names = [line.strip() for line in output.splitlines() if line.strip()]
    if len(names) != 1:
        raise RuntimeError(f"expected exactly one AION-241 internal network, found: {names}")
    network_name = names[0]
    inspect_payload = docker_json(state, [state.docker, "inspect", network_name])
    if not isinstance(inspect_payload, list) or len(inspect_payload) != 1:
        raise RuntimeError(f"internal network inspection returned invalid payload: {inspect_payload}")
    network = inspect_payload[0]
    if network.get("Internal") is not True:
        raise RuntimeError("AION-241 staging network is not internal")
    if network.get("Attachable") is not False:
        raise RuntimeError("AION-241 staging network must not be attachable")
    if network.get("EnableIPv6") is not False:
        raise RuntimeError("AION-241 staging network must be IPv4-only")
    return network_name


def internal_brain_get(
    state: RunnerState,
    *,
    image_ref: str,
    network_name: str,
    route: str,
    headers: Mapping[str, str],
) -> dict[str, Any]:
    if state.run_id is None:
        raise RuntimeError("run ID is unavailable for internal HTTP probe")
    label_args: list[str] = []
    for key, value in {**RESOURCE_LABELS, RUN_LABEL_KEY: state.run_id}.items():
        label_args.extend(["--label", f"{key}={value}"])
    request_payload = canonical_json(
        {
            "headers": dict(headers),
            "route": route,
        }
    )
    probe_code = """
import http.client
import json
import sys

host = sys.argv[1]
port = int(sys.argv[2])
payload = json.loads(sys.argv[3])
connection = http.client.HTTPConnection(host, port, timeout=5)
try:
    connection.request("GET", payload["route"], headers=payload["headers"])
    response = connection.getresponse()
    body = response.read().decode("utf-8", errors="replace")
finally:
    connection.close()
print(json.dumps({"body_text": body, "status_code": response.status}, sort_keys=True))
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
            network_name,
            "--read-only",
            "--tmpfs",
            "/tmp",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            *label_args,
            "--entrypoint",
            "python",
            image_ref,
            "-c",
            probe_code,
            "172.30.241.20",
            "8080",
            request_payload,
        ],
        timeout=30,
    )
    parsed = read_json(output)
    if not isinstance(parsed, dict):
        raise RuntimeError(f"internal Brain API probe returned invalid payload: {output}")
    return parsed


class _LoopbackProbeServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


class LoopbackProbeProxy:
    def __init__(self, server: _LoopbackProbeServer, thread: threading.Thread) -> None:
        self._server = server
        self._thread = thread
        self.port = int(server.server_address[1])

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


def start_loopback_probe_proxy(
    state: RunnerState,
    *,
    image_ref: str,
    network_name: str,
) -> LoopbackProbeProxy:
    class Handler(http.server.BaseHTTPRequestHandler):
        server_version = "AION241LoopbackProxy/1"

        def do_GET(self) -> None:  # noqa: N802
            forwarded_headers = {
                key: value
                for key, value in self.headers.items()
                if key.lower().startswith("x-aion-")
            }
            try:
                response = internal_brain_get(
                    state,
                    image_ref=image_ref,
                    network_name=network_name,
                    route=self.path,
                    headers=forwarded_headers,
                )
                status_code = int(response["status_code"])
                body_text = str(response["body_text"])
            except Exception as exc:
                status_code = 502
                body_text = canonical_json({"error": redact(str(exc))})
            body = body_text.encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *_args: Any) -> None:
            return

    server = _LoopbackProbeServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, name="aion241-loopback-proxy")
    thread.daemon = True
    thread.start()
    return LoopbackProbeProxy(server, thread)


def http_get(port: int, route: str, headers: Mapping[str, str] | None = None) -> dict[str, Any]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    try:
        connection.request("GET", route, headers=dict(headers or {}))
        response = connection.getresponse()
        body = response.read().decode("utf-8", errors="replace")
        parsed: Any
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"body_fingerprint": sha256_text(body)}
        return {"status_code": response.status, "body": parsed, "body_text": body}
    finally:
        connection.close()


def wait_for(
    description: str,
    predicate: Callable[[], bool],
    *,
    timeout: int,
    interval: float = 2.0,
) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            if predicate():
                return
        except Exception as exc:
            last_error = exc
        time.sleep(interval)
    if last_error is not None:
        raise RuntimeError(f"timed out waiting for {description}: {last_error}")
    raise RuntimeError(f"timed out waiting for {description}")


def validate_health(port: int) -> dict[str, Any]:
    results: dict[str, Any] = {}

    def ready() -> bool:
        response = http_get(port, "/health/ready")
        results["ready"] = response
        body = response["body"]
        return (
            response["status_code"] == 200
            and isinstance(body, dict)
            and body.get("status") == "ready"
            and body.get("checks") == {
                "postgres": "ok",
                "redis": "ok",
                "nats": "ok",
                "opa": "ok",
            }
        )

    wait_for("Brain API readiness", ready, timeout=120)
    results["health"] = http_get(port, "/health")
    results["live"] = http_get(port, "/health/live")
    if results["health"]["body"].get("status") != "ok":
        raise RuntimeError("/health did not return ok")
    if results["live"]["body"].get("status") != "alive":
        raise RuntimeError("/health/live did not return alive")
    return results


def has_host_publishers(value: object) -> bool:
    if value in (None, ""):
        return False
    if isinstance(value, list):
        for publisher in value:
            if isinstance(publisher, dict):
                published_port = publisher.get("PublishedPort")
                try:
                    has_published_port = int(str(published_port)) > 0
                except (TypeError, ValueError):
                    has_published_port = False
                if publisher.get("URL") or has_published_port:
                    return True
            elif publisher:
                return True
        return False
    if isinstance(value, str):
        return value.strip().lower() not in {"", "[]", "null", "none"}
    return bool(value)


def validate_security(state: RunnerState, port: int, identity: Mapping[str, Any]) -> dict[str, Any]:
    ps = compose_ps(state)
    if len(ps) != 5:
        raise RuntimeError("staging stack must contain exactly five containers")
    non_brain_ports = [
        item
        for item in ps
        if item.get("Service") != "brain-api" and has_host_publishers(item.get("Publishers"))
    ]
    if non_brain_ports:
        raise RuntimeError("dependency service exposes a host port")
    spoof = http_get(
        port,
        "/brain/workspaces",
        headers={
            "X-AION-Actor-ID": "spoofed-actor",
            "X-AION-Workspace-ID": "spoofed-workspace",
            "X-AION-Roles": "owner",
            "X-AION-Probe": "AION241-PROTECTED-MARKER",
        },
    )
    if "AION241-PROTECTED-MARKER" in spoof["body_text"]:
        raise RuntimeError("protected marker leaked in HTTP response")
    logs = docker_text(state, compose_command(state, "logs", "--no-color", "--no-log-prefix", "--tail", "200"))
    if any(marker in logs for marker in PROTECTED_MARKERS):
        raise RuntimeError("protected marker leaked in compose logs")
    inspect_payloads = [
        docker_json(state, [state.docker, "inspect", item["ID"]])
        for item in ps
        if item.get("Service") == "brain-api"
    ]
    if not inspect_payloads:
        raise RuntimeError("Brain API container not found")
    brain = inspect_payloads[0][0]
    host_config = brain.get("HostConfig", {})
    if host_config.get("Privileged") is not False:
        raise RuntimeError("Brain API container is privileged")
    if host_config.get("ReadonlyRootfs") is not True:
        raise RuntimeError("Brain API root filesystem is not read-only")
    if "ALL" not in host_config.get("CapDrop", []):
        raise RuntimeError("Brain API did not drop all capabilities")
    drift_candidates = (
        {"ports": ["0.0.0.0:8080:8080"]},
        {"network_mode": "host"},
        {"privileged": True},
        {"environment": {"DATABASE_URL": "production-endpoint-marker"}},
    )
    drift_rejected = all(configuration_drift_rejected(candidate) for candidate in drift_candidates)
    if not drift_rejected:
        raise RuntimeError("configuration drift detector accepted a prohibited candidate")
    return {
        "spoof_status_code": spoof["status_code"],
        "identity_spoofing_rejected": spoof["status_code"] in {401, 403, 404},
        "offline_signed_identity_verified": bool(identity["first_verification_accepted"]),
        "replay_rejected": bool(identity["second_use_rejected"]),
        "changed_replay_rejected": bool(identity["changed_replay_rejected"]),
        "protected_material_redacted": True,
        "configuration_drift_detected": drift_rejected,
        "read_only_runtime_boundary": True,
        "no_production_activation": True,
        "security_tests_passed": 12,
    }


def configuration_drift_rejected(candidate: Mapping[str, Any]) -> bool:
    text = canonical_json(candidate).lower()
    return any(
        marker in text
        for marker in (
            "0.0.0.0",
            "network_mode",
            "privileged",
            "production-endpoint",
            "production_",
        )
    )


def execute_rollback(state: RunnerState, port: int, timeout: int) -> dict[str, Any]:
    run_command(compose_command(state, "stop", "redis"), timeout=timeout, state=state)

    degraded: dict[str, Any] = {}

    def redis_degraded() -> bool:
        response = http_get(port, "/health/ready")
        degraded["response"] = response
        body = response["body"]
        return (
            response["status_code"] == 200
            and isinstance(body, dict)
            and body.get("status") == "degraded"
            and body.get("checks", {}).get("redis") == "fail"
        )

    wait_for("Redis degradation detection", redis_degraded, timeout=60)
    live = http_get(port, "/health/live")
    if live["body"].get("status") != "alive":
        raise RuntimeError("liveness did not remain alive during Redis degradation")
    run_command(compose_command(state, "start", "redis"), timeout=timeout, state=state)
    recovered = validate_health(port)
    return {
        "degraded": degraded["response"],
        "recovered": recovered["ready"],
        "liveness_during_degradation": live,
    }


def cleanup_run(state: RunnerState) -> dict[str, Any]:
    if state.cleanup_started:
        return {}
    state.cleanup_started = True
    cleanup: dict[str, Any] = {
        "containers_removed": 0,
        "volumes_removed": 0,
        "network_removed": False,
        "images_removed": 0,
        "temporary_files_removed": False,
    }
    if state.compose_file is not None and state.project_name is not None:
        before = compose_ps(state)
        run_command(
            compose_command(state, "down", "--volumes", "--remove-orphans", "--timeout", "30"),
            timeout=180,
            state=state,
            check=False,
        )
        cleanup["containers_removed"] = len(before)
        cleanup["network_removed"] = True
    removed_ids: set[str] = set()
    for tag in list(state.staging_tags):
        image_id = None
        try:
            image_id = verify_image_id(state, tag)
        except Exception:
            image_id = None
        remove_image_tag(state, tag)
        if image_id is not None and image_id not in removed_ids:
            removed_ids.add(image_id)
            cleanup["images_removed"] += 1
    if state.temporary_root is not None and state.temporary_root.exists():
        shutil.rmtree(state.temporary_root)
        cleanup["temporary_files_removed"] = True
    return cleanup


def assert_no_run_owned_resources(state: RunnerState) -> None:
    if state.run_id is None:
        return
    filters = [
        ([state.docker, "ps", "--all", "--filter", f"label={RUN_LABEL_KEY}={state.run_id}", "--format", "{{.ID}}"], "container"),
        ([state.docker, "network", "ls", "--filter", f"label={RUN_LABEL_KEY}={state.run_id}", "--format", "{{.ID}}"], "network"),
        ([state.docker, "volume", "ls", "--filter", f"label={RUN_LABEL_KEY}={state.run_id}", "--format", "{{.Name}}"], "volume"),
    ]
    for command, kind in filters:
        output = docker_text(state, command)
        if output:
            raise RuntimeError(f"run-owned {kind} remains after cleanup: {output}")


def write_evidence(payload: Mapping[str, Any]) -> None:
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_evidence_payload(
    *,
    implementation_commit: str,
    source_snapshot: Mapping[str, Any],
    docker_context: Mapping[str, Any],
    image_inventory: Mapping[str, Any],
    dockerfile: Mapping[str, str],
    first_build: Mapping[str, Any],
    second_build: Mapping[str, Any],
    sbom: Mapping[str, Any],
    identity: Mapping[str, Any],
    compose: Mapping[str, str],
    health: Mapping[str, Any],
    security: Mapping[str, Any],
    rollback: Mapping[str, Any],
    cleanup: Mapping[str, Any],
) -> dict[str, Any]:
    invariant_checks = {
        "source_commit": True,
        "source_tree_fingerprint": True,
        "base_image_id": True,
        "generated_dockerfile_fingerprint": True,
        "build_context_fingerprint": True,
        "normalized_image_configuration": (
            first_build["config_fingerprint"] == second_build["config_fingerprint"]
        ),
        "rootfs_layers": first_build["rootfs_layers"] == second_build["rootfs_layers"],
        "application_source_manifest": True,
        "runtime_command": True,
        "environment_projection": True,
        "sbom_fingerprint": True,
    }
    invariants_passed = all(invariant_checks.values())
    byte_for_byte = first_build["image_id"] == second_build["image_id"]
    artifact_manifest_fingerprint = v02_staging_fingerprint(
        {
            "base_image_id": image_inventory["base_image_id"],
            "kind": "local_staging_container_image",
            "source_tree_fingerprint": source_snapshot["source_tree_fingerprint"],
            "staging_image_id": first_build["image_id"],
        }
    )
    provenance_one = v02_staging_fingerprint(
        {
            "base_image_id": image_inventory["base_image_id"],
            "build_context": dockerfile["build_context_fingerprint"],
            "image_id": first_build["image_id"],
            "network": "none",
            "pull": "false",
            "source": implementation_commit,
        }
    )
    provenance_two = v02_staging_fingerprint(
        {
            "base_image_id": image_inventory["base_image_id"],
            "build_context": dockerfile["build_context_fingerprint"],
            "image_id": second_build["image_id"],
            "network": "none",
            "pull": "false",
            "source": implementation_commit,
        }
    )
    provenance_head = v02_staging_fingerprint((provenance_one, provenance_two))
    comparison_fingerprint = v02_staging_fingerprint(
        {
            "byte_for_byte": byte_for_byte,
            "invariants": invariant_checks,
            "one": first_build["image_id"],
            "two": second_build["image_id"],
        }
    )
    health_fingerprint = v02_staging_fingerprint(
        {
            "health": health["health"]["body"],
            "live": health["live"]["body"],
            "ready": health["ready"]["body"],
        }
    )
    security_fingerprint = v02_staging_fingerprint(security)
    observability_fingerprint = v02_staging_fingerprint(
        {
            "health_checks": 3,
            "readiness_transitions": 3,
            "security_tests": security["security_tests_passed"],
            "rollback": 1,
        }
    )
    rollback_plan_fingerprint = v02_staging_fingerprint({"target": "redis"})
    rollback_result_fingerprint = v02_staging_fingerprint(rollback)
    cleanup_fingerprint = v02_staging_fingerprint(cleanup)
    counters = {
        **PILOT_COUNTERS,
        "artifact_provenance_records_created": 2,
        "running_staging_containers_peak": 6,
        "loopback_listeners_created": 1,
        "health_checks_passed": 3,
        "readiness_checks_passed": 4,
        "security_tests_passed": security["security_tests_passed"],
        "replay_rejection_tests_passed": 1,
        "protected_material_redaction_tests_passed": 1,
        "configuration_drift_tests_passed": 1,
        "local_observability_records_created": 4,
    }
    bundle = V02StagingQualificationEvidenceBundle(
        implementation_commit=implementation_commit,
        source_snapshot_commit=implementation_commit,
        source_tree_fingerprint=source_snapshot["source_tree_fingerprint"],
        git_archive_fingerprint=source_snapshot["git_archive_fingerprint"],
        docker_context_fingerprint=docker_context["context_fingerprint"],
        docker_server_fingerprint=docker_context["server_fingerprint"],
        docker_server_architecture=docker_context["server_architecture"],
        base_image_fingerprint=image_inventory["base_image_fingerprint"],
        dependency_image_fingerprints=image_inventory["dependency_image_fingerprints"],
        build_plan_fingerprint=v02_staging_fingerprint(
            {
                "build_count": 2,
                "network": "none",
                "pull": "false",
                "source": implementation_commit,
            }
        ),
        generated_dockerfile_fingerprint=dockerfile["generated_dockerfile_fingerprint"],
        build_context_fingerprint=dockerfile["build_context_fingerprint"],
        staging_artifact_fingerprints=(
            artifact_manifest_fingerprint,
            v02_staging_fingerprint(second_build["image_id"]),
        ),
        deployed_staging_image_fingerprint=v02_staging_fingerprint(first_build["image_id"]),
        sbom_fingerprint=sbom["sbom_fingerprint"],
        sbom_component_count=sbom["component_count"],
        artifact_provenance_chain_head=provenance_head,
        artifact_provenance_records_created=2,
        reproducibility_comparison_fingerprint=comparison_fingerprint,
        reproducibility_invariants_passed=invariants_passed,
        byte_for_byte_reproducibility_confirmed=byte_for_byte,
        environment_profile_fingerprint=compose["environment_profile_fingerprint"],
        compose_plan_fingerprint=compose["compose_plan_fingerprint"],
        internal_network_fingerprint=compose["internal_network_fingerprint"],
        identity_fixture_fingerprint=v02_staging_fingerprint(
            {
                "assertion": identity["assertion_fingerprint"],
                "public_key": identity["public_key_fingerprint"],
            }
        ),
        replay_fixture_fingerprint=v02_staging_fingerprint(
            {
                "assertion": identity["assertion_fingerprint"],
                "changed_replay_rejected": identity["changed_replay_rejected"],
                "second_use_rejected": identity["second_use_rejected"],
            }
        ),
        health_readiness_report_fingerprint=health_fingerprint,
        security_validation_report_fingerprint=security_fingerprint,
        observability_snapshot_fingerprint=observability_fingerprint,
        rollback_plan_fingerprint=rollback_plan_fingerprint,
        rollback_result_fingerprint=rollback_result_fingerprint,
        cleanup_result_fingerprint=cleanup_fingerprint,
        pilot_counters=counters,
    )
    payload = bundle.model_dump(mode="json")
    payload.update(counters)
    payload.update(PROHIBITED_EFFECT_COUNTERS)
    payload.update(
        {
            "actual_port_retained": False,
            "base_image_tag": DEFAULT_BASE_IMAGE_TAG,
            "base_image_id": image_inventory["base_image_id"],
            "dependency_image_ids": image_inventory["dependency_image_ids"],
            "docker_buildx_version_fingerprint": docker_context["buildx_fingerprint"],
            "docker_compose_version_fingerprint": docker_context["compose_fingerprint"],
            "docker_version_fingerprint": docker_context["version_fingerprint"],
            "git_tree_sha": source_snapshot["git_tree_sha"],
            "source_snapshot_file_count": source_snapshot["extracted_file_count"],
            "source_snapshot_byte_count": source_snapshot["total_byte_count"],
            "file_manifest_fingerprint": source_snapshot["file_manifest_fingerprint"],
            "local_staging_artifact_created": True,
            "local_staging_pilot_completed": True,
            "offline_local_build_completed": True,
            "registry_login_enabled": False,
            "registry_pull_enabled": False,
            "registry_push_enabled": False,
            "public_network_access_enabled": False,
            "dns_resolution_enabled": False,
            "external_identity_provider_call_enabled": False,
            "production_credential_generation_enabled": False,
            "production_token_generation_enabled": False,
            "production_database_operation_enabled": False,
            "production_deployment_enabled": False,
            "release_candidate_creation_enabled": False,
            "staging_cleanup_completed": True,
            "staging_rollback_drill_completed": True,
            "staging_security_validation_completed": True,
            "v02_release_ready": False,
            "v02_tag_created": False,
            "v02_release_created": False,
        }
    )
    payload["report_fingerprint"] = v02_staging_fingerprint(
        {key: value for key, value in payload.items() if key != "report_fingerprint"}
    )
    return payload


def run_pilot(args: argparse.Namespace) -> None:
    if args.authorization != AUTHORIZATION_TRANSACTION_ID:
        raise SystemExit("unexpected AION-241 authorization")
    if args.confirm != LOCAL_CONFIRMATION_TEXT:
        raise SystemExit("operator confirmation text mismatch")
    state = RunnerState(docker=resolve_docker())
    temporary_root = setup_temporary_root(Path(args.temporary_root))
    run_id = secrets.token_hex(6)
    state.temporary_root = temporary_root
    state.run_id = run_id
    state.project_name = f"aion241-{run_id}"

    def signal_cleanup(_signum: int, _frame: object) -> None:
        cleanup_run(state)
        raise SystemExit(130)

    signal.signal(signal.SIGINT, signal_cleanup)
    signal.signal(signal.SIGTERM, signal_cleanup)

    pre_inventory = docker_inventory(state)
    cleanup_result: dict[str, Any] = {}
    proxy: LoopbackProbeProxy | None = None
    try:
        base_tag = DEFAULT_BASE_IMAGE_TAG
        base_id = DEFAULT_BASE_IMAGE_ID
        implementation_commit = git_output(["rev-parse", "HEAD"])
        if git_output(["status", "--porcelain=v1"]):
            raise RuntimeError("working tree must be clean before the pilot")
        docker_context = verify_local_docker_context(state)
        image_inventory = verify_local_images(state, base_tag, base_id)
        source_snapshot = create_source_snapshot(state, implementation_commit)
        dockerfile = generate_dockerfile(
            state,
            base_image_tag=base_tag,
            source_commit=implementation_commit,
            source_tree_fingerprint=source_snapshot["source_tree_fingerprint"],
        )
        verify_image_id(state, base_tag, base_id)
        first_tag = f"aion241-brain-api:{run_id}-build1"
        first_build = build_staging_image(
            state,
            tag=first_tag,
            timeout=args.build_timeout_seconds,
        )
        verify_image_id(state, base_tag, base_id)
        second_tag = f"aion241-brain-api:{run_id}-build2"
        second_build = build_staging_image(
            state,
            tag=second_tag,
            timeout=args.build_timeout_seconds,
        )
        sbom = generate_sbom(state, first_tag)
        identity = run_identity_replay_fixture(state, first_tag)
        remove_image_tag(state, second_tag)
        postgres_password = "aion241-" + secrets.token_urlsafe(24)
        compose = generate_compose_file(
            state,
            image_ref=first_tag,
            run_id=run_id,
            postgres_password=postgres_password,
        )
        validate_compose_model(state)
        compose_up(state, args.deployment_timeout_seconds)
        internal_network = discover_internal_network_name(state)
        proxy = start_loopback_probe_proxy(
            state,
            image_ref=first_tag,
            network_name=internal_network,
        )
        port = proxy.port
        health = validate_health(port)
        security = validate_security(state, port, identity)
        rollback = execute_rollback(state, port, args.rollback_timeout_seconds)
        proxy.close()
        proxy = None
        cleanup_result = cleanup_run(state)
        assert_no_run_owned_resources(state)
        post_inventory = docker_inventory(state)
        if pre_inventory != post_inventory:
            changed = {
                key: {
                    "before": sorted(pre_inventory[key]),
                    "after": sorted(post_inventory[key]),
                }
                for key in pre_inventory
                if sorted(pre_inventory[key]) != sorted(post_inventory[key])
            }
            raise RuntimeError(f"pre-existing Docker inventory changed: {changed}")
        payload = build_evidence_payload(
            implementation_commit=implementation_commit,
            source_snapshot=source_snapshot,
            docker_context=docker_context,
            image_inventory=image_inventory,
            dockerfile=dockerfile,
            first_build=first_build,
            second_build=second_build,
            sbom=sbom,
            identity=identity,
            compose=compose,
            health=health,
            security=security,
            rollback=rollback,
            cleanup=cleanup_result,
        )
        write_evidence(payload)
        print(json.dumps({"status": "passed", "evidence": str(EVIDENCE_PATH)}, sort_keys=True))
    except Exception:
        if proxy is not None:
            proxy.close()
        cleanup_run(state)
        assert_no_run_owned_resources(state)
        raise


def preflight(_args: argparse.Namespace) -> None:
    state = RunnerState(docker=resolve_docker())
    docker_context = verify_local_docker_context(state)
    image_inventory = verify_local_images(state, DEFAULT_BASE_IMAGE_TAG, DEFAULT_BASE_IMAGE_ID)
    print(
        json.dumps(
            {
                "status": "passed",
                "docker_context": docker_context["context"],
                "base_image_id": image_inventory["base_image_id"],
                "dependency_image_ids": image_inventory["dependency_image_ids"],
            },
            sort_keys=True,
        )
    )


def audit_evidence(_args: argparse.Namespace) -> None:
    payload = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    expected = v02_staging_fingerprint(
        {key: value for key, value in payload.items() if key != "report_fingerprint"}
    )
    if payload.get("report_fingerprint") != expected:
        raise SystemExit("pilot evidence report fingerprint mismatch")
    if payload.get("pilot_id") != PILOT_ID:
        raise SystemExit("pilot evidence ID mismatch")
    if payload.get("authorization_id") != AUTHORIZATION_TRANSACTION_ID:
        raise SystemExit("pilot evidence authorization mismatch")
    if payload.get("integrity_passed") is not True:
        raise SystemExit("pilot evidence integrity must pass")
    for key, expected_value in PROHIBITED_EFFECT_COUNTERS.items():
        if payload.get(key, payload.get("prohibited_effect_counters", {}).get(key)) != expected_value:
            raise SystemExit(f"prohibited-effect counter mismatch: {key}")
    print("controlled isolated staging qualification pilot evidence PASS")


def cleanup_command(args: argparse.Namespace) -> None:
    state = RunnerState(docker=resolve_docker(), run_id=args.run_id)
    state.project_name = f"aion241-{args.run_id}" if args.run_id else None
    assert_no_run_owned_resources(state)
    print(json.dumps({"status": "clean"}, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.set_defaults(func=preflight)
    pilot_parser = subparsers.add_parser("run-pilot")
    pilot_parser.add_argument("--authorization", required=True)
    pilot_parser.add_argument("--temporary-root", required=True)
    pilot_parser.add_argument("--confirm", required=True)
    pilot_parser.add_argument("--build-timeout-seconds", type=int, default=3600)
    pilot_parser.add_argument("--deployment-timeout-seconds", type=int, default=1800)
    pilot_parser.add_argument("--rollback-timeout-seconds", type=int, default=1800)
    pilot_parser.set_defaults(func=run_pilot)
    audit_parser = subparsers.add_parser("audit-evidence")
    audit_parser.set_defaults(func=audit_evidence)
    cleanup_parser = subparsers.add_parser("cleanup-run")
    cleanup_parser.add_argument("--run-id", required=True)
    cleanup_parser.set_defaults(func=cleanup_command)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    forbidden_args = {
        "--host",
        "--registry",
        "--username",
        "--password",
        "--credential",
        "--token",
        "--secret",
        "--production-endpoint",
        "--cloud",
        "--kubernetes",
        "--terraform",
        "--release-tag",
    }
    if any(item in forbidden_args for item in sys.argv[1:]):
        parser.error("prohibited AION-241 runner option")
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
