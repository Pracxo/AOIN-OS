"""Create module developer kit certification tables."""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, MetaData, Table, Text
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()

aion_module_packages = Table(
    "aion_module_packages",
    metadata,
    Column("module_package_id", Text, primary_key=True),
    Column("module_id", Text, nullable=False),
    Column("version", Text, nullable=False),
    Column("package_name", Text, nullable=False),
    Column("display_name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("manifest", JSONB, nullable=False),
    Column("compatibility", JSONB, nullable=False),
    Column("metadata", JSONB, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_module_packages_module_id", "module_id"),
    Index("ix_aion_module_packages_version", "version"),
    Index("ix_aion_module_packages_package_name", "package_name"),
    Index("ix_aion_module_packages_status", "status"),
    Index("ix_aion_module_packages_created_at", "created_at"),
)

aion_capability_certifications = Table(
    "aion_capability_certifications",
    metadata,
    Column("certification_id", Text, primary_key=True),
    Column(
        "module_package_id",
        Text,
        ForeignKey("aion_module_packages.module_package_id"),
        nullable=False,
    ),
    Column("module_id", Text, nullable=False),
    Column("version", Text, nullable=False),
    Column("capability_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("score", Float, nullable=False),
    Column("checks", JSONB, nullable=False),
    Column("failures", JSONB, nullable=False),
    Column("warnings", JSONB, nullable=False),
    Column("certified_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_capability_certifications_module_package_id", "module_package_id"),
    Index("ix_aion_capability_certifications_module_id", "module_id"),
    Index("ix_aion_capability_certifications_version", "version"),
    Index("ix_aion_capability_certifications_capability_id", "capability_id"),
    Index("ix_aion_capability_certifications_status", "status"),
    Index("ix_aion_capability_certifications_score", "score"),
    Index("ix_aion_capability_certifications_created_at", "created_at"),
)

aion_module_certification_runs = Table(
    "aion_module_certification_runs",
    metadata,
    Column("certification_run_id", Text, primary_key=True),
    Column(
        "module_package_id",
        Text,
        ForeignKey("aion_module_packages.module_package_id"),
        nullable=False,
    ),
    Column("module_id", Text, nullable=False),
    Column("version", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("total_checks", Integer, nullable=False),
    Column("passed_checks", Integer, nullable=False),
    Column("failed_checks", Integer, nullable=False),
    Column("warning_checks", Integer, nullable=False),
    Column("score", Float, nullable=False),
    Column("report", JSONB, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_module_certification_runs_module_package_id", "module_package_id"),
    Index("ix_aion_module_certification_runs_module_id", "module_id"),
    Index("ix_aion_module_certification_runs_version", "version"),
    Index("ix_aion_module_certification_runs_status", "status"),
    Index("ix_aion_module_certification_runs_score", "score"),
    Index("ix_aion_module_certification_runs_created_at", "created_at"),
)

aion_module_contract_test_cases = Table(
    "aion_module_contract_test_cases",
    metadata,
    Column("test_case_id", Text, primary_key=True),
    Column("module_package_id", Text, nullable=True),
    Column("capability_id", Text, nullable=True),
    Column("test_type", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("input", JSONB, nullable=False),
    Column("expected", JSONB, nullable=False),
    Column("status", Text, nullable=False),
    Column("metadata", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_module_contract_test_cases_module_package_id", "module_package_id"),
    Index("ix_aion_module_contract_test_cases_capability_id", "capability_id"),
    Index("ix_aion_module_contract_test_cases_test_type", "test_type"),
    Index("ix_aion_module_contract_test_cases_status", "status"),
    Index("ix_aion_module_contract_test_cases_created_at", "created_at"),
)

