import pytest
import httpx
from vikunja_python.core.models.user import User

@pytest.mark.asyncio
async def test_container_running(vikunja_server):
    """Test that the container is reachable via HTTP."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{vikunja_server}/info")
        assert resp.status_code == 200
        data = resp.json()
        assert "version" in data

@pytest.mark.asyncio
async def test_auth_works(vikunja_auth):
    """Test that authentication provides a valid token."""
    assert vikunja_auth["token"] is not None
    assert vikunja_auth["username"] is not None

@pytest.mark.asyncio
async def test_authenticated_client(async_client):
    """Test that the authenticated client can fetch the current user."""
    resp = await async_client.get("/user")
    assert resp.status_code == 200
    user = User(**resp.json())
    assert user.id > 0
