import pytest
from vikunja_python.core.models.phase6_medium import (
    Bucket, BucketCreateRequest, BucketUpdateRequest, BucketMoveRequest,
    ReactionKind, Reaction, ReactionMapEntry, ReactionCreateRequest,
    SubscriptionType, Subscription, SubscriptionCreateRequest
)
from vikunja_python.core.models.project import Project

@pytest.mark.asyncio
async def test_project_lifecycle(async_client):
    """CRUD lifecycle for Project to validate model"""
    # 1. Create
    project_data = {"title": "Hermes Test Project"}
    resp = await async_client.put("/projects", json=project_data)
    assert resp.status_code in [200, 201]
    
    new_project_json = resp.json()
    project_id = new_project_json['id']
    
    project_obj = Project(**new_project_json)
    assert project_obj.id == project_id
    
    # 2. Get
    resp = await async_client.get(f"/projects/{project_id}")
    assert resp.status_code == 200
    Project(**resp.json())

    # 3. Delete
    resp = await async_client.delete(f"/projects/{project_id}")
    assert resp.status_code in [200, 204]

@pytest.mark.asyncio
async def test_bucket_lifecycle(async_client):
    """CRUD lifecycle for Bucket"""
    # 1. Create Project for bucket
    project_data = {"title": "Project for Bucket Test"}
    resp = await async_client.put("/projects", json=project_data)
    assert resp.status_code in [200, 201]
    project_id = resp.json()['id']
    
    # Vikunja buckets need a view
    # A view is automatically created for a project. Let's get the views.
    resp = await async_client.get(f"/projects/{project_id}/views")
    assert resp.status_code == 200
    views = resp.json()
    assert len(views) > 0
    view_id = views[0]['id']
    
    # 2. Create Bucket
    bucket_payload = {"title": "Hermes Test Column"}
    resp = await async_client.put(f"/projects/{project_id}/views/{view_id}/buckets", json=bucket_payload)
    assert resp.status_code in [200, 201]
    
    new_bucket_json = resp.json()
    bucket_id = new_bucket_json['id']
    Bucket(**new_bucket_json)

    # Create a second bucket so we can delete the first one without a 412 precondition error
    await async_client.put(f"/projects/{project_id}/views/{view_id}/buckets", json={"title": "Keep Column"})
    
    # 3. Update
    update_payload = {"title": "Hermes Updated Column"}
    resp = await async_client.post(f"/projects/{project_id}/views/{view_id}/buckets/{bucket_id}", json=update_payload)
    assert resp.status_code == 200
    Bucket(**resp.json())

    # 4. Delete
    resp = await async_client.delete(f"/projects/{project_id}/views/{view_id}/buckets/{bucket_id}")
    assert resp.status_code in [200, 204]
    
@pytest.mark.asyncio
async def test_reaction_lifecycle(async_client):
    """CRUD lifecycle for Reaction"""
    # 1. Create Project and Task
    project_data = {"title": "Project for Reaction Test"}
    resp = await async_client.put("/projects", json=project_data)
    project_id = resp.json()['id']
    
    task_payload = {"title": "Task for Reaction", "project_id": project_id}
    resp = await async_client.put(f"/projects/{project_id}/tasks", json=task_payload)
    assert resp.status_code in [200, 201], f"Failed to create task: {resp.text}"
    task_id = resp.json()['id']
    
    # 2. Create Reaction
    reaction_payload = {"value": "❤️"}
    # Note: Vikunja spec says PUT /tasks/{id}/reactions
    resp = await async_client.put(f"/tasks/{task_id}/reactions", json=reaction_payload)
    
    assert resp.status_code in [200, 201], f"Reaction failed: {resp.text}"
    new_reaction_json = resp.json()
    Reaction(**new_reaction_json)
    
    # 3. Delete Reaction
    resp = await async_client.post(f"/tasks/{task_id}/reactions/delete", json={"value": "❤️"})
    assert resp.status_code in [200, 204]

@pytest.mark.asyncio
async def test_subscription_lifecycle(async_client):
    """CRUD lifecycle for Subscription"""
    # 1. Create Project and Task
    project_data = {"title": "Project for Sub Test"}
    resp = await async_client.put("/projects", json=project_data)
    project_id = resp.json()['id']
    
    task_payload = {"title": "Task for Sub Test", "project_id": project_id}
    resp = await async_client.put(f"/projects/{project_id}/tasks", json=task_payload)
    task_id = resp.json()['id']
    
    # 2. Create Subscription
    # The spec actually says PUT /subscriptions/task/{entityID}
    resp = await async_client.put(f"/subscriptions/task/{task_id}")
    
    if resp.status_code == 200:
        new_sub_json = resp.json()
        Subscription(**new_sub_json)
    else:
        # Some versions just return 204 on PUT
        assert resp.status_code in [200, 201, 204], f"Subscription failed: {resp.text}"
    
    # 3. Delete Subscription
    resp = await async_client.delete(f"/subscriptions/task/{task_id}")
    assert resp.status_code in [200, 204]
