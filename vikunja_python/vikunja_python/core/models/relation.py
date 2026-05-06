"""
Task Relationship Models for Vikunja API

Covers: models.TaskRelation, models.RelationKind, and related types
API endpoints: /tasks/{id}/relations (implied - relationships are part of task CRUD)

Relationship Types (12 kinds):
- subtask/parenttask: Hierarchical parent-child relationships
- blocking/blocked: Dependency relationships (A blocks B means B can't start until A done)
- precedes/follows: Sequential ordering (A precedes B means A comes before B)
- related: Generic association
- duplicateof/duplicates: Duplicate task tracking
- copiedfrom/copiedto: Source/destination of task copies

Usage Examples:
    # Create a subtask relationship (Task 2 is a subtask of Task 1)
    relation = TaskRelation(
        task_id=2,              # This task (the child/subtask)
        other_task_id=1,        # Related task (the parent)
        relation_kind="subtask" # This task IS A subtask of other_task
    )
    
    # Create a blocking relationship (Task 1 blocks Task 2)
    relation = TaskRelation(
        task_id=1,              # This task (the blocker)
        other_task_id=2,        # Blocked task (depends on this one)
        relation_kind="blocking" # This task BLOCKS the other
    )
"""

from pydantic import Field
from datetime import datetime
from typing import Optional, Literal
from .base import VikunjaBaseModel, User


# ============================================================================
# Relation Kind Enum (12 types)
# ============================================================================

RelationKind = Literal[
    "unknown",      # Default/undefined relationship
    "subtask",       # This task IS A subtask of other_task (child → parent)
    "parenttask",    # This task HAS OTHER as subtask (parent → child)
    "related",       # Generic association (bidirectional)
    "duplicateof",   # This task IS A DUPLICATE OF other_task
    "duplicates",    # This task HAS OTHER AS duplicate (reverse of duplicateof)
    "blocking",      # This task BLOCKS other_task (other can't start until this done)
    "blocked",       # This task IS BLOCKED BY other_task (depends on other)
    "precedes",      # This task COMES BEFORE other_task (sequential)
    "follows",       # This task COMES AFTER other_task (sequential)
    "copiedfrom",    # This task WAS COPIED FROM other_task (source)
    "copiedto",      # This task IS A COPY IN other_task (destination)
]

# Human-readable descriptions for each relation kind
RELATION_KIND_DESCRIPTIONS: dict[str, str] = {
    "unknown": "Undefined relationship type",
    "subtask": "This task is a subtask of the other task (child relationship)",
    "parenttask": "This task has the other task as a subtask (parent relationship)",
    "related": "Generic association between tasks",
    "duplicateof": "This task is a duplicate of the other task",
    "duplicates": "The other task is a duplicate of this task",
    "blocking": "This task blocks the other task (other depends on this)",
    "blocked": "This task is blocked by the other task (this depends on other)",
    "precedes": "This task must be completed before the other task",
    "follows": "This task comes after the other task in sequence",
    "copiedfrom": "This task was copied from the other task (original)",
    "copiedto": "This task is a copy of the other task (duplicate)",
}


# ============================================================================
# Task Relation Model
# ============================================================================

class TaskRelation(VikunjaBaseModel):
    """
    Relationship between two tasks.
    
    API endpoint: Part of task CRUD, managed via /tasks/{id}/relations
    
    Key Concept: The relationship is FROM this task TO another task.
    
    Examples:
        # Task 5 is a subtask of Task 1
        relation = TaskRelation(
            task_id=5,              # This task (the subtask)
            other_task_id=1,        # Parent task
            relation_kind="subtask" # "I am a subtask of other"
        )
        
        # Task 3 blocks Task 7 (Task 7 can't start until Task 3 done)
        relation = TaskRelation(
            task_id=3,              # This task (the blocker)
            other_task_id=7,        # Blocked task
            relation_kind="blocking" # "I block the other task"
        )
        
        # Task 2 is blocked by Task 4 (Task 2 depends on Task 4)
        relation = TaskRelation(
            task_id=2,              # This task (the one waiting)
            other_task_id=4,        # Blocking task
            relation_kind="blocked" # "I am blocked by the other task"
        )
    
    Common Patterns:
        - Subtask hierarchy: Use "subtask" from child to parent
        - Dependencies: Use "blocking" for blocker, "blocked" for dependent
        - Sequence: Use "precedes" for earlier task, "follows" for later
    
    Fields from API spec (models.TaskRelation):
        - task_id: The "base" task (this task)
        - other_task_id: The related task
        - relation_kind: Type of relationship
        - created: Auto-set timestamp
        - created_by: User who created the relation
    """
    
    # Core Identification (2 fields)
    id: Optional[int] = Field(None, description="Unique relation identifier (auto-assigned)")
    task_id: int = Field(..., description="This task's ID (the 'base' task)")
    
    # Relationship Definition (2 fields)
    other_task_id: int = Field(..., description="ID of the related task")
    relation_kind: RelationKind = Field(..., description="Type of relationship")
    
    # Metadata (2 fields - auto-managed by server)
    created: Optional[datetime] = Field(None, description="Creation timestamp (read-only)")
    created_by: Optional[User] = Field(None, description="User who created this relation")
    
    @property
    def relationship_description(self) -> str:
        """Human-readable description of this relationship."""
        kind_desc = RELATION_KIND_DESCRIPTIONS.get(self.relation_kind, "Unknown relationship")
        return f"Task {self.task_id} {kind_desc.lower()} (related task: {self.other_task_id})"


# ============================================================================
# Task Relation Request Models
# ============================================================================

class TaskRelationCreateRequest(VikunjaBaseModel):
    """
    Request body for creating a task relationship.
    
    Required fields: task_id, other_task_id, relation_kind
    
    API endpoint: POST /tasks/{id}/relations (implied)
    
    Example:
        # Make Task 5 a subtask of Task 1
        req = TaskRelationCreateRequest(
            task_id=5,
            other_task_id=1,
            relation_kind="subtask"
        )
    """
    task_id: int = Field(..., description="This task's ID (the base task)")
    other_task_id: int = Field(..., description="Related task's ID")
    relation_kind: RelationKind = Field(..., description="Type of relationship")
    
    def model_dump_for_api(self) -> dict:
        """Convert to dict for API submission."""
        return self.model_dump(exclude_none=True)


class TaskRelationUpdateRequest(VikunjaBaseModel):
    """
    Request body for updating a task relationship.
    
    Only provided fields are updated.
    
    API endpoint: POST /tasks/{id}/relations/{relation_id} (implied)
    """
    other_task_id: Optional[int] = None
    relation_kind: Optional[RelationKind] = None
    
    def model_dump_for_api(self) -> dict:
        """Convert to dict, excluding None values."""
        return self.model_dump(exclude_none=True)


# ============================================================================
# Task Relation Response Models
# ============================================================================

class TaskRelationListResponse(VikunjaBaseModel):
    """Response for listing task relationships."""
    success: bool = Field(True, description="Request succeeded")
    relations: list[TaskRelation] = Field(default_factory=list, description="List of task relations")
    error: Optional[str] = Field(None, description="Error message if failed")


class TaskRelationGetResponse(VikunjaBaseModel):
    """Response for getting a single task relationship."""
    success: bool = Field(True, description="Request succeeded")
    relation: Optional[TaskRelation] = Field(None, description="The task relation")
    error: Optional[str] = Field(None, description="Error message if failed")
