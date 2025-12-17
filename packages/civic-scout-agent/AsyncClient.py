import os
import asyncio
import logging
from typing import List, Dict, Optional, Any

import httpx

logger = logging.getLogger(__name__)


class CivicAsyncClient:
    """
    Async HTTP client for civic data sources.

    - Use `fetch_socrata_paginated` for Socrata datasets with optional SoQL queries
      and app token support.
    - Supports async context manager and explicit close().
    """

    def __init__(self, base_url: str = "https://data.cityofnewyork.us/resource/", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/") + "/"
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self._timeout)
        return self._client

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def close(self) -> None:
        if self._client:
            try:
                await self._client.aclose()
            except Exception as e:
                logger.debug("Error closing httpx client: %s", e)
            finally:
                self._client = None

    async def fetch_paged_data(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Generic single-request fetch helper (returns parsed JSON or empty list).
        """
        client = self._ensure_client()
        try:
            resp = await client.get(endpoint, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error fetching %s: %s", endpoint, e)
            return []
        except Exception as e:
            logger.error("Error fetching %s: %s", endpoint, e)
            return []

    async def fetch_socrata_paginated(
        self,
        resource: str,
        soql: Optional[str] = None,
        app_token: Optional[str] = None,
        limit: int = 1000,
        max_pages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all pages from a Socrata dataset resource with SoQL support.

        Args:
            resource: Socrata resource id (e.g. "ebds-hqr2" or "ebds-hqr2.json")
            soql: Optional SoQL query string (e.g. "SELECT * WHERE date > '2025-01-01'")
                  If provided with LIMIT/OFFSET, uses that directly; otherwise paginates.
            app_token: Optional Socrata app token to include as `X-App-Token` header.
            limit: Page size for `$limit` when paginating (default 1000).
            max_pages: Optional max number of pages to fetch (prevent runaway requests).
        Returns:
            A list of result dicts (aggregated across pages).
        """
        resource = resource.replace(".json", "")
        endpoint = f"{resource}.json"
        client = self._ensure_client()

        headers = {}
        if app_token:
            headers["X-App-Token"] = app_token

        results: List[Dict[str, Any]] = []

        # If a SoQL query is provided, prefer using $query for server-side filtering.
        if soql:
            # If the provided SoQL already contains LIMIT/OFFSET we don't paginate manually.
            soql_upper = soql.upper()
            has_limit = "LIMIT" in soql_upper
            has_offset = "OFFSET" in soql_upper

            if has_limit or has_offset:
                params = {"$query": soql}
                try:
                    resp = await client.get(endpoint, params=params, headers=headers)
                    resp.raise_for_status()
                    return resp.json()
                except Exception as e:
                    logger.error("Socrata $query request failed: %s", e)
                    return []

            # No explicit LIMIT/OFFSET in SoQL — we'll paginate by appending LIMIT/OFFSET blocks.
            offset = 0
            page_count = 0
            while True:
                paged_query = f"{soql} LIMIT {limit} OFFSET {offset}"
                params = {"$query": paged_query}
                try:
                    resp = await client.get(endpoint, params=params, headers=headers)
                    resp.raise_for_status()
                    page = resp.json()
                except Exception as e:
                    logger.error("Socrata paginated $query failed at offset %s: %s", offset, e)
                    break

                if not isinstance(page, list) or not page:
                    break

                results.extend(page)
                page_count += 1
                offset += limit

                if max_pages and page_count >= max_pages:
                    break
                if len(page) < limit:
                    break

            return results

        # No soql: use $limit/$offset style pagination
        offset = 0
        page_count = 0
        while True:
            params = {"$limit": limit, "$offset": offset}
            try:
                resp = await client.get(endpoint, params=params, headers=headers)
                resp.raise_for_status()
                page = resp.json()
            except Exception as e:
                logger.error("Socrata paginated request failed at offset %s: %s", offset, e)
                break

            if not isinstance(page, list) or not page:
                break

            results.extend(page)
            page_count += 1
            offset += limit

            if max_pages and page_count >= max_pages:
                break
            if len(page) < limit:
                break

        return results