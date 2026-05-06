import httpx
import pytest
from vikunja_python.core.models.base import Token

@pytest.mark.asyncio
async def test_full_auth_lifecycle(vikunja_auth):
    """Test full authentication lifecycle using the ephemeral test container."""
    VIKUNJA_URL = vikunja_auth["base_url"]
    USERNAME = vikunja_auth["username"]
    PASSWORD = vikunja_auth["password"]
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        print("\n[1] Attempting Login...")
        login_payload = {
            "long_token": True,
            "password": PASSWORD,
            "username": USERNAME
        }
        login_resp = await client.post(f"{VIKUNJA_URL}/login", json=login_payload)
        
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        
        # Validate Token model
        token_data = login_resp.json()
        token_obj = Token(**token_data)
        assert token_obj.token is not None
        print("✅ Login successful & Token validated")

        print("\n[2] Attempting Token Refresh...")
        refresh_resp = await client.get(f"{VIKUNJA_URL}/user/token/refresh", headers={"Authorization": f"Bearer {token_obj.token}"})
        if refresh_resp.status_code == 200:
             print("✅ Token refreshed successfully via GET.")
             new_token_data = refresh_resp.json()
             assert "token" in new_token_data
        elif refresh_resp.status_code == 404:
             print("⚠️  Refresh endpoint not found or incorrect method.")

        print("\n[3] Attempting Logout...")
        logout_resp = await client.post(f"{VIKUNJA_URL}/logout", headers={"Authorization": f"Bearer {token_obj.token}"})
        assert logout_resp.status_code in [200, 204, 404]
