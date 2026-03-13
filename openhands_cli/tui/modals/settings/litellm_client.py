"""LiteLLM Proxy client for OpenHands-CLI settings."""

import logging
from typing import Any

import httpx


logger = logging.getLogger(__name__)


class LiteLLMProxyClient:
    """Client for interacting with LiteLLM Proxy."""

    def __init__(self, base_url: str, api_key: str | None = None):
        """Initialize LiteLLM Proxy client.

        Args:
            base_url: LiteLLM Proxy URL (e.g., http://localhost:4000)
            api_key: API key for authentication (optional for /v1/models)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def list_models(self) -> list[str]:
        """Fetch available models from LiteLLM Proxy.

        Returns:
            List of model names (aliases) configured in LiteLLM Proxy

        Raises:
            httpx.RequestError: If the request fails
        """
        url = f"{self.base_url}/v1/models"
        headers = {}

        # Always send API key if available for authentication
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            # Try without auth first (some proxies allow public model listing)
            pass

        try:
            response = await self._client.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            models = data.get("data", [])

            # Extract model names (aliases from model_name in config)
            model_names = [model.get("id", "") for model in models]

            # Filter out empty strings
            model_names = [name for name in model_names if name]

            logger.debug(f"Fetched {len(model_names)} models from LiteLLM Proxy")
            return sorted(model_names)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching models: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error fetching models: {e}")
            raise
        except (KeyError, ValueError) as e:
            logger.error(f"Parse error fetching models: {e}")
            raise

    async def test_connection(self) -> dict[str, Any]:
        """Test connection to LiteLLM Proxy.

        Returns:
            Dict with connection status and info

        Example:
            {
                "success": True,
                "proxy_version": "1.x.x",
                "models_count": 5
            }
        """
        url = f"{self.base_url}/health/liveliness"

        try:
            response = await self._client.get(url)
            response.raise_for_status()

            return {
                "success": True,
                "status": "connected",
                "proxy_url": self.base_url,
            }

        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}",
            }
        except httpx.RequestError as e:
            return {
                "success": False,
                "error": str(e),
            }


async def fetch_available_models(
    proxy_url: str, api_key: str | None = None
) -> list[str]:
    """Convenience function to fetch available models.

    Args:
        proxy_url: LiteLLM Proxy URL
        api_key: Optional API key

    Returns:
        List of model names
    """
    client = LiteLLMProxyClient(proxy_url, api_key)
    try:
        return await client.list_models()
    finally:
        await client.close()


async def test_proxy_connection(proxy_url: str) -> dict[str, Any]:
    """Convenience function to test proxy connection.

    Args:
        proxy_url: LiteLLM Proxy URL

    Returns:
        Connection status dict
    """
    client = LiteLLMProxyClient(proxy_url)
    try:
        return await client.test_connection()
    finally:
        await client.close()
