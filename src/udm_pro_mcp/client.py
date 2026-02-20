"""Async HTTP client for the UDM Pro REST API."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .errors import APIError, AuthenticationError
from .models import UDMConfig

logger = logging.getLogger(__name__)


class UDMProClient:
    """Manages an authenticated session with a UDM Pro controller.

    Handles login, CSRF token refresh, and auto-reconnect on 401.
    """

    def __init__(self, config: UDMConfig) -> None:
        self._config = config
        self._session: aiohttp.ClientSession | None = None
        self._csrf_token: str | None = None

    # ---- lifecycle ----

    async def connect(self) -> None:
        """Create the HTTP session and authenticate."""
        jar = aiohttp.CookieJar(unsafe=True)  # needed for IP-based origins
        connector = aiohttp.TCPConnector(ssl=self._config.verify_ssl)
        self._session = aiohttp.ClientSession(
            base_url=self._config.base_url,
            cookie_jar=jar,
            connector=connector,
        )
        await self._login()

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None

    # ---- authentication ----

    async def _login(self) -> None:
        assert self._session is not None
        payload = {
            "username": self._config.username,
            "password": self._config.password,
        }
        async with self._session.post("/api/auth/login", json=payload) as resp:
            if resp.status != 200:
                raise AuthenticationError(
                    f"Login failed (HTTP {resp.status}): {await resp.text()}"
                )
            self._csrf_token = resp.headers.get("X-CSRF-Token")
            logger.info("Authenticated with UDM Pro at %s", self._config.host)

    async def _ensure_auth(self) -> None:
        """Re-login if the session has expired."""
        if self._session is None:
            await self.connect()

    # ---- internal request helpers ----

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self._csrf_token:
            headers["X-CSRF-Token"] = self._csrf_token
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        retry_auth: bool = True,
    ) -> Any:
        """Issue a request, auto-reconnecting on 401."""
        await self._ensure_auth()
        assert self._session is not None

        async with self._session.request(
            method, path, json=json, headers=self._headers()
        ) as resp:
            # Update CSRF token if present
            new_csrf = resp.headers.get("X-CSRF-Token")
            if new_csrf:
                self._csrf_token = new_csrf

            if resp.status == 401 and retry_auth:
                logger.info("Session expired, re-authenticating...")
                await self._login()
                return await self._request(
                    method, path, json=json, retry_auth=False
                )

            if resp.status >= 400:
                text = await resp.text()
                raise APIError(
                    f"API error {resp.status} on {method} {path}: {text}",
                    status=resp.status,
                )

            if resp.content_type == "application/json":
                body = await resp.json()
                # Standard UniFi envelope: {"meta": {"rc": "ok"}, "data": [...]}
                if isinstance(body, dict) and "data" in body:
                    return body["data"]
                return body

            return await resp.text()

    # ---- public convenience methods ----

    def _api(self, endpoint: str) -> str:
        """Build a site-scoped API path."""
        return f"/proxy/network/api/s/{self._config.site}/{endpoint}"

    async def get(self, endpoint: str) -> Any:
        return await self._request("GET", self._api(endpoint))

    async def post(self, endpoint: str, data: dict | None = None) -> Any:
        return await self._request("POST", self._api(endpoint), json=data)

    async def put(self, endpoint: str, data: dict | None = None) -> Any:
        return await self._request("PUT", self._api(endpoint), json=data)

    async def delete(self, endpoint: str) -> Any:
        return await self._request("DELETE", self._api(endpoint))

    async def post_cmd(self, manager: str, command: str, **kwargs: Any) -> Any:
        """Post a command to a UniFi device manager."""
        payload: dict[str, Any] = {"cmd": command}
        payload.update(kwargs)
        return await self.post(f"cmd/{manager}", payload)

    async def get_raw(self, path: str) -> Any:
        """GET a non-site-scoped path."""
        return await self._request("GET", path)
