"""
Task Expansion Models for Vikunja API

Covers: models.TaskComment, models.TaskAttachment, models.TaskReminder
API endpoints: Part of task CRUD with expand=[comments,attachments,reminders]

These models represent the expanded data that can be fetched alongside tasks.
Use expand query parameter to include these in task responses.

Usage Examples:
    # Fetch task with all expansions
    task = client.get_task(2, expand=["comments", "attachments", "reminders"])
    
    # Access expanded data
    for comment in task.comments:
        print(f"{comment.author.username}: {comment.comment}")
"""

from pydantic import Field, RootModel
from datetime import datetime
from typing import Optional, Dict, List, Literal
from .base import VikunjaBaseModel, User


# ============================================================================
# Task Comment Model
# ============================================================================

class TaskComment(VikunjaBaseModel):
    """
    A comment on a task.
    
    API endpoint: Part of task response with expand=comments
    
    Comments support markdown formatting and reactions. Each comment has:
        - id: Unique identifier
        - comment: The comment text (markdown)
        - author: User who wrote the comment
        - created/updated: Timestamps
        - reactions: Map of emoji reactions to users
    
    Fields from API spec (models.TaskComment):
        - id: Comment ID
        - comment: Comment text content
        - author: User object for comment author
        - created: Creation timestamp
        - updated: Last update timestamp
        - reactions: Reaction map (emoji -> list of users)
    
    Example from API response:
        {
            "id": 1,
            "comment": "This needs fixing",
            "author": {"id": 1, "username": "alice"},
            "created": "2024-01-15T10:30:00Z",
            "updated": "2024-01-15T10:30:00Z",
            "reactions": {"👍": [{"id": 2, "username": "bob"}]}
        }
    """
    
    # Core Identification (2 fields)
    id: int = Field(..., description="Unique comment ID")
    comment: str = Field(..., description="Comment text content (markdown)")
    
    # Author and Timestamps (3 fields)
    author: Optional[User] = Field(None, description="User who wrote this comment")
    created: Optional[datetime] = Field(None, description="Creation timestamp")
    updated: Optional[datetime] = Field(None, description="Last update timestamp")
    
    # Reactions (1 field)
    reactions: Optional[Dict[str, List[User]]] = Field(
        None, 
        description="Map of emoji to list of users who reacted"
    )


# ============================================================================
# Task Attachment Model  
# ============================================================================

class TaskAttachment(VikunjaBaseModel):
    """
    A file attachment on a task.
    
    API endpoint: Part of task response with expand=attachments
    
    Attachments reference files stored in the Vikunja file system. Each has:
        - id: Unique identifier
        - file: File metadata (name, size, mime type)
        - created: Upload timestamp
        - created_by: User who uploaded it
        - task_id: Parent task ID
    
    Fields from API spec (models.TaskAttachment):
        - id: Attachment ID
        - file: File object with name, size, mime
        - created: Upload timestamp
        - created_by: User who uploaded
        - task_id: Parent task ID
    
    Example from API response:
        {
            "id": 1,
            "file": {
                "id": 100,
                "name": "screenshot.png",
                "size": 245760,
                "mime": "image/png"
            },
            "created": "2024-01-15T10:30:00Z",
            "created_by": {"id": 1, "username": "alice"},
            "task_id": 5
        }
    """
    
    # Core Identification (3 fields)
    id: int = Field(..., description="Unique attachment ID")
    task_id: int = Field(..., description="Parent task ID")
    file: dict = Field(..., description="File metadata (name, size, mime)")
    
    # Metadata (2 fields)
    created: Optional[datetime] = Field(None, description="Upload timestamp")
    created_by: Optional[User] = Field(None, description="User who uploaded this attachment")


# ============================================================================
# Task Reminder Model
# ============================================================================

# ReminderRelation is a RootModel[str] for the date field reference
ReminderRelation = RootModel[str]
"""The date field a reminder is relative to.

API spec: models.ReminderRelation

Values:
    - due_date: Relative to task's due date
    - start_date: Relative to task's start date  
    - end_date: Relative to task's end date

Usage:
    from models.task_expansion import ReminderRelation
    
    # Create a reminder relative to due date
    rel = ReminderRelation("due_date")
"""

ReminderRelation.DUE_DATE = "due_date"
ReminderRelation.START_DATE = "start_date"  
ReminderRelation.END_DATE = "end_date"


class TaskReminder(VikunjaBaseModel):
    """
    A reminder for a task.
    
    API endpoint: Part of task response with expand=reminders
    
    Reminders can be absolute (specific datetime) or relative to task dates.
    
    Fields from API spec (models.TaskReminder):
        - reminder: Absolute datetime string (ISO 8601)
        - relative_to: Date field reference (due_date, start_date, end_date)
        - relative_period: Seconds offset from relative_to date
    
    Examples:
        # Absolute reminder at specific time
        {
            "reminder": "2024-01-20T09:00:00Z",
            "relative_to": null,
            "relative_period": 0
        }
        
        # Relative reminder (30 minutes before due date)
        {
            "reminder": null,
            "relative_to": "due_date",
            "relative_period": -1800  # -30 minutes in seconds
        }
    
    Notes:
        - If `reminder` is set, it's an absolute reminder (ignores relative fields)
        - If `relative_to` is set, it's a relative reminder (uses relative_period offset)
        - Negative relative_period means before the reference date
        - Positive relative_period means after the reference date
    """
    
    # Core Reminder Definition (3 fields - one mode active at a time)
    reminder: Optional[str] = Field(
        None, 
        description="Absolute datetime (ISO 8601). If set, overrides relative fields."
    )
    relative_to: Optional[ReminderRelation] = Field(
        None,
        description="Date field reference (due_date, start_date, end_date)"
    )
    relative_period: Optional[int] = Field(
        0,
        description="Seconds offset from relative_to date. Negative=before, positive=after"
    )
    
    @property
    def is_absolute(self) -> bool:
        """Check if this is an absolute reminder."""
        return self.reminder is not None
    
    @property
    def is_relative(self) -> bool:
        """Check if this is a relative reminder."""
        return self.relative_to is not None
    
    def get_description(self) -> str:
        """Human-readable description of this reminder."""
        if self.is_absolute:
            return f"Absolute reminder at {self.reminder}"
        elif self.is_relative:
            offset = self.relative_period or 0
            direction = "before" if offset <= 0 else "after"
            abs_offset = abs(offset)
            if abs_offset >= 3600:
                time_str = f"{abs_offset // 3600} hours"
            elif abs_offset >= 60:
                time_str = f"{abs_offset // 60} minutes"
            else:
                time_str = f"{abs_offset} seconds"
            return f"Relative reminder {time_str} {direction} {self.relative_to}"
        return "Reminder with no timing specified"


# ============================================================================
# Response Models for Task Expansions
# ============================================================================

class TaskCommentsResponse(VikunjaBaseModel):
    """Response containing task comments."""
    success: bool = Field(True, description="Request succeeded")
    comments: List[TaskComment] = Field(default_factory=list, description="List of comments")
    error: Optional[str] = Field(None, description="Error message if failed")


class TaskAttachmentsResponse(VikunjaBaseModel):
    """Response containing task attachments."""
    success: bool = Field(True, description="Request succeeded")
    attachments: List[TaskAttachment] = Field(default_factory=list, description="List of attachments")
    error: Optional[str] = Field(None, description="Error message if failed")


class TaskRemindersResponse(VikunjaBaseModel):
    """Response containing task reminders."""
    success: bool = Field(True, description="Request succeeded")
    reminders: List[TaskReminder] = Field(default_factory=list, description="List of reminders")
    error: Optional[str] = Field(None, description="Error message if failed")
