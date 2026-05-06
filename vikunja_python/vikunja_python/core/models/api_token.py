"""
API Token Management Models

Models for managing Vikunja API tokens, including creation, listing, and permission details.
Based on Vikunja API v2.3.0 specification.
"""

from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Permission(IntEnum):
    """Permission levels for API tokens and project sharing."""
    
    READ_ONLY = 0
    """Read-only access - can view but not modify"""
    
    READ_WRITE = 1
    """Write access - can create, update, delete own items"""
    
    ADMIN = 2
    """Admin access - full control including member management"""


class SharingType(IntEnum):
    """Types of link sharing for projects."""
    
    UNDEFINED = 0
    """Undefined sharing type"""
    
    WITHOUT_PASSWORD = 1
    """Shared without password protection"""
    
    WITH_PASSWORD = 2
    """Shared with password protection"""


class RouteDetail(BaseModel):
    """API route detail for token permissions."""
    
    model_config = ConfigDict(extra='ignore')
    
    method: str = Field(..., description="HTTP method (GET, POST, PUT, DELETE)")
    path: str = Field(..., description="API path pattern")


class APITokenRoute(BaseModel):
    """API token route definition."""
    
    model_config = ConfigDict(extra='ignore')
    
    # Note: API spec shows empty object - may be populated with route details
    # Placeholder for future expansion when /routes endpoint is fully documented
    pass


class APIToken(BaseModel):
    """API token representation.
    
    Represents an API key that can be used to authenticate requests to the Vikunja API.
    The actual token value is only visible immediately after creation.
    """
    
    model_config = ConfigDict(extra='ignore')
    
    id: int = Field(..., description="The unique, numeric id of this api key")
    title: str = Field(..., max_length=255, description="A human-readable name for this token")
    created: datetime = Field(..., description="A timestamp when this api key was created. You cannot change this value.")
    expires_at: Optional[datetime] = Field(None, description="The date when this key expires. Null means no expiration.")
    permissions: dict = Field(default_factory=dict, description="The permissions this token has. Possible values are available via the /routes endpoint and consist of HTTP method + path combinations.")
    
    # The actual token value - only visible after creation
    # This field is typically set only on create response
    token: Optional[str] = Field(None, description="The actual api key. Only visible after creation. Store this securely!")


class APITokenCreateRequest(BaseModel):
    """Request to create a new API token."""
    
    model_config = ConfigDict(extra='ignore')
    
    title: str = Field(..., max_length=255, description="A human-readable name for this token")
    expires_at: Optional[datetime] = Field(None, description="The date when this key expires. Null means no expiration.")
    permissions: Optional[Dict[str, List[str]]] = Field(None, description="Map of resource names to lists of allowed actions (e.g., {'projects': ['create', 'read_all']}). If null, grants all permissions.")


class APITokenUpdateRequest(BaseModel):
    """Request to update an API token."""
    
    model_config = ConfigDict(extra='ignore')
    
    title: Optional[str] = Field(None, max_length=255, description="A human-readable name for this token")
    expires_at: Optional[datetime] = Field(None, description="The date when this key expires. Null means no expiration.")


class APITokenListResponse(BaseModel):
    """Response containing a list of API tokens."""
    
    model_config = ConfigDict(extra='ignore')
    
    tokens: list[APIToken] = Field(default_factory=list, description="List of API tokens")


class APITokenGetResponse(BaseModel):
    """Response containing a single API token (with sensitive data)."""
    
    model_config = ConfigDict(extra='ignore')
    
    token: APIToken = Field(..., description="The API token details")


class APITokenCreateResponse(BaseModel):
    """Response from creating an API token (includes the actual token value)."""
    
    model_config = ConfigDict(extra='ignore')
    
    token: APIToken = Field(..., description="The created API token with the actual token value")
    warning: Optional[str] = Field(None, description="Warning message about storing the token securely")


class APITokenDeleteResponse(BaseModel):
    """Response from deleting an API token."""
    
    model_config = ConfigDict(extra='ignore')
    
    success: bool = Field(..., description="Whether the deletion was successful")
