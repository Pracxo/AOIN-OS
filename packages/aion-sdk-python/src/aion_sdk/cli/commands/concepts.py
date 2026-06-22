"""aionctl concept commands."""

from __future__ import annotations

from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

concepts_app = typer.Typer(no_args_is_help=True, help="Concept registry commands.")


def install_concept_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install concept registry commands."""

    app.add_typer(concepts_app, name="concepts")

    @concepts_app.command("create")
    def create(
        ctx: typer.Context,
        name: Annotated[str, typer.Option("--name")],
        description: Annotated[str, typer.Option("--description")],
        concept_type: Annotated[str, typer.Option("--type")] = "generic",
    ) -> None:
        """Create one concept."""
        payload: JSONDict = {
            "name": name,
            "concept_type": concept_type,
            "description": description,
            "owner_scope": get_scope(ctx),
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).concepts.create(payload))

    @concepts_app.command("list")
    def list_concepts(
        ctx: typer.Context,
        query: Annotated[str | None, typer.Option("--query")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List concepts."""
        render(
            ctx,
            _client(get_client(ctx)).concepts.list_concepts(
                get_scope(ctx),
                query=query,
                limit=limit,
            ),
        )


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)
