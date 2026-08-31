"""Closed error taxonomy shared by every phase-5 acquisition adapter
(block D). A downloader records one of these codes per failed unit of
work -- never a bare exception name -- so a failure report is comparable
across providers and a human can tell "the provider is down" apart from
"our own schema assumption broke" without reading a traceback.
"""
from __future__ import annotations

ERROR_TYPES = frozenset({
    "HTTP_ERROR",
    "AUTH_ERROR",
    "RATE_LIMIT",
    "TIMEOUT",
    "EMPTY_RESPONSE",
    "IDENTITY_MISMATCH",
    "SCHEMA_MISMATCH",
    "PROVIDER_ERROR",
    "LICENSE_BLOCK",
    "UNKNOWN_ERROR",
})


def classify_http_error(exc, auth_error_statuses=(401, 403)) -> str:
    """Map an urllib.error.HTTPError to a taxonomy code by status."""
    status = getattr(exc, "code", None)
    if status == 429:
        return "RATE_LIMIT"
    if status in auth_error_statuses:
        return "AUTH_ERROR"
    if status is not None:
        return "HTTP_ERROR"
    return "UNKNOWN_ERROR"
