from __future__ import annotations

import concurrent.futures

from aion_brain.contracts.secure_runtime import InMemorySecureRuntimeAuditLedger


def test_audit_chain_appends_are_thread_safe_for_one_session() -> None:
    ledger = InMemorySecureRuntimeAuditLedger()

    def append(index: int) -> str:
        return (
            ledger.append(
                session_id="session-AION-231",
                event_type=f"event-{index}",
                reason_codes=("concurrency_smoke",),
            ).audit_hash
            or ""
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        hashes = list(executor.map(append, range(8)))

    assert len(hashes) == 8
    assert ledger.verify_chain("session-AION-231") is True
