"""HTTP client for the WooCommerce REST API.

Responsibilities:
  * Authentication (HTTP Basic over HTTPS — see docs/auth.md).
  * Client-side rate limiting + retry with backoff.
  * Pagination that follows the store's X-WP-TotalPages header.
  * A stable, normalised search/read surface used by the MCP tools.
"""

from __future__ import annotations

import time
from typing import Any, Iterator

import requests
from requests.auth import HTTPBasicAuth

from .config import Config
from .errors import AuthError, NotFoundError, RateLimitedError, UpstreamError
from .rate_limiter import TokenBucket, backoff_delay

# Statuses worth retrying: explicit rate limiting + transient upstream errors.
RETRY_STATUS = {429, 500, 502, 503, 504}


class WooCommerceClient:
    def __init__(self, config: Config, session: requests.Session | None = None):
        self.cfg = config
        self.session = session or requests.Session()
        self.session.auth = HTTPBasicAuth(config.consumer_key, config.consumer_secret)
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "agent-studio-woocommerce-connector/0.1",
            }
        )
        self._bucket = TokenBucket(config.requests_per_second)

    # ---- low level -----------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self.cfg.store_url}/wp-json/{self.cfg.api_version}/{path.lstrip('/')}"

    def request(self, method: str, path: str, params: dict | None = None, **kw) -> requests.Response:
        url = self._url(path)
        attempt = 0
        while True:
            self._bucket.acquire()
            try:
                resp = self.session.request(
                    method,
                    url,
                    params=params,
                    timeout=self.cfg.timeout,
                    verify=self.cfg.verify_ssl,
                    **kw,
                )
            except requests.RequestException as exc:
                if attempt < self.cfg.max_retries:
                    time.sleep(backoff_delay(attempt))
                    attempt += 1
                    continue
                raise UpstreamError(0, f"network error: {exc}") from exc

            if resp.status_code in RETRY_STATUS:
                if attempt < self.cfg.max_retries:
                    retry_after = resp.headers.get("Retry-After")
                    delay = (
                        float(retry_after)
                        if retry_after and retry_after.isdigit()
                        else backoff_delay(attempt)
                    )
                    time.sleep(delay)
                    attempt += 1
                    continue
                if resp.status_code == 429:
                    raise RateLimitedError(
                        "Store kept rate-limiting after retries; reduce WC_RPS or retry later."
                    )

            if resp.status_code in (401, 403):
                raise AuthError(
                    f"Authentication failed ({resp.status_code}). "
                    "Check WC_CONSUMER_KEY/SECRET and the key's Read permission."
                )
            if resp.status_code == 404:
                raise NotFoundError(f"Not found: {path}")
            if resp.status_code >= 400:
                raise UpstreamError(resp.status_code, resp.text[:300])
            return resp

    def get(self, path: str, params: dict | None = None) -> requests.Response:
        return self.request("GET", path, params=params)

    # ---- pagination / search primitives --------------------------------

    def paginate(
        self,
        path: str,
        params: dict | None = None,
        *,
        max_items: int | None = None,
        per_page: int | None = None,
    ) -> Iterator[dict]:
        """Yield every item across pages, following X-WP-TotalPages.

        This is the scalable primitive: callers iterate lazily and can cap
        with `max_items` to bound context/time. For very large catalogs, the
        long-term fix is incremental sync (see docs/limitations.md), not deep
        pagination.
        """
        query = dict(params or {})
        query["per_page"] = min(per_page or self.cfg.per_page, Config.MAX_PER_PAGE)
        page = 1
        total_pages = 1
        yielded = 0
        while page <= total_pages:
            query["page"] = page
            resp = self.get(path, params=query)
            try:
                total_pages = int(resp.headers.get("X-WP-TotalPages") or 1)
            except (TypeError, ValueError):
                total_pages = 1
            batch = resp.json()
            if not isinstance(batch, list) or not batch:
                break
            for item in batch:
                yield item
                yielded += 1
                if max_items is not None and yielded >= max_items:
                    return
            page += 1

    def page(
        self,
        path: str,
        params: dict | None = None,
        *,
        page: int = 1,
        per_page: int = 50,
    ) -> tuple[list[dict], dict[str, int]]:
        """Fetch a single page plus its pagination metadata.

        Returns (items, meta) where meta = {page, per_page, total, total_pages}.
        """
        query = dict(params or {})
        query["page"] = max(1, page)
        query["per_page"] = min(max(1, per_page), Config.MAX_PER_PAGE)
        resp = self.get(path, params=query)
        items = resp.json()
        if not isinstance(items, list):
            items = [items]
        meta = {
            "page": query["page"],
            "per_page": query["per_page"],
            "total": _int_header(resp, "X-WP-Total", len(items)),
            "total_pages": _int_header(resp, "X-WP-TotalPages", 1),
        }
        return items, meta


def _int_header(resp: requests.Response, name: str, default: int) -> int:
    try:
        return int(resp.headers.get(name, default))
    except (TypeError, ValueError):
        return default
