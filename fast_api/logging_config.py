from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any


PII_PATTERNS = [
    (re.compile(r"\b\d{11}\b"), "***NIN/BVN***"),
    (re.compile(r"(\+234|234|0)[7-9]\d{9}\b"), "***MSISDN***"),
    (re.compile(r"\b\d{15}\b"), "***IMSI***"),
]

SENSITIVE_KEYS = frozenset({
    "password", "hashed_password", "token", "access_token",
    "refresh_token", "api_key", "secret", "secret_key",
    "authorization", "cookie", "x-api-key",
})


def mask_pii(text: str) -> str:
    for pattern, replacement in PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def redact_dict(data: dict[str, Any], depth: int = 0) -> dict[str, Any]:
    if depth > 5:
        return {"_truncated": True}
    result = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_KEYS:
            result[key] = "[REDACTED]"
        elif isinstance(value, str):
            result[key] = mask_pii(value)
        elif isinstance(value, dict):
            result[key] = redact_dict(value, depth + 1)
        elif isinstance(value, list):
            result[key] = [
                redact_dict(v, depth + 1) if isinstance(v, dict)
                else mask_pii(v) if isinstance(v, str)
                else v
                for v in value
            ]
        else:
            result[key] = value
    return result


class JSONFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": mask_pii(record.getMessage()),
        }

        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id

        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id

        if hasattr(record, "extra_data"):
            log_entry["data"] = redact_dict(record.extra_data)

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": mask_pii(str(record.exc_info[1])),
            }

        return json.dumps(log_entry, default=str)


class PIIMaskingFilter(logging.Filter):

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = mask_pii(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: mask_pii(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    mask_pii(str(a)) if isinstance(a, str) else a
                    for a in record.args
                )
        return True


def configure_logging(log_level: str = "INFO", json_output: bool = True) -> None:
    root_logger = logging.getLogger()

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler()

    if json_output:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )

    handler.addFilter(PIIMaskingFilter())
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
