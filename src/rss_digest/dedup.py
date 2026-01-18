"""URL normalization and hashing utilities for deduplication."""

from __future__ import annotations

import hashlib
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_PARAMS = {"ref", "fbclid", "gclid"}
TRACKING_PREFIXES = ("utm_",)


def _is_tracking_param(key: str) -> bool:
    lowered = key.lower()
    return lowered in TRACKING_PARAMS or lowered.startswith(TRACKING_PREFIXES)


def normalize_url(url: str) -> str:
    """Normalize URLs for deduplication.

    Rules:
    - Remove fragments.
    - Remove tracking query parameters (utm_*, ref, fbclid, gclid).
    - Lowercase host.
    - Normalize trailing slash (keep '/' for root, remove for others).
    """
    parts = urlsplit(url)
    scheme = parts.scheme
    hostname = (parts.hostname or "").lower()
    netloc = hostname
    if parts.port:
        netloc = f"{hostname}:{parts.port}"

    query_params = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not _is_tracking_param(key)
    ]
    query = urlencode(query_params, doseq=True)

    path = parts.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    return urlunsplit((scheme, netloc, path, query, ""))


def canonical_url_hash(url: str) -> str:
    """Return SHA-256 hash for the normalized URL."""
    normalized = normalize_url(url)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
