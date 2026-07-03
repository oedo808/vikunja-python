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
        # Respect SSL_CERT_FILE explicitly — more reliable than relying on
        # certifi's env-var propagation which can be lost in subprocess spawns.
        verify = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE") or True
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=30.0,
            verify=verify,
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

    async def get_dashboard_summary(self) -> dict:
        """Quick polling summary for ePaper dashboard. Queries saved filters in parallel."""
        filters = {
            "overdue": -3,
            "due_today": -4,
            "due_soon": -2,
        }
        import asyncio
        async def fetch(label: str, filter_id: int) -> dict:
            data = await self.request("GET", "/tasks", params={
                "page": 1, "per_page": 10, "project_id": filter_id
            })
            if isinstance(data, dict) and "error" in data:
                return {"label": label, "count": 0, "tasks": [], "error": data["error"]}
            tasks = data if isinstance(data, list) else []
            return {
                "label": label,
                "count": len(tasks),
                "tasks": [
                    {"id": t.get("id"), "title": t.get("title"),
                     "due_date": t.get("due_date"), "priority": t.get("priority", 0)}
                    for t in tasks[:10]
                ]
            }
        results = await asyncio.gather(*[
            fetch(label, fid) for label, fid in filters.items()
        ])
        total = sum(r["count"] for r in results)
        return {"total": total, "filters": {r["label"]: r for r in results}}
