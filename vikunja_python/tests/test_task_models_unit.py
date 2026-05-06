import pytest
from vikunja_python.core.models.task import Task
from vikunja_python.core.models.base import Label

def test_task_model_with_subtasks():
    """Verify that the Task model can handle nested subtasks."""
    subtask_data = {
        "id": 2,
        "title": "Subtask 1",
        "identifier": "#2",
        "project_id": 1,
        "done": False,
        "created": "2026-05-05T12:00:00Z",
        "updated": "2026-05-05T12:00:00Z"
    }
    
    task_data = {
        "id": 1,
        "title": "Parent Task",
        "identifier": "#1",
        "project_id": 1,
        "done": False,
        "created": "2026-05-05T12:00:00Z",
        "updated": "2026-05-05T12:00:00Z",
        "subtasks": [subtask_data]
    }
    
    task = Task(**task_data)
    assert task.id == 1
    assert len(task.subtasks) == 1
    assert task.subtasks[0].id == 2
    assert task.subtasks[0].title == "Subtask 1"

def test_task_model_with_labels():
    """Verify that the Task model handles expanded labels."""
    label_data = {
        "id": 10,
        "title": "Urgent",
        "hex_color": "ff0000",
        "created": "2026-05-05T12:00:00Z",
        "updated": "2026-05-05T12:00:00Z"
    }
    
    task_data = {
        "id": 1,
        "title": "Task with labels",
        "identifier": "#1",
        "project_id": 1,
        "done": False,
        "created": "2026-05-05T12:00:00Z",
        "updated": "2026-05-05T12:00:00Z",
        "labels": [label_data]
    }
    
    task = Task(**task_data)
    assert len(task.labels) == 1
    assert task.labels[0].title == "Urgent"
    assert task.labels[0].hex_color == "#ff0000"

def test_label_model_validation():
    """Test label model validation (hex color format)."""
    # Both models now normalize to include # prefix
    
    from vikunja_python.core.models.base import Label as BaseLabel
    l1 = BaseLabel(id=1, title="test", hex_color="ff0000", created="2026-05-05T12:00:00Z", updated="2026-05-05T12:00:00Z")
    assert l1.hex_color == "#ff0000"
    
    from vikunja_python.core.models.label import Label as FullLabel
    l2 = FullLabel(id=1, title="test", hex_color="#ff0000")
    assert l2.hex_color == "#ff0000"
    
    with pytest.raises(ValueError):
        FullLabel(id=1, title="test", hex_color="invalid")
