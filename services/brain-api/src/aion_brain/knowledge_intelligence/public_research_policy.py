"""Pure policy helpers for the AION-219 public research pilot."""

from __future__ import annotations

import re
import urllib.robotparser as robotparser
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal, cast
from urllib.parse import urljoin, urlsplit, urlunsplit

from aion_brain.contracts.knowledge_public_research_pilot import (
    APPROVED_CONTENT_TYPES,
    APPROVED_ENCODINGS,
    APPROVED_LICENCE_STATUSES,
    APPROVED_METHODS,
    APPROVED_SOURCE_CLASSES,
    PUBLIC_RESEARCH_RESOURCE_LIMITS,
    PUBLIC_RESEARCH_USER_AGENT,
    PublicResearchHttpOutcome,
    PublicResearchPilotSourceCandidate,
    public_research_fingerprint,
    reject_prohibited_text,
    validate_domain_name,
    validate_public_research_url,
)
from aion_brain.knowledge_intelligence.research_policy import (
    detect_untrusted_content_instruction_markers,
)

RequestMethod = Literal["GET", "HEAD"]
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
ROBOTS_PATH = "/robots.txt"
ROBOTS_MAX_BYTES = 65_536

_CRLF_RE = re.compile(r"[\r\n]")
_SAFE_RESPONSE_HEADER_NAMES = {
    "cache-control",
    "content-language",
    "content-length",
    "content-type",
    "date",
    "etag",
    "expires",
    "last-modified",
    "link",
    "x-robots-tag",
}
_UNSAFE_RESPONSE_HEADER_NAMES = {
    "authorization",
    "proxy-authenticate",
    "set-cookie",
    "www-authenticate",
}
_REJECTED_X_ROBOTS_DIRECTIVES = {"none", "noindex", "noarchive", "nosnippet", "noai"}


class PublicResearchPolicyError(ValueError):
    """Raised when an AION-219 policy check fails closed."""

    def __init__(self, outcome: PublicResearchHttpOutcome, reason_code: str) -> None:
        super().__init__(reason_code)
        self.outcome = outcome
        self.reason_code = reason_code


@dataclass(frozen=True)
class PublicResearchResponsePolicyDecision:
    """Safe response metadata derived before retaining no source body."""

    content_type: str
    character_encoding: str | None
    safe_headers: dict[str, str]
    content_length: int | None
    x_robots_allowed: bool
    x_robots_fingerprint: str
    safe_header_fingerprint: str


@dataclass(frozen=True)
class PublicResearchRobotsDecision:
    """Per-host robots policy result for one pilot plan."""

    allowed: bool
    status_code: int
    reason_code: str
    fingerprint: str


def canonicalize_public_research_url(url: str) -> str:
    """Return the canonical HTTPS URL accepted by the public pilot."""

    validate_public_research_url(url)
    split = urlsplit(url)
    hostname = validate_domain_name(split.hostname or "", "public research URL hostname")
    if split.port is not None and (split.port < 1 or split.port > 65535):
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_DESTINATION,
            "port_outside_bounds",
        )
    port = split.port
    netloc = hostname if port in {None, 443} else f"{hostname}:{port}"
    path = split.path or "/"
    return urlunsplit(("https", netloc, path, split.query, ""))


def domain_allowlist_fingerprint(domains: tuple[str, ...]) -> str:
    """Return a deterministic fingerprint for an exact domain allowlist."""

    normalized = normalize_domain_allowlist(domains)
    return public_research_fingerprint({"explicit_domain_allowlist": normalized})


def normalize_domain_allowlist(domains: tuple[str, ...]) -> tuple[str, ...]:
    """Normalize exact domains and reject universal or wildcard allowlists."""

    if not domains:
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_DOMAIN,
            "domain_allowlist_empty",
        )
    if len(domains) > PUBLIC_RESEARCH_RESOURCE_LIMITS["maximum_domains_per_plan"]:
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_DOMAIN,
            "domain_allowlist_over_budget",
        )
    normalized = tuple(sorted(validate_domain_name(value, "domain allowlist") for value in domains))
    if len(set(normalized)) != len(normalized):
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_DOMAIN,
            "domain_allowlist_duplicate",
        )
    return normalized


def validate_method(method: str) -> RequestMethod:
    """Validate an operator-specified read-only method."""

    normalized = method.upper()
    if normalized not in APPROVED_METHODS:
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_METHOD,
            "method_not_allowed",
        )
    return cast(RequestMethod, normalized)


def validate_candidate_policy(
    candidate: PublicResearchPilotSourceCandidate,
    *,
    allowlist: tuple[str, ...],
    allowed_methods: tuple[str, ...],
    allowed_content_types: tuple[str, ...],
) -> str:
    """Validate source class, licence, allowlist, method, and URL policy."""

    canonical_url = canonicalize_public_research_url(candidate.original_url)
    if candidate.domain not in normalize_domain_allowlist(allowlist):
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_DOMAIN,
            "domain_not_allowlisted",
        )
    if candidate.method not in allowed_methods:
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_METHOD,
            "method_not_allowed",
        )
    if candidate.source_class not in APPROVED_SOURCE_CLASSES:
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_HEADERS,
            "source_class_rejected",
        )
    if candidate.licence_policy_status not in APPROVED_LICENCE_STATUSES:
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_HEADERS,
            "licence_rejected",
        )
    if set(candidate.expected_content_types) - set(allowed_content_types):
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_CONTENT_TYPE,
            "candidate_content_type_not_allowed",
        )
    return canonical_url


def validate_no_operator_headers(headers: Mapping[str, str] | None) -> None:
    """Reject every operator-supplied outbound header."""

    if headers:
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_HEADERS,
            "operator_headers_rejected",
        )


def fixed_request_headers(allowed_content_types: tuple[str, ...]) -> dict[str, str]:
    """Build fixed credential-free outbound headers."""

    for value in allowed_content_types:
        if value not in APPROVED_CONTENT_TYPES:
            raise PublicResearchPolicyError(
                PublicResearchHttpOutcome.REJECTED_CONTENT_TYPE,
                "content_type_not_allowed",
            )
    return {
        "User-Agent": PUBLIC_RESEARCH_USER_AGENT,
        "Accept": ", ".join(allowed_content_types),
        "Accept-Language": "en",
        "Accept-Encoding": "identity",
        "Connection": "close",
    }


def request_target_for_url(url: str) -> str:
    """Return the origin-form request target for a canonical HTTPS URL."""

    canonical = canonicalize_public_research_url(url)
    split = urlsplit(canonical)
    target = split.path or "/"
    if split.query:
        target = f"{target}?{split.query}"
    if _CRLF_RE.search(target):
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_HEADERS,
            "request_target_crlf_rejected",
        )
    return target


def host_header_for_url(url: str) -> str:
    """Return the fixed Host header value for a canonical HTTPS URL."""

    split = urlsplit(canonicalize_public_research_url(url))
    hostname = validate_domain_name(split.hostname or "", "Host header hostname")
    if split.port not in {None, 443}:
        return f"{hostname}:{split.port}"
    return hostname


def project_safe_response_headers(
    headers: Sequence[tuple[str, str]] | Mapping[str, str],
) -> dict[str, str]:
    """Project bounded safe response headers and reject unsafe header values."""

    items = headers.items() if isinstance(headers, Mapping) else headers
    projected: dict[str, str] = {}
    for raw_name, raw_value in sorted(items, key=lambda item: item[0].lower()):
        name = raw_name.lower().strip()
        value = raw_value.strip()
        if _CRLF_RE.search(name) or _CRLF_RE.search(value):
            raise PublicResearchPolicyError(
                PublicResearchHttpOutcome.REJECTED_HEADERS,
                "response_header_crlf_rejected",
            )
        if name in _UNSAFE_RESPONSE_HEADER_NAMES:
            continue
        if name not in _SAFE_RESPONSE_HEADER_NAMES:
            continue
        reject_prohibited_text(value, "safe response header")
        projected[name] = value[:512]
        if len(projected) > PUBLIC_RESEARCH_RESOURCE_LIMITS["maximum_safe_headers_per_snapshot"]:
            raise PublicResearchPolicyError(
                PublicResearchHttpOutcome.REJECTED_HEADERS,
                "too_many_safe_response_headers",
            )
    return projected


def response_policy_decision(
    *,
    status_code: int,
    method: RequestMethod,
    headers: Sequence[tuple[str, str]] | Mapping[str, str],
    maximum_response_bytes: int,
    allowed_content_types: tuple[str, ...],
) -> PublicResearchResponsePolicyDecision:
    """Validate response headers before body retention."""

    del method
    header_items = list(headers.items() if isinstance(headers, Mapping) else headers)
    header_map: dict[str, list[str]] = {}
    for name, value in header_items:
        header_map.setdefault(name.lower().strip(), []).append(value.strip())

    if status_code == 101:
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_HEADERS,
            "protocol_upgrade_rejected",
        )

    content_lengths = header_map.get("content-length", [])
    parsed_content_length: int | None = None
    if content_lengths:
        parsed_values = {int(value) for value in content_lengths if value.isdigit()}
        if len(parsed_values) != 1 or len(parsed_values) != len(set(content_lengths)):
            raise PublicResearchPolicyError(
                PublicResearchHttpOutcome.REJECTED_CONTENT_LENGTH,
                "conflicting_content_length",
            )
        parsed_content_length = next(iter(parsed_values))
        if parsed_content_length > maximum_response_bytes:
            raise PublicResearchPolicyError(
                PublicResearchHttpOutcome.REJECTED_CONTENT_LENGTH,
                "content_length_over_budget",
            )

    transfer_encodings = tuple(value.lower() for value in header_map.get("transfer-encoding", ()))
    if transfer_encodings and content_lengths:
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_HEADERS,
            "ambiguous_transfer_and_content_length",
        )
    if any(value not in {"chunked", "identity"} for value in transfer_encodings):
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_HEADERS,
            "transfer_encoding_rejected",
        )

    content_encodings = tuple(value.lower() for value in header_map.get("content-encoding", ()))
    if any(value != "identity" for value in content_encodings):
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_CONTENT_ENCODING,
            "compressed_response_rejected",
        )

    content_type, charset = parse_content_type_header(
        header_map.get("content-type", ["text/plain"])[0]
    )
    if content_type not in allowed_content_types:
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_CONTENT_TYPE,
            "content_type_not_allowed",
        )
    if charset is not None and charset not in APPROVED_ENCODINGS:
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_CHARACTER_ENCODING,
            "character_encoding_not_allowed",
        )

    safe_headers = project_safe_response_headers(header_items)
    x_allowed, x_fp = evaluate_x_robots_header(header_map.get("x-robots-tag", ()))
    if not x_allowed:
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_HEADERS,
            "x_robots_rejected",
        )
    return PublicResearchResponsePolicyDecision(
        content_type=content_type,
        character_encoding=charset,
        safe_headers=safe_headers,
        content_length=parsed_content_length,
        x_robots_allowed=x_allowed,
        x_robots_fingerprint=x_fp,
        safe_header_fingerprint=public_research_fingerprint(safe_headers),
    )


def parse_content_type_header(value: str) -> tuple[str, str | None]:
    """Return a validated media type and optional character encoding."""

    parts = [part.strip() for part in value.split(";") if part.strip()]
    content_type = parts[0].lower() if parts else "text/plain"
    if content_type not in APPROVED_CONTENT_TYPES:
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_CONTENT_TYPE,
            "content_type_not_allowed",
        )
    charset: str | None = None
    for item in parts[1:]:
        if item.lower().startswith("charset="):
            charset = item.split("=", 1)[1].strip().strip('"').lower()
    if charset is not None and charset not in APPROVED_ENCODINGS:
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_CHARACTER_ENCODING,
            "character_encoding_not_allowed",
        )
    return content_type, charset


def validate_response_body_size(
    body_length: int,
    *,
    maximum_response_bytes: int,
    total_transfer_bytes: int,
    maximum_total_transfer_bytes: int,
) -> None:
    """Enforce per-source and total transfer budgets."""

    if body_length > maximum_response_bytes:
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_RESPONSE_SIZE,
            "source_response_size_over_budget",
        )
    if total_transfer_bytes + body_length > maximum_total_transfer_bytes:
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_RESPONSE_SIZE,
            "total_transfer_size_over_budget",
        )


def evaluate_redirect_location(
    *,
    current_url: str,
    location: str | None,
    allowlist: tuple[str, ...],
    seen_urls: tuple[str, ...],
) -> str:
    """Validate and canonicalize one manual redirect destination."""

    if not location:
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_REDIRECT,
            "redirect_location_missing",
        )
    if _CRLF_RE.search(location):
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_REDIRECT,
            "redirect_location_crlf_rejected",
        )
    destination = canonicalize_public_research_url(urljoin(current_url, location))
    if destination in seen_urls:
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_REDIRECT,
            "redirect_loop_rejected",
        )
    hostname = urlsplit(destination).hostname or ""
    if validate_domain_name(hostname, "redirect hostname") not in normalize_domain_allowlist(
        allowlist
    ):
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_REDIRECT,
            "redirect_domain_not_allowlisted",
        )
    if len(seen_urls) >= PUBLIC_RESEARCH_RESOURCE_LIMITS["maximum_redirects_per_fetch"] + 1:
        raise PublicResearchPolicyError(
            PublicResearchHttpOutcome.REJECTED_REDIRECT,
            "redirect_limit_exceeded",
        )
    return destination


def evaluate_x_robots_header(values: Sequence[str]) -> tuple[bool, str]:
    """Evaluate X-Robots-Tag directives without storing raw headers."""

    directives: set[str] = set()
    for value in values:
        for part in value.split(","):
            directive = part.strip().lower().split(":", 1)[-1].strip()
            if directive:
                directives.add(directive)
    rejected = bool(directives & _REJECTED_X_ROBOTS_DIRECTIVES)
    return (not rejected, public_research_fingerprint({"x_robots_directives": sorted(directives)}))


def evaluate_robots_policy(
    *,
    robots_url: str,
    target_url: str,
    status_code: int,
    headers: Sequence[tuple[str, str]] | Mapping[str, str],
    body: bytes,
) -> PublicResearchRobotsDecision:
    """Evaluate one already-fetched robots.txt response."""

    safe_robots_url = canonicalize_public_research_url(robots_url)
    safe_target_url = canonicalize_public_research_url(target_url)
    decision_payload = {
        "robots_url": public_research_fingerprint({"url": safe_robots_url}),
        "target_url": public_research_fingerprint({"url": safe_target_url}),
        "status_code": status_code,
    }
    if status_code in {404, 410}:
        return _robots_decision(True, status_code, "robots_not_present", decision_payload)
    if status_code in {401, 403}:
        return _robots_decision(False, status_code, "robots_access_disallowed", decision_payload)
    if status_code >= 500:
        return _robots_decision(False, status_code, "robots_server_error_abstain", decision_payload)
    if status_code != 200:
        return _robots_decision(False, status_code, "robots_status_rejected", decision_payload)
    response_policy_decision(
        status_code=status_code,
        method="GET",
        headers=headers,
        maximum_response_bytes=ROBOTS_MAX_BYTES,
        allowed_content_types=("text/plain",),
    )
    if len(body) > ROBOTS_MAX_BYTES:
        return _robots_decision(False, status_code, "robots_oversized_abstain", decision_payload)
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return _robots_decision(False, status_code, "robots_encoding_abstain", decision_payload)
    parser = robotparser.RobotFileParser()
    parser.set_url(safe_robots_url)
    parser.parse(text.splitlines())
    allowed = parser.can_fetch(PUBLIC_RESEARCH_USER_AGENT, safe_target_url)
    return _robots_decision(
        allowed,
        status_code,
        "robots_allowed" if allowed else "robots_disallowed",
        decision_payload,
    )


def robots_url_for_source(url: str) -> str:
    """Return the robots.txt URL for a canonical source URL."""

    split = urlsplit(canonicalize_public_research_url(url))
    netloc = split.netloc
    return urlunsplit(("https", netloc, ROBOTS_PATH, "", ""))


def detect_prompt_injection_markers(body: bytes) -> tuple[str, ...]:
    """Detect instruction-like markers in untrusted source content."""

    return detect_untrusted_content_instruction_markers(body)


def _robots_decision(
    allowed: bool,
    status_code: int,
    reason_code: str,
    payload: Mapping[str, object],
) -> PublicResearchRobotsDecision:
    full_payload = dict(payload)
    full_payload.update({"allowed": allowed, "reason_code": reason_code})
    return PublicResearchRobotsDecision(
        allowed=allowed,
        status_code=status_code,
        reason_code=reason_code,
        fingerprint=public_research_fingerprint(full_payload),
    )


__all__ = [
    "PublicResearchPolicyError",
    "PublicResearchResponsePolicyDecision",
    "PublicResearchRobotsDecision",
    "REDIRECT_STATUSES",
    "ROBOTS_MAX_BYTES",
    "ROBOTS_PATH",
    "RequestMethod",
    "canonicalize_public_research_url",
    "detect_prompt_injection_markers",
    "domain_allowlist_fingerprint",
    "evaluate_redirect_location",
    "evaluate_robots_policy",
    "evaluate_x_robots_header",
    "fixed_request_headers",
    "host_header_for_url",
    "normalize_domain_allowlist",
    "parse_content_type_header",
    "project_safe_response_headers",
    "request_target_for_url",
    "response_policy_decision",
    "robots_url_for_source",
    "validate_candidate_policy",
    "validate_method",
    "validate_no_operator_headers",
    "validate_response_body_size",
]
