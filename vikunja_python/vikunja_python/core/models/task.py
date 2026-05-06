"""
Task Models for Vikunja API

Covers: models.Task and related request/response types
API endpoints: /tasks, /projects/{id}/tasks, /tasks/{id}
"""

from pydantic import Field, field_validator, model_validator
from datetime import datetime
from typing import Optional, Any
from .base import VikunjaBaseModel, User, Label


# ============================================================================
# Task Entity Model (27 fields from API)
# ============================================================================

class Task(VikunjaBaseModel):
    """
    Task model representing a single task in Vikunja.
    
    API endpoint: GET /tasks, GET /tasks/{id}
    
    All 27 fields discovered from actual API response at v2.3.0:
    https://vikunja.ok9.io/api/v1/tasks
    
    Date Format: ISO 8601 with timezone (e.g., "2026-04-27T14:51:09-05:00")
    Default Dates: "0001-01-01T00:00:00Z" represents null/unset
    
    Nested Objects:
        - assignees[]: User objects
        - labels[]: Full Label objects  
        - created_by: User object
        - related_tasks: dict (relation types)
    
    Nullable Fields (return null in API):
        - attachments, reminders, reactions
    """
    
    # Core Identification (6 fields)
    id: int = Field(..., description="Unique task identifier")
    title: str = Field(..., max_length=255, description="Task title (required)")
    description: Optional[str] = Field(None, max_length=10000, description="Task description (markdown)")
    identifier: str = Field(..., description="Task identifier within project (e.g., '#1')")
    index: int = Field(0, description="Task index for ordering within view/bucket")
    project_id: int = Field(..., description="Parent project ID")
    
    # Status Fields (3 fields)
    done: bool = Field(False, description="Completion status")
    done_at: Optional[datetime] = Field(None, description="Timestamp when task was marked done")
    percent_done: int = Field(0, ge=0, le=100, description="Completion percentage (0-100)")
    
    # Priority & Importance (3 fields)
    priority: int = Field(0, ge=0, le=5, description="Task priority (0-5, higher = more important)")
    is_favorite: bool = Field(False, description="Marked as favorite/starred")
    hex_color: str = Field("", description="Custom hex color for task (without #)")
    
    # Date/Time Fields (6 fields) - All ISO 8601 with timezone
    created: datetime = Field(..., description="Creation timestamp")
    updated: datetime = Field(..., description="Last update timestamp")
    due_date: Optional[datetime] = Field(None, description="Due date/time")
    start_date: Optional[datetime] = Field(None, description="Start date/time")
    end_date: Optional[datetime] = Field(None, description="End date/time")
    
    # Note: "0001-01-01T00:00:00Z" is returned for unset dates - handle in validator
    
    # Recurrence Fields (2 fields)
    repeat_after: int = Field(0, ge=0, description="Recurrence interval in seconds")
    repeat_mode: int = Field(0, description="Recurrence mode (1=after completion, 2=after original due date)")
    
    # Positioning Fields (3 fields) - For Kanban/board views
    bucket_id: int = Field(0, description="Bucket ID in board view")
    position: int = Field(0, description="Position within bucket")
    
    # Nested Objects (4 fields)
    assignees: Optional[list[User]] = Field(default_factory=list, description="Users assigned to this task")
    labels: Optional[list[Label]] = Field(default_factory=list, description="Labels/tags on this task")
    created_by: Optional[User] = Field(None, description="User who created this task")
    related_tasks: Optional[dict[str, Any]] = Field(default_factory=dict, description="Related tasks by relation type")
    subtasks: Optional[list['Task']] = Field(default_factory=list, description="Subtasks of this task (requires expand=subtasks)")
    
    # Nullable Fields (3 fields) - May be null in API response
    attachments: Optional[list[Any]] = Field(None, description="File attachments (requires expand=attachments)")
    reminders: Optional[list[Any]] = Field(None, description="Task reminders (requires expand=reminders)")
    reactions: Optional[list[Any]] = Field(None, description="Emoji reactions (requires expand=reactions)")
    
    # Custom Fields (1 field) - UNKNOWN: Full structure not verified
    custom_fields: Optional[dict[str, Any]] = Field(None, description="Custom field values")
    
    @model_validator(mode='after')
    def populate_subtasks_from_relations(self) -> 'Task':
        """Populate subtasks field from related_tasks['subtask'] if expanded."""
        if not self.subtasks and self.related_tasks and "subtask" in self.related_tasks:
            rels = self.related_tasks["subtask"]
            if rels and isinstance(rels, list) and len(rels) > 0:
                # API might return dicts or Task objects
                # Use type(self) to avoid circular imports during definition
                cls = type(self)
                self.subtasks = [cls(**r) if isinstance(r, dict) else r for r in rels]
        return self

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def handle_default_dates(cls, v):
        """Convert '0001-01-01T00:00:00Z' to None for unset dates."""
        if v == "0001-01-01T00:00:00Z":
            return None
        return v
    
    @field_validator('due_date', 'done_at', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        """Parse ISO 8601 datetime strings."""
        if v is None or v == "":
            return None
        # Handle timezone offset format (e.g., -05:00)
        if isinstance(v, str):
            try:
                # Python 3.11+ handles timezone offsets natively
                return datetime.fromisoformat(v)
            except ValueError:
                return None
        return v


# ============================================================================
# Task Request Models (for Create/Update operations)
# ============================================================================

class TaskCreateRequest(VikunjaBaseModel):
    """
    Request body for creating a new task.
    
    Required fields: title
    Optional fields: All other task properties
    
    API endpoint: POST /tasks, POST /projects/{id}/tasks
    """
    title: str = Field(..., min_length=1, max_length=255, description="Task title (required)")
    
    # Optional fields - only send if explicitly set
    description: Optional[str] = Field(None, max_length=10000)
    priority: Optional[int] = Field(None, ge=0, le=5)
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    done: Optional[bool] = Field(None, description="Set initial completion status")
    
    # Recurrence
    repeat_after: Optional[int] = Field(None, ge=0)
    repeat_mode: Optional[int] = Field(None)
    
    # Assignments (IDs, not full objects)
    assignee_ids: Optional[list[int]] = Field(None, description="User IDs to assign")
    label_ids: Optional[list[int]] = Field(None, description="Label IDs to apply")
    
    # Positioning
    bucket_id: Optional[int] = None
    project_id: Optional[int] = None
    
    def model_dump_for_api(self) -> dict:
        """
        Convert to dict, excluding None values.
        
        Vikunja API expects only provided fields - don't send nulls.
        """
        return self.model_dump(exclude_none=True)


class TaskUpdateRequest(VikunjaBaseModel):
    """
    Request body for updating an existing task.
    
    All fields optional - only provided fields are updated.
    
    API endpoint: POST /tasks/{id} (PATCH semantics)
    """
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=10000)
    priority: Optional[int] = Field(None, ge=0, le=5)
    done: Optional[bool] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    percent_done: Optional[int] = Field(None, ge=0, le=100)
    is_favorite: Optional[bool] = None
    hex_color: Optional[str] = None
    
    # Recurrence
    repeat_after: Optional[int] = Field(None, ge=0)
    repeat_mode: Optional[int] = None
    
    # Positioning
    bucket_id: Optional[int] = None
    position: Optional[int] = None
    
    def model_dump_for_api(self) -> dict:
        """Convert to dict, excluding None values."""
        return self.model_dump(exclude_none=True)


# ============================================================================
# Task List Request/Response Models
# ============================================================================

class TaskListRequest(VikunjaBaseModel):
    """
    Query parameters for listing tasks.
    
    API endpoint: GET /tasks, GET /projects/{id}/tasks
    
    Pagination headers returned:
        x-pagination-total-pages
        x-pagination-result-count
    """
    # Filtering
    project_id: Optional[int] = Field(None, description="Filter by project ID")
    filter: Optional[str] = Field(None, description="Vikunja filter syntax (e.g., 'done = false')")
    filter_timezone: Optional[str] = Field(None, description="Timezone for date filters")
    filter_include_nulls: bool = Field(False, description="Include null-valued fields in filter")
    
    # Pagination
    page: int = Field(1, ge=1, description="Page number (1-based)")
    per_page: int = Field(50, ge=1, le=100, description="Items per page")
    
    # Sorting
    sort_by: Optional[list[str]] = Field(None, description="Fields to sort by (e.g., ['due_date', 'priority'])")
    order_by: Optional[str] = Field(None, pattern="^(asc|desc)$", description="Sort order")
    
    # Expansion (fetch nested objects)
    expand: Optional[list[str]] = Field(
        None, 
        description="Expand nested objects: subtasks, labels, buckets, reactions, comments, reminders, attachments"
    )


class TaskListResponse(VikunjaBaseModel):
    """
    Response for task list operations.
    
    Includes pagination metadata from response headers.
    """
    success: bool = Field(True, description="Request succeeded")
    tasks: list[Task] = Field(default_factory=list, description="List of tasks")
    total_count: Optional[int] = Field(None, description="Total number of tasks (across all pages)")
    page: Optional[int] = Field(None, description="Current page number")
    per_page: Optional[int] = Field(None, description="Items per page")
    total_pages: Optional[int] = Field(None, description="Total number of pages")

# Rebuild model for recursive subtasks
Task.model_rebuild()
