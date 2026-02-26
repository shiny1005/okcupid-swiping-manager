"""
HTTP client for OkCupid Web API.
Uses cloudscraper to bypass Cloudflare; cookies/headers mirror the browser after reverse engineering.
Supports loading auth and API config from sample.json.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import quote

import cloudscraper
import requests

from okcupid_api.config import ENDPOINTS
from okcupid_api.exceptions import OkCupidAuthError, OkCupidAPIError


class OkCupidClient:
    """
    Single session client. Authenticate via cookies or tokens discovered from browser.
    Pass credentials via constructor or use from_sample() to load from sample.json.
    """

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        proxies: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ):
        self.base_url = (base_url or ENDPOINTS.base_url).rstrip("/")
        self.timeout = timeout
        self._session = cloudscraper.create_scraper()
        if proxies:
            self._session.proxies.update(proxies)

        # Default headers to mimic browser – refine after reverse engineering
        self._session.headers.update({
            "User-Agent": os.getenv(
                "OKCUPID_USER_AGENT",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
        })
        if headers:
            self._session.headers.update(headers)
        if cookies:
            self._session.cookies.update(cookies)
        # Optional: load cookies from env OKCUPID_COOKIE_<name>=<value>
        for key, value in os.environ.items():
            if key.startswith("OKCUPID_COOKIE_") and value:
                self._session.cookies.set(key.replace("OKCUPID_COOKIE_", "", 1), value)

    @classmethod
    def from_sample(
        cls,
        path: Optional[Path] = None,
        *,
        timeout: float = 30.0,
    ) -> "OkCupidClient":
        """
        Build client from sample.json. Path defaults to backend/sample.json.
        Uses auth.cookies, auth.token, auth.headers, api.base_url, api.user_agent, proxy.
        """
        from okcupid_api.load_sample import load_sample

        data = load_sample(path)
        auth = data.get("auth", {})
        api = data.get("api", {})
        proxy_cfg = data.get("proxy", {})

        # Prefer API host (GraphQL) so requests go to e2p-okapi.api.okcupid.com
        base_url = api.get("api_host") or api.get("base_url") or ENDPOINTS.base_url
        user_agent = api.get("user_agent") or cls._default_user_agent()

        cookie_string = (auth.get("cookie_string") or "").strip()
        cookies = auth.get("cookies")
        if cookies is None:
            cookies = {}
        cookies = {k: v for k, v in (cookies or {}).items() if v}
        if not cookie_string:
            cookies = cookies or None
        else:
            cookies = None

        headers = dict(auth.get("headers") or {})
        if user_agent:
            headers["User-Agent"] = user_agent
        token = auth.get("token")
        if token:
            headers["Authorization"] = token if token.startswith("Bearer ") else f"Bearer {token}"

        proxies = None
        if proxy_cfg:
            url = (proxy_cfg.get("url") or "").strip()
            if url:
                proxies = {"http": url, "https": url}
            elif proxy_cfg.get("host") and proxy_cfg.get("username") is not None:
                # Build URL with URL-encoded credentials (handles commas, colons, etc.)
                scheme = (proxy_cfg.get("type") or "socks5").strip().lower()
                if scheme not in ("socks5", "socks4", "http"):
                    scheme = "socks5"
                host = (proxy_cfg.get("host") or "").strip()
                port = proxy_cfg.get("port", 1080)
                user = quote(str(proxy_cfg.get("username", "")), safe="")
                pw = quote(str(proxy_cfg.get("password", "")), safe="")
                url = f"{scheme}://{user}:{pw}@{host}:{port}"
                proxies = {"http": url, "https": url}
            else:
                http_url = (proxy_cfg.get("http") or "").strip()
                https_url = (proxy_cfg.get("https") or "").strip()
                if http_url or https_url:
                    proxies = {
                        "http": http_url or https_url,
                        "https": https_url or http_url,
                    }

        client = cls(
            base_url=base_url.rstrip("/"),
            cookies=cookies,
            headers=headers or None,
            proxies=proxies,
            timeout=timeout,
        )
        if cookie_string:
            client._session.headers["Cookie"] = cookie_string
        return client

    @staticmethod
    def _default_user_agent() -> str:
        return os.getenv(
            "OKCUPID_USER_AGENT",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

    def _url(self, path: str) -> str:
        path = path.lstrip("/")
        return f"{self.base_url}/{path}"

    def graphql(
        self,
        query: str,
        *,
        path: Optional[str] = None,
        operation_name: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> requests.Response:
        """
        POST to the GraphQL endpoint (e.g. /graphql/).
        query: GraphQL query or mutation string.
        operation_name: optional operationName.
        variables: optional variables object.
        """
        from okcupid_api.config import ENDPOINTS

        path = path or ENDPOINTS.graphql
        body = {"query": query}
        if operation_name is not None:
            body["operationName"] = operation_name
        if variables is not None:
            body["variables"] = variables
        return self.post(path, json=body, **kwargs)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Send request; path can be template (e.g. /profile/{user_id})."""
        url = self._url(path)
        kwargs.setdefault("timeout", self.timeout)
        resp = self._session.request(
            method, url, params=params, json=json, data=data, **kwargs
        )
        if resp.status_code == 401:
            raise OkCupidAuthError("Unauthorized – check cookies/token")
        if resp.status_code == 429:
            raise OkCupidAPIError("Rate limited")
        return resp

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("PATCH", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("PUT", path, **kwargs)

    @property
    def session(self):
        return self._session
