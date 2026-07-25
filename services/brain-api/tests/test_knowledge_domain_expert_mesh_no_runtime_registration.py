from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
KI_ROOT = REPO_ROOT / "services/brain-api/src/aion_brain/knowledge_intelligence"


def test_mesh_adds_no_api_cli_or_runtime_registration():
    forbidden = [
        KI_ROOT / "domain_expert_runtime.py",
        KI_ROOT / "domain_expert_model_provider.py",
        KI_ROOT / "domain_expert_tools.py",
        REPO_ROOT / "services/brain-api/src/aion_brain/api/domain_expert_mesh.py",
    ]
    assert not any(path.exists() for path in forbidden)
