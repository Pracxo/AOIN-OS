"""Redis readiness boundary."""

from redis import Redis


def check_redis(redis_url: str, timeout_seconds: float = 1.0) -> bool:
    """Return whether Redis responds to ping."""
    client = Redis.from_url(
        redis_url,
        socket_connect_timeout=timeout_seconds,
        socket_timeout=timeout_seconds,
    )
    try:
        return bool(client.ping())
    except Exception:
        return False
    finally:
        client.close()
