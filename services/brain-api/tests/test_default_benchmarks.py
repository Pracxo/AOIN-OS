"""Default benchmark definition tests."""

from aion_brain.performance.defaults import list_default_benchmarks
from tests.performance_fakes import SCOPE


def test_default_benchmarks_contain_no_domain_terms() -> None:
    text = " ".join(
        [benchmark.model_dump_json() for benchmark in list_default_benchmarks(SCOPE)]
    ).lower()

    for term in {"finance", "trading", "legal", "healthcare", "medical", "payments"}:
        assert term not in text


def test_default_benchmarks_include_full_local_suite() -> None:
    benchmark_types = {benchmark.benchmark_type for benchmark in list_default_benchmarks(SCOPE)}

    assert {"smoke", "full_local", "memory", "retrieval", "reasoning", "visual"} <= benchmark_types
