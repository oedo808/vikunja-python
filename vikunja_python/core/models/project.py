"""
Project Models for Vikunja API

Covers: models.Project and related request/response types
API endpoints: /projects, /projects/{id}
"""

from pydantic import Field, field_validator
from datetime import datetime
from typing import Optional, Any
from .base import VikunjaBaseModel, User


# ============================================================================
# View Configuration Models (nested in Project)
# ============================================================================

class ViewFilter(VikunjaBaseModel):
    """
    Filter configuration for a project view.
    
    Used in: ProjectView.filter
    """
    s: Optional[str] = Field(None, description="Search term")
    sort_by: Optional[list[str]] = Field(None, description="Fields to sort by")
    order_by: Optional[str] = Field(None, description="Sort order (asc/desc)")
    filter: Optional[str] = Field(None, description="Filter expression (e.g., 'done = false')")
    filter_include_nulls: bool = Field(False, description="Include null values in filter")


class BucketConfiguration(VikunjaBaseModel):
    """
    Bucket configuration for Kanban/board views.
    
    Used in: ProjectView.bucket_configuration
    
    UNKNOWN: Full structure not yet verified from API response
    TODO: Extract from actual API call with project that has buckets configured
    """
    # UNKNOWN: Field definitions pending API verification
    mode: Optional[str] = Field(None, description="Configuration mode (none/manual)")
    # TODO: Add remaining fields after API inspection


class ProjectView(VikunjaBaseModel):
    """
    View configuration within a project.
    
    Vikunja supports multiple view types per project:
        - list: List view
        - gantt: Gantt chart view  
        - table: Table/spreadsheet view
        - kanban: Kanban board with buckets
    
    Used in: Project.views[]
    """
    id: int = Field(..., description="Unique view identifier")
    title: str = Field(..., description="View name/title")
    project_id: int = Field(..., description="Parent project ID")
    view_kind: str = Field(..., description="View type: list, gantt, table, kanban")
    
    # Filter configuration
    filter: Optional[ViewFilter] = Field(None, description="View filter settings")
    
    # Positioning
    position: int = Field(0, description="Display order within project")
    
    # Bucket configuration (for Kanban views)
    bucket_configuration_mode: str = Field("none", description="Bucket mode: none, manual, automatic")
    bucket_configuration: Optional[BucketConfiguration] = Field(None, description="Bucket settings")
    default_bucket_id: int = Field(0, description="Default bucket for new tasks")
    done_bucket_id: int = Field(0, description="Bucket for completed tasks")
    
    # Timestamps
    created: datetime = Field(..., description="Creation timestamp")
    updated: datetime = Field(..., description="Last update timestamp")


# ============================================================================
# Project Entity Model (18 fields from API)
# ============================================================================

class Project(VikunjaBaseModel):
    """
    Project model representing a project in Vikunja.
    
    API endpoint: GET /projects, GET /projects/{id}
    
    All 18 fields discovered from actual API response at v2.3.0:
    https://vikunja.ok9.io/api/v1/projects
    
    Nested Objects:
        - owner: User object (project creator)
        - views[]: Array of ProjectView objects
        - background_information: null or object (Unsplash background data)
    
    Special Values:
        - parent_project_id: 0 = root level project
        - position: 65536 for default Inbox project
        - max_permission: null or int (0=read, 1=write, 2=admin)
    """
    
    # Core Identification (5 fields)
    id: int = Field(..., description="Unique project identifier")
    title: str = Field(..., max_length=255, description="Project title")
    description: Optional[str] = Field(None, max_length=10000, description="Project description (markdown)")
    identifier: str = Field("", description="Short identifier/code for project")
    hex_color: str = Field("", description="Project color (without #)")
    
    # Hierarchy (2 fields)
    parent_project_id: int = Field(0, description="Parent project ID (0 = root level)")
    owner: User = Field(..., description="Project owner/creator")
    
    # Status Flags (2 fields)
    is_archived: bool = Field(False, description="Archived status")
    is_favorite: bool = Field(False, description="Marked as favorite/starred")
    
    # Positioning (1 field)
    position: int = Field(0, description="Display order (65536 for default Inbox)")
    
    # Settings & Configuration (4 fields)
    background_information: Optional[Any] = Field(None, description="Background image info (Unsplash data)")
    background_blur_hash: str = Field("", description="Blur hash for background preview")
    views: list[ProjectView] = Field(default_factory=list, description="Configured views for this project")
    max_permission: Optional[int] = Field(None, ge=0, le=2, description="Max permission level (0=read, 1=write, 2=admin)")
    
    # Timestamps (2 fields)
    created: datetime = Field(..., description="Creation timestamp")
    updated: datetime = Field(..., description="Last update timestamp")


# ============================================================================
# Project Request Models (for Create/Update operations)
# ============================================================================

class ProjectCreateRequest(VikunjaBaseModel):
    """
    Request body for creating a new project.
    
    Required fields: title
    Optional fields: All other project properties
    
    API endpoint: PUT /projects
    """
    title: str = Field(..., min_length=1, max_length=255, description="Project title (required)")
    
    # Optional fields - only send if explicitly set
    description: Optional[str] = Field(None, max_length=10000)
    identifier: Optional[str] = None
    hex_color: Optional[str] = None
    
    # Hierarchy
    parent_project_id: Optional[int] = Field(None, description="Parent project ID (omit for root)")
    
    def model_dump_for_api(self) -> dict:
        """Convert to dict, excluding None values."""
        return self.model_dump(exclude_none=True)


class ProjectUpdateRequest(VikunjaBaseModel):
    """
    Request body for updating an existing project.
    
    All fields optional - only provided fields are updated.
    
    API endpoint: POST /projects/{id} (PATCH semantics)
    """
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=10000)
    identifier: Optional[str] = None
    hex_color: Optional[str] = None
    is_archived: Optional[bool] = None
    is_favorite: Optional[bool] = None
    
    # Hierarchy (moving projects)
    parent_project_id: Optional[int] = None
    
    def model_dump_for_api(self) -> dict:
        """Convert to dict, excluding None values."""
        return self.model_dump(exclude_none=True)


# ============================================================================
# Project List Request/Response Models
# ============================================================================

class ProjectListRequest(VikunjaBaseModel):
    """
    Query parameters for listing projects.
    
    API endpoint: GET /projects
    
    Pagination headers returned:
        x-pagination-total-pages
        x-pagination-result-count
    """
    # Pagination
    page: int = Field(1, ge=1, description="Page number (1-based)")
    per_page: int = Field(50, ge=1, le=100, description="Items per page")
    
    # Filtering
    search: Optional[str] = Field(None, description="Search term for project title/description")
    sort_by: Optional[str] = Field(None, description="Field to sort by (e.g., 'title', 'updated')")


class ProjectListResponse(VikunjaBaseModel):
    """
    Response for project list operations.
    
    Includes pagination metadata from response headers.
    """
    success: bool = Field(True, description="Request succeeded")
    projects: list[Project] = Field(default_factory=list, description="List of projects")
    total_count: Optional[int] = Field(None, description="Total number of projects (across all pages)")
    page: Optional[int] = Field(None, description="Current page number")
    per_page: Optional[int] = Field(None, description="Items per page")
    total_pages: Optional[int] = Field(None, description="Total number of pages")
