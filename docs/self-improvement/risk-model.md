# Self-Improvement Risk Model

Task: AION-165

## Risk Levels

- `low`
- `medium`
- `high`
- `critical`

## Classification Rules

Low risk applies to isolated documentation, examples, or non-runtime fixtures with no protected paths and no behavioral change. Medium risk applies to bounded internal logic with existing coverage and no external calls. High risk applies to changes that affect runtime decision behavior, data retention, security-sensitive validation, or high-blast-radius shared modules. Critical risk applies to protected-core modification, approval policy relaxation, benchmark weakening, holdout disclosure, production deployment, autonomous merge behavior, or model-weight training.

## Mandatory Blocks

Missing rollback plans block high-risk proposals. Benchmark failure blocks approval. Safety failure blocks approval even when quality metrics improve. Protected-core changes require dual approval and cannot be processed as ordinary proposals.
