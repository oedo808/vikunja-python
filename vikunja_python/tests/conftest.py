import pytest
import pytest_asyncio
import httpx
import asyncio
import string
import random
import time
from testcontainers.core.container import DockerContainer, LogMessageWaitStrategy
from testcontainers.core.waiting_utils import wait_for_logs

import os
os.environ["TESTCONTAINERS_RYUK_DISABLED"] = "true"

def generate_random_string(length=12):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@pytest.fixture(scope="session")
def vikunja_server():
    """Spins up an ephemeral Vikunja container for the test session."""
    with DockerContainer("vikunja/vikunja:2.3.0") \
        .with_env("VIKUNJA_SERVICE_ENABLEREGISTRATION", "true") \
        .with_env("VIKUNJA_SERVICE_PUBLICURL", "http://localhost:3456/") \
        .with_env("VIKUNJA_CORS_ENABLE", "false") \
        .with_env("VIKUNJA_FILES_BASEPATH", "/tmp/files") \
        .with_env("VIKUNJA_DATABASE_PATH", "/tmp/vikunja.db") \
        .with_exposed_ports(3456) as vikunja:
        
        # Wait for the server to be ready
        vikunja.waiting_for(LogMessageWaitStrategy("Vikunja version v2.3.0"))
        time.sleep(2) # Give it a little extra time to bind ports
        
        host = vikunja.get_container_host_ip()
        port = vikunja.get_exposed_port(3456)
        url = f"http://{host}:{port}/api/v1"
        
        yield url

@pytest_asyncio.fixture(scope="session")
async def vikunja_auth(vikunja_server):
    """Registers a user and returns authentication credentials."""
    username = generate_random_string(8)
    password = generate_random_string(32)
    email = f"{username}@example.com"
    
    async with httpx.AsyncClient(base_url=vikunja_server) as client:
        # Register user
        reg_payload = {
            "username": username,
            "password": password,
            "email": email
        }
        resp = await client.post("/register", json=reg_payload)
        resp.raise_for_status()
        
        # Login
        login_payload = {
            "username": username,
            "password": password,
            "long_token": True
        }
        login_resp = await client.post("/login", json=login_payload)
        login_resp.raise_for_status()
        
        token = login_resp.json().get("token")
        
        yield {"username": username, "password": password, "token": token, "base_url": vikunja_server}

@pytest_asyncio.fixture
async def async_client(vikunja_auth):
    """Returns an authenticated httpx AsyncClient."""
    headers = {"Authorization": f"Bearer {vikunja_auth['token']}"}
    async with httpx.AsyncClient(base_url=vikunja_auth['base_url'], headers=headers) as client:
        yield client
