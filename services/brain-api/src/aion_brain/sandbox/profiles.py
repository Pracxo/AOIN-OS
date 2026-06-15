"""Sandbox profile helpers."""

from aion_brain.contracts.sandbox import ResourceLimits


def default_resource_limits() -> ResourceLimits:
    """Return conservative local no-op defaults."""
    return ResourceLimits(
        cpu_millis=500,
        memory_mb=128,
        timeout_seconds=30,
        max_output_bytes=65536,
        max_files=0,
        max_file_bytes=0,
    )


__all__ = ["default_resource_limits"]
