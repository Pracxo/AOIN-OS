# Final Evaluation Scenarios

AION-244 executes exactly 32 hard-gated scenarios in `scripts/lib/v02_release_candidate_final_evaluation.py`.

The scenario set covers AION-243 delivery, authorization lineage, committed evidence integrity, retained local candidate integrity, source and artifact lineage, checksum and signature verification, SBOM and provenance verification, smoke checks, no-publication boundaries, release asset readiness, annotated tag target readiness, GitHub prerelease transaction readiness, and final RC1 publication authorization readiness.

A scenario failure produces the exact FAIL decision and leaves the candidate unpublished.
