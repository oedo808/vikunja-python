import pytest
from vikunja_python.core.models.task import Task
from vikunja_python.core.models.label import Label, LabelCreateRequest

@pytest.mark.asyncio
async def test_task_hierarchy_and_labels_integration(async_client):
    """
    Mandatory integration test for Phase 6 enhancements:
    1. Label creation
    2. Hierarchical task creation (subtasks)
    3. Detailed listing with expansion
    """
    # 1. Create a Label
    label_payload = {"title": "IntegrationTest", "hex_color": "#ff00ff"}
    resp = await async_client.put("/labels", json=label_payload)
    assert resp.status_code in [200, 201]
    label_id = resp.json()["id"]
    
    # 2. Create a Project
    proj_resp = await async_client.put("/projects", json={"title": "Hierarchy Project"})
    assert proj_resp.status_code in [200, 201]
    project_id = proj_resp.json()["id"]
    
    # 3. Create Parent Task
    parent_resp = await async_client.put(f"/projects/{project_id}/tasks", json={"title": "Parent Task"})
    assert parent_resp.status_code in [200, 201]
    parent_id = parent_resp.json()["id"]
    
    # 4. Create Subtask using the relation endpoint
    sub_resp = await async_client.put(f"/projects/{project_id}/tasks", json={"title": "Child Task"})
    assert sub_resp.status_code in [200, 201]
    child_id = sub_resp.json()["id"]
    
    # Create the subtask relationship
    rel_payload = {"other_task_id": child_id, "relation_kind": "subtask"}
    rel_resp = await async_client.put(f"/tasks/{parent_id}/relations", json=rel_payload)
    assert rel_resp.status_code in [200, 201]
    
    # 5. Add label to Parent
    await async_client.put(f"/tasks/{parent_id}/labels", json={"label_id": label_id})
    
    # 6. Test list_tasks with expansion (The core of the enhancement)
    # GET /projects/{id}/tasks?expand=subtasks
    list_resp = await async_client.get(f"/projects/{project_id}/tasks", params={"expand": ["subtasks"]})
    assert list_resp.status_code == 200
    tasks_data = list_resp.json()

    # Use the Task model to parse the response
    tasks = [Task(**item) for item in tasks_data]
    parent_task = next((t for t in tasks if t.id == parent_id), None)

    assert parent_task is not None
    assert len(parent_task.subtasks) == 1
    assert parent_task.subtasks[0].id == child_id
    assert parent_task.subtasks[0].title == "Child Task"

    # 7. Verify Labels are present (v2.3.0 returns them by default)
    assert len(parent_task.labels) == 1
    assert parent_task.labels[0].id == label_id
    assert parent_task.labels[0].hex_color == "#ff00ff"

@pytest.mark.asyncio
async def test_pagination_integration(async_client):
    """Verify that pagination parameters are respected."""
    # Create a project and 3 tasks
    proj_resp = await async_client.put("/projects", json={"title": "Pagination Project"})
    project_id = proj_resp.json()["id"]
    
    for i in range(3):
        await async_client.put(f"/projects/{project_id}/tasks", json={"title": f"Task {i}"})
        
    # List with per_page=2
    list_resp = await async_client.get("/tasks", params={"per_page": 2, "filter": f"project_id = {project_id}"})
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 2
    
    # Check headers for pagination info (as defined in base.py/task.py)
    assert "x-pagination-total-pages" in list_resp.headers
    assert int(list_resp.headers["x-pagination-total-pages"]) >= 2
