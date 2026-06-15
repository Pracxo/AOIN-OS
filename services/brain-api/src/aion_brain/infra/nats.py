"""NATS readiness boundary."""

import asyncio

from nats.aio.client import Client as NATSClient


async def check_nats_async(nats_url: str, timeout_seconds: float = 1.0) -> bool:
    """Return whether NATS accepts a short-lived connection."""
    client = NATSClient()
    try:
        await client.connect(
            servers=[nats_url],
            connect_timeout=max(1, int(timeout_seconds)),
            max_reconnect_attempts=0,
        )
        return bool(client.is_connected)
    except Exception:
        return False
    finally:
        if client.is_connected:
            await client.close()


def check_nats(nats_url: str, timeout_seconds: float = 1.0) -> bool:
    """Run the async NATS readiness check from a synchronous API boundary."""
    try:
        return asyncio.run(check_nats_async(nats_url, timeout_seconds=timeout_seconds))
    except Exception:
        return False
