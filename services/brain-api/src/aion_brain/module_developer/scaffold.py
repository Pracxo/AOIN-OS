"""Generic module scaffold generator."""

import json
from datetime import UTC, datetime

from aion_brain.contracts.capabilities import CapabilityManifest
from aion_brain.contracts.module_developer import ModuleScaffold, ModuleScaffoldRequest


class ModuleScaffoldGenerator:
    """Create generic non-executable module package files."""

    def scaffold(self, request: ModuleScaffoldRequest) -> ModuleScaffold:
        """Generate static starter files only."""

        manifest = CapabilityManifest(
            module_id=request.module_id,
            version="0.1.0",
            capabilities=[
                {
                    "capability_id": f"{request.module_id}.generic.capability_{index}",
                    "name": f"generic.capability_{index}",
                    "description": "Generic example capability contract.",
                    "input_schema": {"type": "object", "additionalProperties": True},
                    "output_schema": {"type": "object", "additionalProperties": True},
                    "risk_level": "low",
                    "permissions_required": ["capability.invoke"],
                    "memory_read_scopes": [],
                    "memory_write_scopes": [],
                    "execution_mode": "sync",
                    "timeout_seconds": 5,
                    "audit_level": "full",
                    "metadata": {"generated_by": "aion_module_scaffold"},
                }
                for index in range(1, request.capability_count + 1)
            ],
            permissions_required=["capability.invoke"],
            memory_read_scopes=[],
            memory_write_scopes=[],
            events_subscribed=[],
            events_published=[],
            execution_mode="sync",
        )
        readme = (
            f"# {request.package_name}\n\n"
            "Generic AION module package scaffold. This package contains only "
            "contracts and static test metadata. It contains no executable code, "
            "provider SDK integration, external endpoint, or domain workflow.\n"
        )
        manifest_yaml = _manifest_yaml(manifest)
        tests = [
            {
                "test_type": "schema_validation",
                "name": "manifest schemas are objects",
                "input": {"manifest": manifest.model_dump(mode="json")},
                "expected": {"valid": True},
            },
            {
                "test_type": "dry_run_invocation",
                "name": "dry run stays non-executable",
                "input": {"mode": "dry_run"},
                "expected": {"external_execution": False},
            },
        ]
        files = {
            "aion.module.yaml": manifest_yaml,
            "aion.module.json": json.dumps(manifest.model_dump(mode="json"), indent=2) + "\n",
            "README.md": readme,
            "contract_tests.json": json.dumps(tests, indent=2) + "\n",
        }
        return ModuleScaffold(
            module_id=request.module_id,
            package_name=request.package_name,
            files=files,
            manifest=manifest,
            readme=readme,
            created_at=datetime.now(UTC),
        )


def _manifest_yaml(manifest: CapabilityManifest) -> str:
    data = manifest.model_dump(mode="json")
    lines = [
        f"module_id: {data['module_id']}",
        f"version: {data['version']}",
        "capabilities:",
    ]
    for capability in manifest.capabilities:
        lines.extend(
            [
                f"  - capability_id: {capability['capability_id']}",
                f"    name: {capability['name']}",
                f"    description: {capability['description']}",
                f"    risk_level: {capability['risk_level']}",
                f"    execution_mode: {capability['execution_mode']}",
                f"    timeout_seconds: {capability['timeout_seconds']}",
                f"    audit_level: {capability['audit_level']}",
            ]
        )
        lines.append("    permissions_required:")
        for permission in capability["permissions_required"]:
            lines.append(f"      - {permission}")
        lines.append("    input_schema:")
        lines.append("      type: object")
        lines.append("      additionalProperties: true")
        lines.append("    output_schema:")
        lines.append("      type: object")
        lines.append("      additionalProperties: true")
    lines.extend(
        [
            "permissions_required:",
            "  - capability.invoke",
            "memory_read_scopes: []",
            "memory_write_scopes: []",
            "events_subscribed: []",
            "events_published: []",
            "execution_mode: sync",
        ]
    )
    return "\n".join(lines) + "\n"
