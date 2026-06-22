"""Module scaffold generator tests."""

from aion_brain.contracts.module_developer import ModuleScaffoldRequest
from aion_brain.module_developer.scaffold import ModuleScaffoldGenerator


def test_scaffold_generator_creates_generic_files() -> None:
    scaffold = ModuleScaffoldGenerator().scaffold(
        ModuleScaffoldRequest(
            module_id="generic.example",
            package_name="generic-example",
            capability_count=2,
            owner_scope=["workspace:main"],
        )
    )

    assert "aion.module.yaml" in scaffold.files
    assert "aion.module.json" in scaffold.files
    assert "contract_tests.json" in scaffold.files
    assert len(scaffold.manifest.capabilities) == 2


def test_scaffold_generator_creates_no_executable_code() -> None:
    scaffold = ModuleScaffoldGenerator().scaffold(
        ModuleScaffoldRequest(
            module_id="generic.example",
            package_name="generic-example",
            owner_scope=["workspace:main"],
        )
    )

    assert all(not name.endswith((".py", ".sh", ".js", ".ts")) for name in scaffold.files)
    assert "external endpoint" in scaffold.readme
