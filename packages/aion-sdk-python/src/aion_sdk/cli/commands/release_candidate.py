"""aionctl release candidate commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

rc_app = typer.Typer(no_args_is_help=True, help="Release candidate gate helpers.")
matrices_app = typer.Typer(
    no_args_is_help=False,
    invoke_without_command=True,
    help="RC verification matrix commands.",
)


def install_release_candidate_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install release candidate commands."""

    app.add_typer(rc_app, name="rc")
    rc_app.add_typer(matrices_app, name="matrices")

    @rc_app.command("create")
    def create_candidate(
        ctx: typer.Context,
        rc_key: Annotated[str, typer.Option("--rc-key")],
        version: Annotated[str, typer.Option("--version")] = "0.1.0",
        source_ref: Annotated[str | None, typer.Option("--source-ref")] = None,
        commit_ref: Annotated[str | None, typer.Option("--commit-ref")] = None,
        tag_ref: Annotated[str | None, typer.Option("--tag-ref")] = None,
    ) -> None:
        """Create a local release candidate record."""

        payload: JSONDict = {
            "rc_key": rc_key,
            "version": version,
            "owner_scope": get_scope(ctx),
        }
        _set(payload, "source_ref", source_ref)
        _set(payload, "commit_ref", commit_ref)
        _set(payload, "tag_ref", tag_ref)
        render(ctx, _client(get_client(ctx)).release_candidate.create_candidate(payload))

    @rc_app.command("candidates")
    def candidates(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        version: Annotated[str | None, typer.Option("--version")] = None,
        release_ready: Annotated[bool | None, typer.Option("--release-ready")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List release candidates."""

        render(
            ctx,
            _client(get_client(ctx)).release_candidate.list_candidates(
                get_scope(ctx),
                status=status,
                version=version,
                release_ready=release_ready,
                limit=limit,
            ),
        )

    @matrices_app.callback()
    def matrices(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List RC verification matrices."""

        if ctx.invoked_subcommand is None:
            render(
                ctx,
                _client(get_client(ctx)).release_candidate.list_matrices(
                    get_scope(ctx),
                    status=status,
                    limit=limit,
                ),
            )

    @matrices_app.command("seed")
    def seed_matrices(
        ctx: typer.Context,
        dry_run: Annotated[
            bool,
            typer.Option("--dry-run/--apply", help="Preview by default; --apply persists."),
        ] = True,
    ) -> None:
        """Seed default RC verification matrices."""

        render(
            ctx,
            _client(get_client(ctx)).release_candidate.seed_default_matrices(
                get_scope(ctx),
                dry_run=dry_run,
            ),
        )

    @rc_app.command("run")
    def run_gate(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        rc_key: Annotated[str | None, typer.Option("--rc-key")] = None,
        version: Annotated[str | None, typer.Option("--version")] = None,
        dry_run: Annotated[
            bool,
            typer.Option("--dry-run/--controlled", help="Run in dry-run mode by default."),
        ] = True,
        service_checks: Annotated[
            bool,
            typer.Option("--service-checks/--no-service-checks"),
        ] = True,
        docker_smoke: Annotated[
            bool,
            typer.Option("--docker-smoke/--no-docker-smoke"),
        ] = False,
    ) -> None:
        """Run the local RC gate."""

        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("mode", "dry_run" if dry_run else "controlled")
        payload.setdefault("run_service_checks", service_checks)
        payload.setdefault("include_docker_smoke", docker_smoke)
        _set(payload, "rc_key", rc_key)
        _set(payload, "version", version)
        render(ctx, _client(get_client(ctx)).release_candidate.run_gate(payload))

    @rc_app.command("run-get")
    def get_run(
        ctx: typer.Context,
        rc_run_id: Annotated[str, typer.Option("--id")],
    ) -> None:
        """Get one RC gate run."""

        render(
            ctx,
            _client(get_client(ctx)).release_candidate.get_run(rc_run_id, get_scope(ctx)),
        )

    @rc_app.command("findings")
    def findings(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        blocking: Annotated[bool | None, typer.Option("--blocking")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List RC findings."""

        render(
            ctx,
            _client(get_client(ctx)).release_candidate.list_findings(
                get_scope(ctx),
                status=status,
                severity=severity,
                blocking=blocking,
                limit=limit,
            ),
        )

    @rc_app.command("dismiss-finding")
    def dismiss_finding(
        ctx: typer.Context,
        finding_id: Annotated[str, typer.Option("--id")],
        reason: Annotated[str, typer.Option("--reason")] = "dismissed",
    ) -> None:
        """Dismiss an RC finding."""

        render(
            ctx,
            _client(get_client(ctx)).release_candidate.dismiss_finding(
                finding_id,
                get_scope(ctx),
                reason=reason,
            ),
        )

    @rc_app.command("reports")
    def reports(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        version: Annotated[str | None, typer.Option("--version")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        """List RC reports."""

        render(
            ctx,
            _client(get_client(ctx)).release_candidate.list_reports(
                get_scope(ctx),
                status=status,
                version=version,
                limit=limit,
            ),
        )

    @rc_app.command("evidence")
    def evidence(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        """List RC evidence packs."""

        render(
            ctx,
            _client(get_client(ctx)).release_candidate.list_evidence_packs(
                get_scope(ctx),
                status=status,
                limit=limit,
            ),
        )

    @rc_app.command("query")
    def query(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        version: Annotated[str | None, typer.Option("--version")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """Query RC-owned records."""

        payload = _load_payload(payload_file)
        payload.setdefault("scope", get_scope(ctx))
        payload.setdefault("limit", limit)
        _set(payload, "status", status)
        _set(payload, "version", version)
        render(ctx, _client(get_client(ctx)).release_candidate.query(payload))


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    try:
        parsed = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise typer.BadParameter("payload must be a JSON object")
    return cast(JSONDict, parsed)


def _set(payload: dict[str, object], key: str, value: object | None) -> None:
    if value is not None:
        payload[key] = value


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)


__all__ = ["install_release_candidate_commands"]
