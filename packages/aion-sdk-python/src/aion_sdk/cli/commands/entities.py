"""aionctl entity commands."""

from __future__ import annotations

from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

entities_app = typer.Typer(no_args_is_help=True, help="Entity registry commands.")
merge_app = typer.Typer(no_args_is_help=True, help="Entity merge proposal commands.")
split_app = typer.Typer(no_args_is_help=True, help="Entity split proposal commands.")


def install_entity_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install entity registry commands."""

    app.add_typer(entities_app, name="entities")
    entities_app.add_typer(merge_app, name="merge")
    entities_app.add_typer(split_app, name="split")

    @entities_app.command("create")
    def create(
        ctx: typer.Context,
        name: Annotated[str, typer.Option("--name")],
        entity_type: Annotated[str, typer.Option("--type")] = "generic",
        confidence: Annotated[float, typer.Option("--confidence")] = 0.5,
    ) -> None:
        """Create one entity."""
        payload: JSONDict = {
            "canonical_name": name,
            "entity_type": entity_type,
            "owner_scope": get_scope(ctx),
            "confidence": confidence,
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).entities.create(payload))

    @entities_app.command("query")
    def query(
        ctx: typer.Context,
        query_text: Annotated[str | None, typer.Option("--query")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        """Query entities."""
        payload: JSONDict = {"query": query_text, "scope": get_scope(ctx), "limit": limit}
        render(ctx, _client(get_client(ctx)).entities.query(payload))

    @entities_app.command("extract")
    @entities_app.command("extract-mentions")
    def extract(
        ctx: typer.Context,
        text: Annotated[str, typer.Option("--text")],
        source_type: Annotated[str, typer.Option("--source-type")] = "generic",
        source_id: Annotated[str, typer.Option("--source-id")] = "cli-input",
    ) -> None:
        """Extract entity mentions deterministically."""
        payload: JSONDict = {
            "source_type": source_type,
            "source_id": source_id,
            "text": text,
            "owner_scope": get_scope(ctx),
        }
        render(ctx, _client(get_client(ctx)).entities.extract_mentions(payload))

    @entities_app.command("resolve")
    def resolve(
        ctx: typer.Context,
        text: Annotated[str, typer.Option("--text")],
        source_type: Annotated[str, typer.Option("--source-type")] = "generic",
        source_id: Annotated[str, typer.Option("--source-id")] = "cli-input",
        dry_run: Annotated[bool, typer.Option("--dry-run/--write")] = True,
    ) -> None:
        """Resolve mentions to canonical entities."""
        payload: JSONDict = {
            "source_type": source_type,
            "source_id": source_id,
            "text": text,
            "owner_scope": get_scope(ctx),
            "dry_run": dry_run,
        }
        render(ctx, _client(get_client(ctx)).entities.resolve(payload))

    @entities_app.command("references")
    def references(
        ctx: typer.Context,
        entity_id: Annotated[str | None, typer.Option("--entity-id")] = None,
        concept_id: Annotated[str | None, typer.Option("--concept-id")] = None,
        source_type: Annotated[str | None, typer.Option("--source-type")] = None,
        source_id: Annotated[str | None, typer.Option("--source-id")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List reference links."""
        render(
            ctx,
            _client(get_client(ctx)).entities.list_references(
                get_scope(ctx),
                entity_id=entity_id,
                concept_id=concept_id,
                source_type=source_type,
                source_id=source_id,
                limit=limit,
            ),
        )

    @entities_app.command("propose-merge")
    def propose_merge(
        ctx: typer.Context,
        primary_entity_id: Annotated[str, typer.Option("--primary")],
        duplicate_entity_id: Annotated[str, typer.Option("--duplicate")],
        reason: Annotated[str, typer.Option("--reason")],
    ) -> None:
        """Propose an entity merge."""
        payload: JSONDict = {
            "primary_entity_id": primary_entity_id,
            "duplicate_entity_id": duplicate_entity_id,
            "reason": reason,
        }
        render(ctx, _client(get_client(ctx)).entities.propose_merge(payload, get_scope(ctx)))

    @merge_app.command("propose")
    def merge_propose(
        ctx: typer.Context,
        primary_entity_id: Annotated[str, typer.Option("--primary")],
        duplicate_entity_id: Annotated[str, typer.Option("--duplicate")],
        reason: Annotated[str, typer.Option("--reason")],
    ) -> None:
        """Propose an entity merge."""
        payload: JSONDict = {
            "primary_entity_id": primary_entity_id,
            "duplicate_entity_id": duplicate_entity_id,
            "reason": reason,
        }
        render(ctx, _client(get_client(ctx)).entities.propose_merge(payload, get_scope(ctx)))

    @merge_app.command("approve")
    def merge_approve(
        ctx: typer.Context,
        proposal_id: Annotated[str, typer.Argument()],
        reason: Annotated[str, typer.Option("--reason")],
        approved: Annotated[bool, typer.Option("--approved")] = False,
    ) -> None:
        """Approve an entity merge proposal."""
        render(
            ctx,
            _client(get_client(ctx)).entities.approve_merge(
                proposal_id,
                reason,
                get_scope(ctx),
                approval_present=approved,
            ),
        )

    @merge_app.command("reject")
    def merge_reject(
        ctx: typer.Context,
        proposal_id: Annotated[str, typer.Argument()],
        reason: Annotated[str, typer.Option("--reason")],
    ) -> None:
        """Reject an entity merge proposal."""
        render(
            ctx,
            _client(get_client(ctx)).entities.reject_merge(
                proposal_id,
                reason,
                get_scope(ctx),
            ),
        )

    @split_app.command("propose")
    def split_propose(
        ctx: typer.Context,
        entity_id: Annotated[str, typer.Option("--entity-id")],
        reason: Annotated[str, typer.Option("--reason")],
    ) -> None:
        """Propose an entity split."""
        payload: JSONDict = {"entity_id": entity_id, "reason": reason, "proposed_entities": []}
        render(ctx, _client(get_client(ctx)).entities.propose_split(payload, get_scope(ctx)))

    @split_app.command("approve")
    def split_approve(
        ctx: typer.Context,
        proposal_id: Annotated[str, typer.Argument()],
        reason: Annotated[str, typer.Option("--reason")],
        approved: Annotated[bool, typer.Option("--approved")] = False,
    ) -> None:
        """Approve an entity split proposal."""
        render(
            ctx,
            _client(get_client(ctx)).entities.approve_split(
                proposal_id,
                reason,
                get_scope(ctx),
                approval_present=approved,
            ),
        )

    @split_app.command("reject")
    def split_reject(
        ctx: typer.Context,
        proposal_id: Annotated[str, typer.Argument()],
        reason: Annotated[str, typer.Option("--reason")],
    ) -> None:
        """Reject an entity split proposal."""
        render(
            ctx,
            _client(get_client(ctx)).entities.reject_split(
                proposal_id,
                reason,
                get_scope(ctx),
            ),
        )


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)
