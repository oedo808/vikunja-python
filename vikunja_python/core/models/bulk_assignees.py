"""
Bulk Assignment Models

Models for bulk task assignment operations.
Based on Vikunja API v2.3.0 specification.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    """User representation for bulk assignments."""
    
    model_config = ConfigDict(extra='ignore')
    
    id: int = Field(..., description="The unique user ID")
    username: str = Field(..., description="The username")
    name: str = Field(..., description="The full name of the user")
    email: Optional[str] = Field(None, description="The email address of the user")
    created: datetime = Field(..., description="Account creation timestamp")
    updated: datetime = Field(..., description="Last update timestamp")


class BulkAssignees(BaseModel):
    """Request to bulk assign users to tasks.
    
    Used when assigning multiple users to a single task or the same set of users
    to multiple tasks.
    """
    
    model_config = ConfigDict(extra='ignore')
    
    assignees: list[User] = Field(..., description="List of users to assign to the task(s)")


class BulkAssigneesCreateRequest(BaseModel):
    """Request to create bulk assignments for a task."""
    
    model_config = ConfigDict(extra='ignore')
    
    assignees: list[int] = Field(
        ..., 
        description="List of user IDs to assign to the task"
    )


class BulkAssigneesResponse(BaseModel):
    """Response from a bulk assignment operation."""
    
    model_config = ConfigDict(extra='ignore')
    
    assignees: list[User] = Field(..., description="List of assigned users")


class BulkTask(BaseModel):
    """Bulk task operation request.
    
    Used for updating multiple tasks with the same field values at once.
    """
    
    model_config = ConfigDict(extra='ignore')
    
    task_ids: list[int] = Field(
        ..., 
        description="List of task IDs to update"
    )
    fields: list[str] = Field(
        ..., 
        description="List of field names to update (e.g., 'title', 'priority', 'done')"
    )
    values: dict = Field(
        default_factory=dict, 
        description="Map of field names to values. Only fields in the 'fields' list will be updated."
    )


class BulkTaskResponse(BaseModel):
    """Response from a bulk task operation."""
    
    model_config = ConfigDict(extra='ignore')
    
    tasks: list[dict] = Field(
        default_factory=list, 
        description="List of updated task objects"
    )
    success_count: int = Field(
        0, 
        description="Number of tasks successfully updated"
    )
    failure_count: int = Field(
        0, 
        description="Number of tasks that failed to update"
    )
