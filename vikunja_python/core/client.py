import os
import sys
import logging
from typing import Optional
import httpx
from pydantic import BaseModel, ConfigDict, Field

# Set up logging for CLI/MCP
def setup_logging(is_mcp: bool = False):
    # Support VIKUNJA_DEBUG=true or 1 to enable DEBUG logs
    debug_val = os.getenv("VIKUNJA_DEBUG", "").lower()
    level = logging.DEBUG if debug_val in ("1", "true", "yes", "on") else logging.INFO
    
    if is_mcp:
        # MCP must log to stderr to avoid corrupting JSON-RPC on stdout
        logging.basicConfig(
            level=level,
            format="%(levelname)s: %(message)s",
            stream=sys.stderr,
            force=True  # Ensure we override any default handlers from libraries
        )
    else:
        logging.basicConfig(
            level=level,
            format="%(levelname)s: %(message)s",
            force=True
        )

class VikunjaClient:
    """
    Core HTTP client for Vikunja API.
    Handles both JWT and API Key authentication.
    """
    def __init__(self, base_url: str, token: str, is_api_key: bool = True):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.is_api_key = is_api_key
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=30.0
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def request(self, method: str, path: str, **kwargs):
        """Wrapper for httpx requests with error handling."""
        try:
            resp = await self.client.request(method, path, **kwargs)
            resp.raise_for_status()
            if resp.status_code == 204:
                return None
            return resp.json()
        except httpx.HTTPStatusError as e:
            # Return structured error for LLM/CLI to digest
            error_data = {"error": str(e), "status_code": e.response.status_code}
            try:
                error_data["details"] = e.response.json()
            except:
                error_data["details"] = e.response.text
            return error_data
        except Exception as e:
            return {"error": str(e), "status_code": 500}
