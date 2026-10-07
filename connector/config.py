"""Runtime configuration for the WooCommerce connector.

All secrets come from the environment. Nothing is hard-coded, and nothing
secret is ever logged. See `.env.example` for the expected variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


def _env(name: str, default: str | None = None, *, required: bool = False) -> str | None:
    value = os.environ.get(name, default)
    if required and not value:
        raise ConfigError(
            f"Missing required environment variable: {name}. "
            "Copy .env.example to .env and fill it in."
        )
    return value


@dataclass(frozen=True)
class Config:
    """Immutable connector configuration."""

    store_url: str
    consumer_key: str
    consumer_secret: str
    api_version: str = "wc/v3"
    timeout: float = 20.0
    max_retries: int = 4
    per_page: int = 100
    requests_per_second: float = 5.0
    verify_ssl: bool = True

    # WooCommerce caps `per_page` at 100 per the REST API contract.
    MAX_PER_PAGE: int = 100

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            store_url=(_env("WC_STORE_URL", required=True) or "").rstrip("/"),
            consumer_key=_env("WC_CONSUMER_KEY", required=True) or "",
            consumer_secret=_env("WC_CONSUMER_SECRET", required=True) or "",
            api_version=_env("WC_API_VERSION", "wc/v3") or "wc/v3",
            timeout=float(_env("WC_TIMEOUT", "20") or "20"),
            max_retries=int(_env("WC_MAX_RETRIES", "4") or "4"),
            per_page=min(int(_env("WC_PER_PAGE", "100") or "100"), 100),
            requests_per_second=float(_env("WC_RPS", "5") or "5"),
            verify_ssl=(_env("WC_VERIFY_SSL", "true") or "true").lower() != "false",
        )

    def validate(self) -> None:
        if not self.store_url.startswith(("http://", "https://")):
            raise ConfigError("WC_STORE_URL must start with http:// or https://")
        if not self.consumer_key or not self.consumer_secret:
            raise ConfigError("WooCommerce consumer key/secret must be set.")
        if self.requests_per_second <= 0:
            raise ConfigError("WC_RPS must be positive.")
