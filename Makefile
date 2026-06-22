.PHONY: help install-brain install-sdk test test-brain test-sdk lint typecheck format check docker-build docker-up docker-down contracts kernel-self-test policy-coverage boundary-check openapi-hygiene no-domain-drift repo-health release-check

help:
	@echo "AION OS quality targets"
	@echo "  make install-brain       Install Brain API dev dependencies"
	@echo "  make install-sdk         Install SDK dev dependencies"
	@echo "  make test                Run Brain API and SDK tests"
	@echo "  make lint                Run ruff checks"
	@echo "  make typecheck           Run mypy checks"
	@echo "  make check               Run local quality gate suite"
	@echo "  make docker-build        Build the core Brain API image"
	@echo "  make docker-up           Start the core local stack"
	@echo "  make release-check       Run release candidate checks"

install-brain:
	python3 -m pip install -e "services/brain-api[dev]"

install-sdk:
	python3 -m pip install -e "packages/aion-sdk-python[dev]"

test: test-brain test-sdk

test-brain:
	scripts/test-brain.sh

test-sdk:
	scripts/test-sdk.sh

lint:
	scripts/lint.sh

typecheck:
	scripts/typecheck.sh

format:
	scripts/format.sh

check:
	scripts/check.sh

docker-build:
	scripts/docker-build.sh

docker-up:
	scripts/docker-up-core.sh

docker-down:
	scripts/docker-down.sh

contracts:
	scripts/export-contracts.sh

kernel-self-test:
	scripts/kernel-self-test.sh

policy-coverage:
	scripts/policy-coverage.sh

boundary-check:
	scripts/boundary-check.sh

openapi-hygiene:
	scripts/openapi-hygiene.sh

no-domain-drift:
	scripts/verify-no-domain-drift.sh

repo-health:
	scripts/repo-health.sh

release-check:
	scripts/release-candidate-check.sh
