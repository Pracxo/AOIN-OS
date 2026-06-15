"""Structured logging helpers for AION Brain."""

import json
import logging as py_logging
from collections.abc import Mapping
from typing import Any

from aion_brain.config import Settings, get_settings


def build_log_record(
    message: str,
    *,
    level: str = "INFO",
    settings: Settings | None = None,
    trace_id: str | None = None,
    correlation_id: str | None = None,
    fields: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a JSON-compatible structured log record."""
    active_settings = settings or get_settings()
    record: dict[str, Any] = {
        "service": active_settings.service_name,
        "env": active_settings.env,
        "level": level.upper(),
        "message": message,
    }

    if trace_id is not None:
        record["trace_id"] = trace_id
    if correlation_id is not None:
        record["correlation_id"] = correlation_id
    if fields:
        for key, value in fields.items():
            record.setdefault(key, value)

    return record


def configure_logging(settings: Settings | None = None) -> None:
    """Configure the root logger for AION Brain."""
    active_settings = settings or get_settings()
    level = getattr(py_logging, active_settings.log_level.upper(), py_logging.INFO)
    if not isinstance(level, int):
        level = py_logging.INFO

    root_logger = py_logging.getLogger()
    root_logger.setLevel(level)

    if not root_logger.handlers:
        handler = py_logging.StreamHandler()
        handler.setFormatter(py_logging.Formatter("%(message)s"))
        root_logger.addHandler(handler)


def log_event(
    message: str,
    *,
    level: str = "INFO",
    settings: Settings | None = None,
    trace_id: str | None = None,
    correlation_id: str | None = None,
    fields: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Emit and return a structured JSON-compatible log record."""
    active_settings = settings or get_settings()
    record = build_log_record(
        message,
        level=level,
        settings=active_settings,
        trace_id=trace_id,
        correlation_id=correlation_id,
        fields=fields,
    )
    logger = py_logging.getLogger(active_settings.service_name)
    level_number = getattr(py_logging, record["level"], py_logging.INFO)
    if not isinstance(level_number, int):
        level_number = py_logging.INFO
    logger.log(level_number, json.dumps(record, default=str))
    return record
