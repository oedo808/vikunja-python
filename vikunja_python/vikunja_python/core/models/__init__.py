"""
Vikunja Pydantic Models - Package Exports

This package provides Pydantic v2 models for the Vikunja API (v2.3.0).
Models are the source of truth for all API interactions.

Usage:
    from vikunja_python.models import Task, Project, TaskCreateRequest
    
    # Create a task
    task = TaskCreateRequest(title="My Task", priority=3)
"""

# Base configuration and shared models
from .base import (
    VikunjaBaseModel,
    User,
    ErrorDetail,
    Message,
    Token,
    PaginationInfo,
    ListResponse,
)

# Task models
from .task import (
    Task,
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskListRequest,
    TaskListResponse,
)

# Project models
from .project import (
    Project,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectListRequest,
    ProjectListResponse,
    ProjectView,
    ViewFilter,
    BucketConfiguration,
)

# Filter models
from .filter import (
    SavedFilter,
    SavedFilterCreateRequest,
    SavedFilterUpdateRequest,
    SavedFilterListResponse,
    SavedFilterGetResponse,
    TaskCollection,
)

# Label models
from .label import (
    Label,
    LabelCreateRequest,
    LabelUpdateRequest,
    LabelListResponse,
    LabelGetResponse,
    LabelCreateResponse,
    LabelUpdateResponse,
)

# Task expansion models (comments, attachments, reminders)
from .task_expansion import (
    TaskComment,
    TaskAttachment,
    TaskReminder,
    ReminderRelation,
    TaskCommentsResponse,
    TaskAttachmentsResponse,
    TaskRemindersResponse,
)

# Relationship models
from .relation import (
    RelationKind,
    RELATION_KIND_DESCRIPTIONS,
    TaskRelation,
    TaskRelationCreateRequest,
    TaskRelationUpdateRequest,
    TaskRelationListResponse,
    TaskRelationGetResponse,
)

# User and Team models
from .user import (
    # Core user models
    User,
    UserSettings,
    UserWithSettings,
    
    # Permission enum
    Permission,
    PERMISSION_DESCRIPTIONS,
    
    # Auth request models
    LoginRequest,
    RegisterRequest,
    EmailUpdateRequest,
    PasswordResetRequest,
    
    # TOTP models
    TOTPSetupResponse,
    TOTPPasscodeRequest,
    
    # Project user models
    ProjectUser,
    ProjectUserCreateRequest,
    ProjectUserUpdateRequest,
    
    # Team models
    TeamUser,
    TeamMember,
    Team,
    TeamCreateRequest,
    TeamUpdateRequest,
    TeamWithPermission,
    TeamProject,
    
    # Response models
    UserGetResponse,
    LoginResponse,
    TeamListResponse,
    TeamGetResponse,
    ProjectUserListResponse,
)

# CSV Import and Migration models
from .migration import (
    # CSV Task Attribute enum
    TaskAttribute,
    AttrTitle,
    AttrDescription,
    AttrDueDate,
    AttrStartDate,
    AttrEndDate,
    AttrDone,
    AttrPriority,
    AttrLabels,
    AttrProject,
    AttrReminder,
    AttrIgnore,
    
    # CSV Import models
    ColumnMapping,
    DetectionResult,
    PreviewTask,
    PreviewResult,
    
    # Migration models
    MigrationStatus,
    MicrosoftTodoMigrationRequest,
    TodoistMigrationRequest,
    TrelloMigrationRequest,
    
    # Response models
    CSVImportResponse,
    MigrationResponse,
    MigrationStatusResponse,
)

# Webhook models
from .webhook import (
    # Webhook Event types
    WebhookEvent,
    TaskCreated,
    TaskUpdated,
    TaskDeleted,
    TaskCompleted,
    TaskUncompleted,
    CommentCreated,
    CommentUpdated,
    CommentDeleted,
    
    # Webhook models
    Webhook,
    WebhookCreateRequest,
    WebhookUpdateRequest,
    
    # Response models
    WebhookListResponse,
    WebhookGetResponse,
    WebhookCreateResponse,
    WebhookDeleteResponse,
)

# API Token models (Phase 5 - High Priority)
from .api_token import (
    # Enums
    Permission as APIPermission,
    SharingType as APISharingType,
    
    # Core models
    RouteDetail,
    APITokenRoute,
    APIToken,
    
    # Request models
    APITokenCreateRequest,
    APITokenUpdateRequest,
    
    # Response models
    APITokenListResponse,
    APITokenGetResponse,
    APITokenCreateResponse,
    APITokenDeleteResponse,
)

# Bulk Assignment models (Phase 5 - High Priority)
from .bulk_assignees import (
    User as BulkUser,
    BulkAssignees,
    BulkAssigneesCreateRequest,
    BulkAssigneesResponse,
    BulkTask,
    BulkTaskResponse,
)

# Link Sharing models (Phase 5 - High Priority)
from .link_sharing import (
    # Enums
    SharingType,
    Permission as LinkPermission,
    
    # Core models
    LinkSharing,
    
    # Request models
    LinkSharingCreateRequest,
    LinkSharingUpdateRequest,
    
    # Response models
    LinkSharingListResponse,
    LinkSharingGetResponse,
    LinkSharingCreateResponse,
    LinkSharingDeleteResponse,
)

__all__ = [
    # Base models
    "VikunjaBaseModel",
    "User",
    "ErrorDetail",
    "Message",
    "Token",
    "PaginationInfo",
    "ListResponse",
    
    # Task models
    "Task",
    "TaskCreateRequest",
    "TaskUpdateRequest",
    "TaskListRequest",
    "TaskListResponse",
    
    # Project models
    "Project",
    "ProjectCreateRequest",
    "ProjectUpdateRequest",
    "ProjectListRequest",
    "ProjectListResponse",
    "ProjectView",
    "ViewFilter",
    "BucketConfiguration",
    
    # Filter models
    "SavedFilter",
    "SavedFilterCreateRequest",
    "SavedFilterUpdateRequest",
    "SavedFilterListResponse",
    "SavedFilterGetResponse",
    "TaskCollection",
    
    # Label models
    "Label",
    "LabelCreateRequest",
    "LabelUpdateRequest",
    "LabelListResponse",
    "LabelGetResponse",
    "LabelCreateResponse",
    "LabelUpdateResponse",
    
    # Task expansion models (comments, attachments, reminders)
    "TaskComment",
    "TaskAttachment",
    "TaskReminder",
    "ReminderRelation",
    "TaskCommentsResponse",
    "TaskAttachmentsResponse",
    "TaskRemindersResponse",
    
    # Relationship models
    "RelationKind",
    "RELATION_KIND_DESCRIPTIONS",
    "TaskRelation",
    "TaskRelationCreateRequest",
    "TaskRelationUpdateRequest",
    "TaskRelationListResponse",
    "TaskRelationGetResponse",
    
    # User and Team models
    "User",
    "UserSettings",
    "UserWithSettings",
    "Permission",
    "PERMISSION_DESCRIPTIONS",
    "LoginRequest",
    "RegisterRequest",
    "EmailUpdateRequest",
    "PasswordResetRequest",
    "TOTPSetupResponse",
    "TOTPPasscodeRequest",
    "ProjectUser",
    "ProjectUserCreateRequest",
    "ProjectUserUpdateRequest",
    "TeamUser",
    "TeamMember",
    "Team",
    "TeamCreateRequest",
    "TeamUpdateRequest",
    "TeamWithPermission",
    "TeamProject",
    "UserGetResponse",
    "LoginResponse",
    "TeamListResponse",
    "TeamGetResponse",
    "ProjectUserListResponse",
    
    # CSV Import and Migration models
    "TaskAttribute",
    "AttrTitle",
    "AttrDescription",
    "AttrDueDate",
    "AttrStartDate",
    "AttrEndDate",
    "AttrDone",
    "AttrPriority",
    "AttrLabels",
    "AttrProject",
    "AttrReminder",
    "AttrIgnore",
    "ColumnMapping",
    "DetectionResult",
    "PreviewTask",
    "PreviewResult",
    "MigrationStatus",
    "MicrosoftTodoMigrationRequest",
    "TodoistMigrationRequest",
    "TrelloMigrationRequest",
    "CSVImportResponse",
    "MigrationResponse",
    "MigrationStatusResponse",
    
    # Webhook models
    "WebhookEvent",
    "TaskCreated",
    "TaskUpdated",
    "TaskDeleted",
    "TaskCompleted",
    "TaskUncompleted",
    "CommentCreated",
    "CommentUpdated",
    "CommentDeleted",
    "Webhook",
    "WebhookCreateRequest",
    "WebhookUpdateRequest",
    "WebhookListResponse",
    "WebhookGetResponse",
    "WebhookCreateResponse",
    "WebhookDeleteResponse",
]

__version__ = "0.6.0"
