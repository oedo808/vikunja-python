import pytest
import os
import json
from vikunja_python.mcp.server import list_tasks, list_project_view_tasks, get_project

@pytest.mark.asyncio
async def test_debug_descriptions(async_client, vikunja_auth):
    os.environ["VIKUNJA_URL"] = vikunja_auth["base_url"]
    os.environ["VIKUNJA_API_TOKEN"] = vikunja_auth["token"]
    
    # 1. Create a task with a description
    proj_resp = await async_client.put("/projects", json={"title": "Debug Proj"})
    p_id = proj_resp.json()["id"]
    await async_client.put(f"/projects/{p_id}/tasks", json={"title": "Task with Desc", "description": "This is a detailed description."})
    
    print("\n\n--- DEBUG: list_tasks (project) output ---")
    res = await list_tasks(project_id=p_id)
    print(res)

    print("\n\n--- DEBUG: list_tasks (global) output ---")
    res_global = await list_tasks()
    print(res_global)
    
    # 2. Check views
    print("\n--- DEBUG: get_project output ---")
    p_res = await get_project(project_id=p_id)
    print(p_res)
    
    # Extract a view ID (likely 1 if first project)
    import re
    view_match = re.search(r"ID: (\d+), Kind: list", p_res)
    if view_match:
        v_id = int(view_match.group(1))
        print(f"\n--- DEBUG: list_project_view_tasks (View {v_id}) ---")
        v_res = await list_project_view_tasks(project_id=p_id, view_id=v_id)
        print(v_res)
    else:
        print("\nNo list view found in get_project output.")
