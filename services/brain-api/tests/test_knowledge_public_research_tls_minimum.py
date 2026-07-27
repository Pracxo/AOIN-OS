from __future__ import annotations

import ssl

from aion_brain.knowledge_intelligence.public_research_http_transport import _verified_ssl_context


def test_system_tls_context_requires_tls12_or_newer() -> None:
    context = _verified_ssl_context()
    assert context.check_hostname is True
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.minimum_version == ssl.TLSVersion.TLSv1_2
