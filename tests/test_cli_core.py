import asyncio
import os
import pytest
from vikunja_python.core.client import VikunjaClient
from vikunja_python.core.models.task import Task
from vikunja_python.core.models.project import Project

@pytest.mark.asyncio
async def test_cli_integration_basic(vikunja_auth):
    """Verify that the CLI-facing core client works with the testcontainer."""
    base_url = vikunja_auth["base_url"]
    token = vikunja_auth["token"]
    
    async with VikunjaClient(base_url, token) as client:
        # 1. Create a project
        proj_data = await client.request("PUT", "/projects", json={"title": "CLI Project"})
        project = Project(**proj_data)
        assert project.title == "CLI Project"
        
        # 2. Create a task via client (simulating CLI action)
        task_data = await client.request("PUT", f"/projects/{project.id}/tasks", json={"title": "CLI Task"})
        task = Task(**task_data)
        assert task.title == "CLI Task"
        assert task.project_id == project.id
        
        # 4. Update task
        update_data = await client.request("POST", f"/tasks/{task.id}", json={"done": True})
        assert update_data["done"] is True
        
        # 5. Create another task for relationship
        task2_data = await client.request("PUT", f"/projects/{project.id}/tasks", json={"title": "Task 2"})
        task2 = Task(**task2_data)
        
        # 6. Create relationship
        rel_data = await client.request("PUT", f"/tasks/{task.id}/relations", json={
            "other_task_id": task2.id,
            "relation_kind": "subtask"
        })
        assert rel_data["other_task_id"] == task2.id
        
        # 7. Delete tasks
        await client.request("DELETE", f"/tasks/{task.id}")
        await client.request("DELETE", f"/tasks/{task2.id}")
        
        # Verify deletion
        check = await client.request("GET", f"/tasks/{task.id}")
        assert check["status_code"] == 404

@pytest.mark.asyncio
async def test_error_handling_structured(vikunja_auth):
    """Verify that the client returns structured error data instead of crashing."""
    base_url = vikunja_auth["base_url"]
    token = vikunja_auth["token"]
    
    async with VikunjaClient(base_url, token) as client:
        # Request non-existent project
        data = await client.request("GET", "/projects/999999")
        assert "error" in data
        assert data["status_code"] == 404
        assert "details" in data
