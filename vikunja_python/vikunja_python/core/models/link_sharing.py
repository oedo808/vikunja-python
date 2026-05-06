"""
Link Sharing Models

Models for project link sharing functionality.
Based on Vikunja API v2.3.0 specification.
"""

from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SharingType(IntEnum):
    """Types of link sharing for projects."""
    
    UNDEFINED = 0
    """Undefined sharing type"""
    
    WITHOUT_PASSWORD = 1
    """Shared without password protection"""
    
    WITH_PASSWORD = 2
    """Shared with password protection"""


class Permission(IntEnum):
    """Permission levels for project sharing."""
    
    READ_ONLY = 0
    """Read-only access - can view but not modify"""
    
    READ_WRITE = 1
    """Write access - can create, update, delete own items"""
    
    ADMIN = 2
    """Admin access - full control including member management"""


class User(BaseModel):
    """User representation for link sharing."""
    
    model_config = ConfigDict(extra='ignore')
    
    id: int = Field(..., description="The unique user ID")
    username: str = Field(..., description="The username")
    name: str = Field(..., description="The full name of the user")
    email: Optional[str] = Field(None, description="The email address of the user")


class LinkSharing(BaseModel):
    """Link sharing configuration for a project.
    
    Represents a public share link that allows access to a project without
    requiring user authentication. Can be password-protected.
    """
    
    model_config = ConfigDict(extra='ignore')
    
    id: int = Field(..., description="The ID of the shared thing")
    hash: str = Field(..., description="The public id to get this shared project")
    name: str = Field(..., description="The name of this link share. All actions someone takes while being authenticated with that link will be attributed to this name.")
    permission: Permission = Field(
        Permission.READ_ONLY, 
        description="The permission this project is shared with. 0 = Read only, 1 = Read & Write, 2 = Admin."
    )
    sharing_type: SharingType = Field(
        SharingType.UNDEFINED, 
        description="The kind of this link. 0 = undefined, 1 = without password, 2 = with password."
    )
    shared_by: Optional[User] = Field(None, description="The user who shared this project")
    created: datetime = Field(..., description="A timestamp when this project was shared. You cannot change this value.")
    updated: datetime = Field(..., description="A timestamp when this share was last updated. You cannot change this value.")
    
    # Password is write-only - can be set but not retrieved after creation
    password: Optional[str] = Field(None, description="The password of this link share. You can only set it, not retrieve it after the link share has been created.")


class LinkSharingCreateRequest(BaseModel):
    """Request to create a new link share for a project."""
    
    model_config = ConfigDict(extra='ignore')
    
    name: str = Field(..., max_length=255, description="The name of this link share")
    password: Optional[str] = Field(None, description="Optional password for the link share. If provided, sharing_type will be set to WITH_PASSWORD.")
    permission: Optional[Permission] = Field(
        Permission.READ_ONLY, 
        description="The permission level for this share. 0 = Read only, 1 = Read & Write, 2 = Admin."
    )


class LinkSharingUpdateRequest(BaseModel):
    """Request to update an existing link share."""
    
    model_config = ConfigDict(extra='ignore')
    
    name: Optional[str] = Field(None, max_length=255, description="The name of this link share")
    password: Optional[str] = Field(None, description="New password for the link share. Set to empty string to remove password protection.")
    permission: Optional[Permission] = Field(
        None, 
        description="The permission level for this share. 0 = Read only, 1 = Read & Write, 2 = Admin."
    )


class LinkSharingListResponse(BaseModel):
    """Response containing a list of link shares."""
    
    model_config = ConfigDict(extra='ignore')
    
    shares: list[LinkSharing] = Field(default_factory=list, description="List of link shares")


class LinkSharingGetResponse(BaseModel):
    """Response containing a single link share."""
    
    model_config = ConfigDict(extra='ignore')
    
    share: LinkSharing = Field(..., description="The link share details (password not included)")


class LinkSharingCreateResponse(BaseModel):
    """Response from creating a link share."""
    
    model_config = ConfigDict(extra='ignore')
    
    share: LinkSharing = Field(..., description="The created link share")
    public_url: str = Field(..., description="The public URL for accessing this shared project")


class LinkSharingDeleteResponse(BaseModel):
    """Response from deleting a link share."""
    
    model_config = ConfigDict(extra='ignore')
    
    success: bool = Field(..., description="Whether the deletion was successful")
