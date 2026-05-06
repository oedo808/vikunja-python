"""
Vikunja Pydantic Models - Base Configuration

All Vikunja API models inherit from VikunjaBaseModel for consistent configuration.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional
import re


class VikunjaBaseModel(BaseModel):
    """
    Base model with common configuration for all Vikunja API models.
    
    Configuration:
        extra='ignore': Ignore undocumented fields from API (prevents crashes on upstream changes)
        populate_by_name=True: Accept both snake_case and camelCase field names
        from_attributes=True: Support ORM mode if needed for database integration
    """
    model_config = ConfigDict(
        extra='ignore',           # Ignore undocumented API fields
        populate_by_name=True,    # Allow both naming conventions
        from_attributes=True,     # Support ORM mode
    )


# ============================================================================
# Shared Nested Models (used across multiple entities)
# ============================================================================

class User(VikunjaBaseModel):
    """
    User object as returned by the Vikunja API.

    Appears in: assignees[], created_by, owner (projects), labels.created_by
    """
    id: int = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="Email address")
    name: Optional[str] = Field(None, description="Display name (may be empty string)")
    created: datetime = Field(..., description="Account creation timestamp (ISO 8601)")
    updated: datetime = Field(..., description="Last update timestamp (ISO 8601)")

class Label(VikunjaBaseModel):
    """
    Label (tag) assigned to tasks.
    
    API endpoint: /labels
    Used in: Task.labels[]
    """
    id: int = Field(..., description="Unique label identifier")
    title: str = Field(..., description="Label text/title")
    description: Optional[str] = Field(None, description="Label description (markdown)")
    hex_color: Optional[str] = Field(None, description="Hex color code")

    @field_validator('hex_color')
    @classmethod
    def validate_hex_color(cls, v):
        """Validate and normalize hex color format (#RRGGBB)."""
        if v is None or v == "":
            return None
        # Add # if missing
        if not v.startswith('#'):
            v = f'#{v}'
        if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            return None # Or raise error, but base model should be lenient
        return v
    created_by: Optional[User] = Field(None, description="User who created this label")
    created: datetime = Field(..., description="Creation timestamp (ISO 8601)")
    updated: datetime = Field(..., description="Last update timestamp (ISO 8601)")


class TaskComment(VikunjaBaseModel):
    """
    Comment on a task.
    
    API endpoint: /tasks/{id}/comments
    
    UNKNOWN: Full structure not yet verified from API response
    TODO: Extract from actual API call with expand=comments
    """
    # UNKNOWN: Field definitions pending API verification
    id: Optional[int] = Field(None, description="Comment ID")
    text: Optional[str] = Field(None, description="Comment text (markdown)")
    # TODO: Add remaining fields after API inspection


class TaskAttachment(VikunjaBaseModel):
    """
    File attachment on a task.
    
    API endpoint: /tasks/{id}/attachments
    
    UNKNOWN: Full structure not yet verified from API response
    TODO: Extract from actual API call with expand=attachments
    """
    # UNKNOWN: Field definitions pending API verification
    id: Optional[int] = Field(None, description="Attachment ID")
    filename: Optional[str] = Field(None, description="Original filename")
    # TODO: Add remaining fields after API inspection


class TaskReminder(VikunjaBaseModel):
    """
    Reminder for a task.
    
    API endpoint: /tasks/{id}/reminders
    
    UNKNOWN: Full structure not yet verified from API response
    TODO: Extract from actual API call with expand=reminders
    """
    # UNKNOWN: Field definitions pending API verification
    id: Optional[int] = Field(None, description="Reminder ID")
    reminder_at: Optional[datetime] = Field(None, description="When reminder triggers")
    # TODO: Add remaining fields after API inspection


# ============================================================================
# Error Handling Models
# ============================================================================

class ErrorDetail(VikunjaBaseModel):
    """
    Structured error response for LLM consumption.
    
    Vikunja API returns errors in this format:
        {"code": <int>, "message": "<string>"}
    
    The 'code' field is an error code (e.g., 11 = invalid token).
    """
    code: int = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")


class Message(VikunjaBaseModel):
    """
    Generic API message wrapper.
    
    Used for simple success/error messages from the API.
    """
    code: Optional[int] = Field(None, description="Error code if applicable")
    message: str = Field(..., description="Message text")


# ============================================================================
# Authentication Models
# ============================================================================

class Token(VikunjaBaseModel):
    """
    Authentication token response.
    
    Returned by: POST /login, POST /auth/openid/{provider}/callback
    """
    # UNKNOWN: Exact fields not yet verified - placeholder based on JWT patterns
    token: Optional[str] = Field(None, description="JWT token")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")
    # TODO: Verify exact fields from /login response


# ============================================================================
# Pagination Metadata (from API headers)
# ============================================================================

class PaginationInfo(VikunjaBaseModel):
    """
    Pagination metadata from response headers.
    
    Vikunja returns pagination info in headers:
        x-pagination-total-pages: <int>
        x-pagination-result-count: <int>
    """
    total_pages: Optional[int] = Field(None, description="Total number of pages")
    result_count: Optional[int] = Field(None, description="Number of items in current response")
    # TODO: Add page/per_page if returned in body


# ============================================================================
# Generic Response Wrappers
# ============================================================================

class ListResponse(VikunjaBaseModel):
    """
    Generic wrapper for list responses with pagination.
    
    Usage: ListResponse[Task] for task lists
    """
    success: bool = Field(True, description="Request succeeded")
    items: list = Field(default_factory=list, description="List of items")
    error: Optional[ErrorDetail] = Field(None, description="Error if request failed")
    pagination: Optional[PaginationInfo] = Field(None, description="Pagination metadata")
