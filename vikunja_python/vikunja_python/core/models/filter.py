"""
Filter Models for Vikunja API

Covers: models.SavedFilter and related types
API endpoints: /filters, /filters/{id}

Note: GET /filters returns 405 (Method Not Allowed) - use PUT to create filters.
      Filters are typically managed through the UI or project views.
"""

from pydantic import Field
from datetime import datetime
from typing import Optional, Any
from .base import VikunjaBaseModel, User


# ============================================================================
# Task Collection (filter definition)
# ============================================================================

class TaskCollection(VikunjaBaseModel):
    """
    Filter query definition for matching tasks.
    
    Used in: SavedFilter.filters
    
    Documentation: https://vikunja.io/docs/filters
    
    Example filter syntax: "done = false && priority >= 3"
    """
    filter: Optional[str] = Field(None, description="Filter expression (e.g., 'done = false && priority >= 3')")
    filter_include_nulls: bool = Field(False, description="Include null values in results")
    order_by: Optional[list[str]] = Field(None, description="Order direction: ['asc'] or ['desc']")
    s: Optional[str] = Field(None, description="Search term")
    sort_by: Optional[list[str]] = Field(None, description="Fields to sort by (e.g., ['due_date', 'priority'])")


# ============================================================================
# Saved Filter Entity Model
# ============================================================================

class SavedFilter(VikunjaBaseModel):
    """
    Saved filter model representing a user-created filter preset.
    
    API endpoint: PUT /filters (create), GET /filters/{id}, POST /filters/{id}, DELETE /filters/{id}
    
    Fields from API spec (models.SavedFilter):
        - id: Unique numeric ID
        - title: Filter name (1-250 chars, required)
        - description: Optional description
        - filters: TaskCollection defining the filter logic
        - is_favorite: Whether filter is favorited
        - owner: User who owns this filter
        - created: Creation timestamp (auto-set, read-only)
        - updated: Last update timestamp (auto-set, read-only)
    """
    
    # Core Identification (2 fields)
    id: Optional[int] = Field(None, description="Unique filter identifier (auto-assigned on create)")
    title: str = Field(..., min_length=1, max_length=250, description="Filter name/title")
    
    # Filter Definition (2 fields)
    description: Optional[str] = Field(None, description="Filter description")
    filters: Optional[TaskCollection] = Field(None, description="Filter logic definition")
    
    # Status & Ownership (2 fields)
    is_favorite: bool = Field(False, description="Marked as favorite")
    owner: Optional[User] = Field(None, description="Filter owner")
    
    # Timestamps (auto-managed by server) - 2 fields
    created: Optional[datetime] = Field(None, description="Creation timestamp (read-only)")
    updated: Optional[datetime] = Field(None, description="Last update timestamp (read-only)")


# ============================================================================
# Filter Request Models
# ============================================================================

class SavedFilterCreateRequest(VikunjaBaseModel):
    """
    Request body for creating a new saved filter.
    
    Required fields: title, filters
    Optional fields: description, is_favorite
    
    API endpoint: PUT /filters
    """
    title: str = Field(..., min_length=1, max_length=250, description="Filter name (required)")
    filters: TaskCollection = Field(..., description="Filter logic definition")
    
    # Optional fields
    description: Optional[str] = Field(None, description="Filter description")
    is_favorite: bool = Field(False, description="Mark as favorite")
    
    def model_dump_for_api(self) -> dict:
        """Convert to dict, excluding None values."""
        return self.model_dump(exclude_none=True)


class SavedFilterUpdateRequest(VikunjaBaseModel):
    """
    Request body for updating a saved filter.
    
    All fields optional - only provided fields are updated.
    
    API endpoint: POST /filters/{id}
    """
    title: Optional[str] = Field(None, min_length=1, max_length=250)
    description: Optional[str] = None
    filters: Optional[TaskCollection] = None
    is_favorite: Optional[bool] = None
    
    def model_dump_for_api(self) -> dict:
        """Convert to dict, excluding None values."""
        return self.model_dump(exclude_none=True)


# ============================================================================
# Filter List/Get Response Models
# ============================================================================

class SavedFilterListResponse(VikunjaBaseModel):
    """Response for filter list operations."""
    success: bool = Field(True, description="Request succeeded")
    filters: list[SavedFilter] = Field(default_factory=list, description="List of saved filters")
    error: Optional[Any] = Field(None, description="Error if request failed")


class SavedFilterGetResponse(VikunjaBaseModel):
    """Response for getting a single filter."""
    success: bool = Field(True, description="Request succeeded")
    filter: Optional[SavedFilter] = Field(None, description="The saved filter")
    error: Optional[Any] = Field(None, description="Error if request failed")
