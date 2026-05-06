"""
Label Models for Vikunja API

Covers: models.Label, LabelCreateRequest, LabelUpdateRequest, LabelListResponse
API endpoints: /labels (CRUD operations)

Labels are reusable tags that can be applied to tasks. Each label has:
- title (required): Display name shown on tasks
- hex_color: 7-character hex color code (#RRGGBB)
- description: Optional explanatory text
- created/updated: Auto-managed timestamps
- created_by: User who created the label

Usage Examples:
    # Create a new label
    label = LabelCreateRequest(
        title="bug",
        hex_color="#ff0000",
        description="Bug reports and issues"
    )
    
    # Update an existing label
    update = LabelUpdateRequest(
        title="critical-bug",  # Rename the label
        hex_color="#ff0000"     # Keep same color
    )
"""

from pydantic import Field, field_validator
from datetime import datetime
from typing import Optional
import re
from .base import VikunjaBaseModel, User


# ============================================================================
# Label Model (Full structure from API spec)
# ============================================================================

class Label(VikunjaBaseModel):
    """
    A reusable label/tag for categorizing tasks.
    
    API endpoint: /labels
    
    Labels are shared across projects and can be applied to multiple tasks.
    Each label has a unique ID, title, color, and optional description.
    
    Fields from API spec (models.Label):
        - id: Unique identifier (auto-assigned)
        - title: Display name (required, 1-250 chars)
        - hex_color: Color in #RRGGBB format (max 7 chars)
        - description: Optional explanatory text
        - created: Auto-set creation timestamp
        - updated: Auto-set update timestamp  
        - created_by: User who created the label
    
    Example from API response:
        {
            "id": 1,
            "title": "bug",
            "hex_color": "#ff0000",
            "description": "Bug reports and issues",
            "created": "2024-01-15T10:30:00Z",
            "updated": "2024-01-15T10:30:00Z",
            "created_by": {...}
        }
    """
    
    # Core Identification (2 fields)
    id: Optional[int] = Field(None, description="Unique label ID (auto-assigned by server)")
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=250,
        description="Label display name shown on tasks"
    )
    
    # Visual Properties (2 fields)
    hex_color: Optional[str] = Field(
        None,
        max_length=7,
        description="Hex color code (#RRGGBB format)"
    )
    description: Optional[str] = Field(None, description="Optional label description")
    
    # Metadata (3 fields - auto-managed by server)
    created: Optional[datetime] = Field(None, description="Creation timestamp (read-only)")
    updated: Optional[datetime] = Field(None, description="Last update timestamp (read-only)")
    created_by: Optional[User] = Field(None, description="User who created this label")
    
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
            raise ValueError(f"Invalid hex color format: {v}. Expected #RRGGBB or RRGGBB")
        return v


# ============================================================================
# Label Create Request Model
# ============================================================================

class LabelCreateRequest(VikunjaBaseModel):
    """
    Request body for creating a new label.
    
    Required fields: title (1-250 chars)
    Optional fields: hex_color, description
    
    API endpoint: POST /labels
    
    Example:
        req = LabelCreateRequest(
            title="bug",
            hex_color="#ff0000",
            description="Bug reports and issues"
        )
    
    Validation:
        - title: 1-250 characters, required
        - hex_color: Must be valid #RRGGBB format if provided
        - description: Any length if provided
    """
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=250,
        description="Label display name (required)"
    )
    hex_color: Optional[str] = Field(None, max_length=7, description="Hex color (#RRGGBB)")
    description: Optional[str] = Field(None, description="Optional label description")
    
    @field_validator('hex_color')
    @classmethod
    def validate_hex_color(cls, v):
        """Validate and normalize hex color format."""
        if v is None or v == "":
            return None
        if not v.startswith('#'):
            v = f'#{v}'
        if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError(f"Invalid hex color format: {v}. Expected #RRGGBB or RRGGBB")
        return v

    def model_dump_for_api(self) -> dict:
        """Convert to dict for API submission."""
        return self.model_dump(exclude_none=True)


# ============================================================================
# Label Update Request Model  
# ============================================================================

class LabelUpdateRequest(VikunjaBaseModel):
    """
    Request body for updating an existing label.
    
    All fields are optional - only provided fields are updated.
    
    API endpoint: POST /labels/{id} (implied)
    
    Example:
        # Rename a label, keep color
        req = LabelUpdateRequest(
            title="critical-bug"  # Only title changes
        )
        
        # Update color only
        req = LabelUpdateRequest(
            hex_color="#ff6600"  # Only color changes
        )
    """
    title: Optional[str] = Field(None, min_length=1, max_length=250, description="New label name")
    hex_color: Optional[str] = Field(None, max_length=7, description="New hex color (#RRGGBB)")
    description: Optional[str] = Field(None, description="New label description")
    
    @field_validator('hex_color')
    @classmethod
    def validate_hex_color(cls, v):
        """Validate and normalize hex color format."""
        if v is None or v == "":
            return None
        if not v.startswith('#'):
            v = f'#{v}'
        if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError(f"Invalid hex color format: {v}. Expected #RRGGBB or RRGGBB")
        return v
    
    def model_dump_for_api(self) -> dict:
        """Convert to dict, excluding None values."""
        return self.model_dump(exclude_none=True)


# ============================================================================
# Label Response Models
# ============================================================================

class LabelListResponse(VikunjaBaseModel):
    """Response for listing labels."""
    success: bool = Field(True, description="Request succeeded")
    labels: list[Label] = Field(default_factory=list, description="List of labels")
    error: Optional[str] = Field(None, description="Error message if failed")


class LabelGetResponse(VikunjaBaseModel):
    """Response for getting a single label."""
    success: bool = Field(True, description="Request succeeded")
    label: Optional[Label] = Field(None, description="The requested label")
    error: Optional[str] = Field(None, description="Error message if failed")


class LabelCreateResponse(VikunjaBaseModel):
    """Response for creating a label."""
    success: bool = Field(True, description="Request succeeded")
    label: Optional[Label] = Field(None, description="The created label")
    error: Optional[str] = Field(None, description="Error message if failed")


class LabelUpdateResponse(VikunjaBaseModel):
    """Response for updating a label."""
    success: bool = Field(True, description="Request succeeded")
    label: Optional[Label] = Field(None, description="The updated label")
    error: Optional[str] = Field(None, description="Error message if failed")
