"""Capability adapter boundaries."""

from aion_brain.capabilities.mcp_adapter import MCPAdapter
from aion_brain.capabilities.registry import CapabilityProtocolAdapter, CapabilityRegistry

__all__ = ["CapabilityProtocolAdapter", "CapabilityRegistry", "MCPAdapter"]
