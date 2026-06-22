"""Create local security baseline tables."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0038_create_security_baseline"
down_revision = "0037_create_performance_baselines"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

jsonb = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "aion_threat_model_records",
        sa.Column("threat_model_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("asset_type", sa.Text(), nullable=False),
        sa.Column("threat_type", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("likelihood", sa.Text(), nullable=False),
        sa.Column("impact", sa.Text(), nullable=False),
        sa.Column("controls", jsonb, nullable=False),
        sa.Column("residual_risk", sa.Text(), nullable=False),
        sa.Column("owner_scope", jsonb, nullable=False),
        sa.Column("metadata", jsonb, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aion_threat_model_records_status", "aion_threat_model_records", ["status"])
    op.create_index("ix_aion_threat_model_records_category", "aion_threat_model_records", ["category"])
    op.create_index("ix_aion_threat_model_records_asset_type", "aion_threat_model_records", ["asset_type"])
    op.create_index("ix_aion_threat_model_records_threat_type", "aion_threat_model_records", ["threat_type"])
    op.create_index("ix_aion_threat_model_records_severity", "aion_threat_model_records", ["severity"])
    op.create_index("ix_aion_threat_model_records_likelihood", "aion_threat_model_records", ["likelihood"])
    op.create_index("ix_aion_threat_model_records_residual_risk", "aion_threat_model_records", ["residual_risk"])
    op.create_index("ix_aion_threat_model_records_created_at", "aion_threat_model_records", ["created_at"])

    op.create_table(
        "aion_attack_surface_records",
        sa.Column("attack_surface_id", sa.Text(), primary_key=True),
        sa.Column("surface_type", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("exposure_level", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.Text(), nullable=False),
        sa.Column("owner_scope", jsonb, nullable=False),
        sa.Column("controls", jsonb, nullable=False),
        sa.Column("metadata", jsonb, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_aion_attack_surface_records_surface_type", "aion_attack_surface_records", ["surface_type"])
    op.create_index("ix_aion_attack_surface_records_exposure_level", "aion_attack_surface_records", ["exposure_level"])
    op.create_index("ix_aion_attack_surface_records_risk_level", "aion_attack_surface_records", ["risk_level"])
    op.create_index("ix_aion_attack_surface_records_created_at", "aion_attack_surface_records", ["created_at"])

    op.create_table(
        "aion_security_control_records",
        sa.Column("security_control_id", sa.Text(), primary_key=True),
        sa.Column("control_key", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("evidence_refs", jsonb, nullable=False),
        sa.Column("implementation_refs", jsonb, nullable=False),
        sa.Column("metadata", jsonb, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("control_key", name="uq_aion_security_control_records_control_key"),
    )
    op.create_index("ix_aion_security_control_records_control_key", "aion_security_control_records", ["control_key"])
    op.create_index("ix_aion_security_control_records_category", "aion_security_control_records", ["category"])
    op.create_index("ix_aion_security_control_records_status", "aion_security_control_records", ["status"])
    op.create_index("ix_aion_security_control_records_required", "aion_security_control_records", ["required"])
    op.create_index("ix_aion_security_control_records_created_at", "aion_security_control_records", ["created_at"])

    op.create_table(
        "aion_secret_scan_findings",
        sa.Column("finding_id", sa.Text(), primary_key=True),
        sa.Column("scan_id", sa.Text(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=True),
        sa.Column("finding_type", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("redacted_match", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_aion_secret_scan_findings_scan_id", "aion_secret_scan_findings", ["scan_id"])
    op.create_index("ix_aion_secret_scan_findings_file_path", "aion_secret_scan_findings", ["file_path"])
    op.create_index("ix_aion_secret_scan_findings_finding_type", "aion_secret_scan_findings", ["finding_type"])
    op.create_index("ix_aion_secret_scan_findings_severity", "aion_secret_scan_findings", ["severity"])
    op.create_index("ix_aion_secret_scan_findings_status", "aion_secret_scan_findings", ["status"])
    op.create_index("ix_aion_secret_scan_findings_created_at", "aion_secret_scan_findings", ["created_at"])

    op.create_table(
        "aion_security_scan_runs",
        sa.Column("security_scan_id", sa.Text(), primary_key=True),
        sa.Column("scan_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("owner_scope", jsonb, nullable=False),
        sa.Column("checks", jsonb, nullable=False),
        sa.Column("findings", jsonb, nullable=False),
        sa.Column("failures", jsonb, nullable=False),
        sa.Column("warnings", jsonb, nullable=False),
        sa.Column("report", jsonb, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aion_security_scan_runs_scan_type", "aion_security_scan_runs", ["scan_type"])
    op.create_index("ix_aion_security_scan_runs_status", "aion_security_scan_runs", ["status"])
    op.create_index("ix_aion_security_scan_runs_created_at", "aion_security_scan_runs", ["created_at"])

    op.create_table(
        "aion_hardening_gate_runs",
        sa.Column("hardening_gate_id", sa.Text(), primary_key=True),
        sa.Column("version", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("owner_scope", jsonb, nullable=False),
        sa.Column("checks", jsonb, nullable=False),
        sa.Column("failures", jsonb, nullable=False),
        sa.Column("warnings", jsonb, nullable=False),
        sa.Column("report", jsonb, nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aion_hardening_gate_runs_version", "aion_hardening_gate_runs", ["version"])
    op.create_index("ix_aion_hardening_gate_runs_status", "aion_hardening_gate_runs", ["status"])
    op.create_index("ix_aion_hardening_gate_runs_created_at", "aion_hardening_gate_runs", ["created_at"])


def downgrade() -> None:
    op.drop_table("aion_hardening_gate_runs")
    op.drop_table("aion_security_scan_runs")
    op.drop_table("aion_secret_scan_findings")
    op.drop_table("aion_security_control_records")
    op.drop_table("aion_attack_surface_records")
    op.drop_table("aion_threat_model_records")
