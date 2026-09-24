"""Base client for OpenAI-compatible API calls."""

from typing import Any, Optional

import httpx


class BaseClient:
    """Base HTTP client for OpenAI-compatible APIs."""

    def __init__(self, base_url: str, api_key: str, model: str):
        """Initialize client.

        Args:
            base_url: API base URL
            api_key: API key for authentication
            model: Default model identifier
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=120.0,
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _check_response(self, response: httpx.Response) -> None:
        """Check response and raise for status if needed.

        Args:
            response: HTTP response object

        Raises:
            httpx.HTTPStatusError: If response indicates an error
        """
        # httpx 0.28+ uses is_success instead of ok
        if hasattr(response, "is_success"):
            if not response.is_success:
                response.raise_for_status()
        elif not response.ok:  # pragma: no cover
            response.raise_for_status()

    async def post(
        self, path: str, json: Optional[dict[str, Any]] = None, **kwargs
    ) -> httpx.Response:
        """Make POST request to API."""
        url = f"{self.base_url}{path}"
        response = await self.client.post(url, json=json, **kwargs)
        self._check_response(response)
        return response

    async def get(self, path: str, **kwargs) -> httpx.Response:
        """Make GET request to API."""
        url = f"{self.base_url}{path}"
        response = await self.client.get(url, **kwargs)
        self._check_response(response)
        return response
