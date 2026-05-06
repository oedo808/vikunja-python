"""
Webhook Models for Vikunja API

Covers: models.Webhook - Webhook target management

Webhook Workflow:
1. Create webhook target with POST /projects/{id}/webhooks or POST /user/webhooks
2. Configure target URL, events, and optional auth (Basic Auth, HMAC secret)
3. Vikunja sends POST requests to target URL when configured events occur
4. Manage webhooks via GET/POST/DELETE endpoints

Supported Events:
- task.created
- task.updated
- task.deleted
- task.completed
- task.uncompleted
- comment.created
- comment.updated
- comment.deleted

Usage Examples:
    # Create project webhook for task events
    webhook = WebhookCreateRequest(
        target_url="https://example.com/vikunja-webhook",
        events=["task.created", "task.updated"],
        secret="hmac_secret_key"  # For request signing
    )
    
    # User-level webhook (mutually exclusive with project_id)
    user_webhook = WebhookCreateRequest(
        target_url="https://example.com/user-notifications",
        events=["task.completed"],
        user_id=1
    )
"""

from pydantic import Field, field_validator
from datetime import datetime
from typing import Optional, List
from .base import VikunjaBaseModel
from .user import User


# ============================================================================
# Webhook Event Types (Literal)
# ============================================================================

WebhookEvent = str
"""Webhook event type.

API spec: models.Webhook.events (array of strings)

Common Events:
    "task.created" - Task created
    "task.updated" - Task updated
    "task.deleted" - Task deleted
    "task.completed" - Task marked as done
    "task.uncompleted" - Task unmarked from done
    "comment.created" - Comment added to task
    "comment.updated" - Comment edited
    "comment.deleted" - Comment removed

Usage:
    from models.webhook import WebhookEvent
    
    webhook = WebhookCreateRequest(
        target_url="https://example.com/hook",
        events=["task.created", "task.completed"]
    )
"""

# Named constants for clarity
TaskCreated = "task.created"
TaskUpdated = "task.updated"
TaskDeleted = "task.deleted"
TaskCompleted = "task.completed"
TaskUncompleted = "task.uncompleted"
CommentCreated = "comment.created"
CommentUpdated = "comment.updated"
CommentDeleted = "comment.deleted"


# ============================================================================
# Webhook Models
# ============================================================================

class Webhook(VikunjaBaseModel):
    """
    Webhook target configuration.
    
    API endpoint: GET /projects/{id}/webhooks, GET /user/webhooks
    
    Represents a configured webhook that Vikunja will call when events occur.
    
    Fields from API spec (models.Webhook):
        - id: Unique webhook identifier
        - target_url: URL where POST requests are sent
        - project_id: Project this webhook belongs to (mutually exclusive with user_id)
        - user_id: User this webhook belongs to (mutually exclusive with project_id)
        - events: List of events that trigger this webhook
        - basic_auth_user: Optional Basic Auth username
        - basic_auth_password: Optional Basic Auth password
        - secret: HMAC signing secret for request verification
        - created_by: User who created the webhook
        - created/updated: Timestamps
    
    Example from API response:
        {
            "id": 1,
            "target_url": "https://example.com/vikunja-webhook",
            "project_id": 5,
            "user_id": null,
            "events": ["task.created", "task.updated"],
            "basic_auth_user": "webhook_user",
            "basic_auth_password": "secret_pass",
            "secret": "hmac_secret_key",
            "created_by": {"id": 1, "username": "alice"},
            "created": "2024-01-15T10:30:00Z",
            "updated": "2024-01-15T10:30:00Z"
        }
    
    Usage:
        # Get project webhooks
        webhooks = WebhookListResponse.model_validate(api_response)
        
        for webhook in webhooks.webhooks:
            print(f"Webhook {webhook.id}: {webhook.target_url}")
            print(f"  Events: {', '.join(webhook.events)}")
    """
    
    # Core Identification (2 fields)
    id: Optional[int] = Field(None, description="Unique webhook ID")
    target_url: str = Field(..., description="Target URL for POST requests")
    
    # Scope (1 field - mutually exclusive with user_id)
    project_id: Optional[int] = Field(
        None, 
        description="Project ID (mutually exclusive with user_id)"
    )
    user_id: Optional[int] = Field(
        None, 
        description="User ID (mutually exclusive with project_id)"
    )
    
    # Configuration (3 fields)
    events: Optional[List[WebhookEvent]] = Field(
        None, 
        description="Events that trigger this webhook"
    )
    basic_auth_user: Optional[str] = Field(
        None, 
        description="Basic Auth username for webhook requests"
    )
    basic_auth_password: Optional[str] = Field(
        None, 
        description="Basic Auth password for webhook requests"
    )
    secret: Optional[str] = Field(
        None, 
        description="HMAC signing secret for request verification"
    )
    
    # Metadata (3 fields)
    created_by: Optional[User] = Field(None, description="User who created this webhook")
    created: Optional[datetime] = Field(None, description="Webhook creation timestamp")
    updated: Optional[datetime] = Field(None, description="Last update timestamp")


class WebhookCreateRequest(VikunjaBaseModel):
    """
    Request body for creating a webhook.
    
    API endpoint: POST /projects/{id}/webhooks or POST /user/webhooks
    
    Required fields: target_url
    Optional fields: events, basic_auth_user, basic_auth_password, secret
    
    Note: Either project_id or user_id must be set (handled by API route)
    
    Example:
        req = WebhookCreateRequest(
            target_url="https://example.com/vikunja-webhook",
            events=["task.created", "task.updated"],
            secret="hmac_secret_key"
        )
    """
    
    # Required (1 field)
    target_url: str = Field(..., description="Target URL for POST requests")
    
    # Optional Configuration (4 fields)
    events: Optional[List[WebhookEvent]] = Field(
        None, 
        description="Events that trigger this webhook"
    )
    basic_auth_user: Optional[str] = Field(
        None, 
        description="Basic Auth username for webhook requests"
    )
    basic_auth_password: Optional[str] = Field(
        None, 
        description="Basic Auth password for webhook requests"
    )
    secret: Optional[str] = Field(
        None, 
        description="HMAC signing secret for request verification"
    )
    
    def model_dump_for_api(self) -> dict:
        """Convert to dict for API submission."""
        return self.model_dump(exclude_none=True)


class WebhookUpdateRequest(VikunjaBaseModel):
    """
    Request body for updating a webhook.
    
    API endpoint: POST /projects/{id}/webhooks/{webhook_id}
    
    All fields are optional - only provided fields are updated.
    
    Example:
        req = WebhookUpdateRequest(
            events=["task.created", "task.updated", "task.deleted"],
            secret="new_secret_key"
        )
    """
    
    # Optional Configuration (5 fields)
    target_url: Optional[str] = Field(None, description="New target URL")
    events: Optional[List[WebhookEvent]] = Field(None, description="New event list")
    basic_auth_user: Optional[str] = Field(None, description="New Basic Auth username")
    basic_auth_password: Optional[str] = Field(None, description="New Basic Auth password")
    secret: Optional[str] = Field(None, description="New HMAC signing secret")
    
    def model_dump_for_api(self) -> dict:
        """Convert to dict, excluding None values."""
        return self.model_dump(exclude_none=True)


# ============================================================================
# Response Models
# ============================================================================

class WebhookListResponse(VikunjaBaseModel):
    """Response for listing webhooks."""
    success: bool = Field(True, description="Request succeeded")
    webhooks: List[Webhook] = Field(default_factory=list, description="List of webhooks")
    error: Optional[str] = Field(None, description="Error message if failed")


class WebhookGetResponse(VikunjaBaseModel):
    """Response for getting a single webhook."""
    success: bool = Field(True, description="Request succeeded")
    webhook: Optional[Webhook] = Field(None, description="The requested webhook")
    error: Optional[str] = Field(None, description="Error message if failed")


class WebhookCreateResponse(VikunjaBaseModel):
    """Response for creating a webhook."""
    success: bool = Field(True, description="Request succeeded")
    webhook: Optional[Webhook] = Field(None, description="The created webhook")
    error: Optional[str] = Field(None, description="Error message if failed")


class WebhookDeleteResponse(VikunjaBaseModel):
    """Response for deleting a webhook."""
    success: bool = Field(True, description="Request succeeded")
    error: Optional[str] = Field(None, description="Error message if failed")
