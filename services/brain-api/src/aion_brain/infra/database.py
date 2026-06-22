"""Postgres readiness boundary."""

from sqlalchemy import create_engine, text


def check_postgres(database_url: str, timeout_seconds: float = 1.0) -> bool:
    """Return whether Postgres can answer a minimal query."""
    engine = create_engine(
        database_url,
        connect_args={"connect_timeout": max(1, int(timeout_seconds))},
        pool_pre_ping=True,
    )
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        engine.dispose()
