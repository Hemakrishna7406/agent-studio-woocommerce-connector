"""Typed errors so the agent can reason about failures instead of crashing."""

from __future__ import annotations


class WooCommerceError(Exception):
    """Base class for all connector errors."""


class AuthError(WooCommerceError):
    """401/403 — credentials invalid, revoked, or lacking scope."""


class NotFoundError(WooCommerceError):
    """404 — the requested resource does not exist."""


class RateLimitedError(WooCommerceError):
    """429 — retries exhausted while the store kept rate-limiting us."""


class UpstreamError(WooCommerceError):
    """Any other 4xx/5xx returned by the store."""

    def __init__(self, status_code: int, message: str):
        super().__init__(f"Upstream error {status_code}: {message}")
        self.status_code = status_code
