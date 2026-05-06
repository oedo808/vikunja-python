"""
User and Team Models for Vikunja API

Covers: user.User, v1.UserSettings, models.ProjectUser, models.Team, etc.
API endpoints: /user, /teams, /projects/{id}/users

User Management:
- User profiles with settings
- Authentication (login, register, password reset)
- TOTP 2FA setup and verification

Team Management:
- Team creation and membership
- Project-team associations with permissions
- Team-based access control

Permission Levels (3 levels):
- 0 (Read): Read-only access
- 1 (Write): Read + Create/Update/Delete own items
- 2 (Admin): Full access including member management

Usage Examples:
    # Login and get token
    login = LoginRequest(username="alice", password="secret", long_token=True)
    
    # Create a team
    team = TeamCreateRequest(
        name="Engineering",
        description="Core engineering team",
        is_public=True
    )
    
    # Add user to project with write permission
    project_user = ProjectUserCreateRequest(
        username="bob",
        permission=Permission.WRITE  # or 1
    )
"""

from pydantic import Field, field_validator
from datetime import datetime
from typing import Optional, Dict, Any, Literal
from .base import VikunjaBaseModel


# ============================================================================
# Permission Enum (3 levels)
# ============================================================================

Permission = Literal[0, 1, 2]
"""Permission level for project/team access.

API spec: models.Permission

Values:
    0 (Read): Read-only access
    1 (Write): Read + Create/Update/Delete own items  
    2 (Admin): Full access including member management

Usage:
    from models.user import Permission
    
    # Grant write access to a user
    project_user = ProjectUserCreateRequest(
        username="bob",
        permission=Permission.WRITE  # or simply 1
    )
"""

# Named constants for clarity
Permission.READ: Permission = 0
Permission.WRITE: Permission = 1
Permission.ADMIN: Permission = 2

PERMISSION_DESCRIPTIONS: Dict[Permission, str] = {
    0: "Read-only access - can view but not modify",
    1: "Write access - can create, update, delete own items",
    2: "Admin access - full control including member management",
}


# ============================================================================
# Core User Models
# ============================================================================

class User(VikunjaBaseModel):
    """
    Basic user information.
    
    API endpoint: Referenced in many endpoints (assignees, created_by, etc.)
    
    This is the minimal user object returned in nested contexts like task
    assignees or label creators. For full user profiles, use UserWithSettings.
    
    Fields from API spec (user.User):
        - id: Unique user identifier
        - username: Unique username (1-250 chars)
        - name: Full display name
        - email: User's email address (max 250 chars)
        - created: Account creation timestamp
        - updated: Last update timestamp
    
    Example from API response:
        {
            "id": 1,
            "username": "alice",
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "created": "2024-01-15T10:30:00Z",
            "updated": "2024-01-20T14:45:00Z"
        }
    """
    
    # Core Identification (2 fields)
    id: Optional[int] = Field(None, description="Unique user ID")
    username: str = Field(
        ..., 
        min_length=1, 
        max_length=250,
        description="Unique username"
    )
    
    # Profile Information (2 fields)
    name: Optional[str] = Field(None, description="Full display name")
    email: Optional[str] = Field(
        None, 
        max_length=250,
        description="User's email address"
    )
    
    # Timestamps (2 fields - auto-managed)
    created: Optional[datetime] = Field(None, description="Account creation timestamp")
    updated: Optional[datetime] = Field(None, description="Last update timestamp")


class UserSettings(VikunjaBaseModel):
    """
    User settings and preferences.
    
    API endpoint: Part of UserWithSettings response
    
    Contains user-specific configuration for the Vikunja instance.
    
    Fields from API spec (v1.UserSettings):
        - default_project_id: Default project for new tasks
        - language: User's language preference
        - timezone: Timezone for reminders and displays
        - week_start: Day when week starts (0=Sunday, 1=Monday)
        - discoverable_by_email/name: Privacy settings
        - email_reminders_enabled: Email notification toggle
        - overdue_tasks_reminders_enabled/Time: Daily summary settings
        - extra_settings_links: OpenID-provided links
        - frontend_settings: Frontend-specific settings
    
    Example from API response:
        {
            "default_project_id": 1,
            "language": "en",
            "timezone": "America/New_York",
            "week_start": 1,
            "discoverable_by_email": true,
            "discoverable_by_name": true,
            "email_reminders_enabled": true,
            "overdue_tasks_reminders_enabled": true,
            "overdue_tasks_reminders_time": "09:00"
        }
    """
    
    # Project Settings (1 field)
    default_project_id: Optional[int] = Field(
        None, 
        description="Default project ID for new tasks without specified project"
    )
    
    # Localization (3 fields)
    language: Optional[str] = Field(None, description="User's language preference")
    timezone: Optional[str] = Field(None, description="Timezone for reminders/displays")
    week_start: Optional[int] = Field(
        None, 
        ge=0, 
        le=6,
        description="Day when week starts (0=Sunday, 1=Monday, etc.)"
    )
    
    # Privacy Settings (2 fields)
    discoverable_by_email: Optional[bool] = Field(
        None, 
        description="Can be found by searching exact email"
    )
    discoverable_by_name: Optional[bool] = Field(
        None, 
        description="Can be found by searching name/partial name"
    )
    
    # Notification Settings (3 fields)
    email_reminders_enabled: Optional[bool] = Field(
        None, 
        description="Enable email reminders for tasks"
    )
    overdue_tasks_reminders_enabled: Optional[bool] = Field(
        None, 
        description="Enable daily overdue task summaries"
    )
    overdue_tasks_reminders_time: Optional[str] = Field(
        None, 
        description="Time for daily overdue summary (e.g., '09:00')"
    )
    
    # Extended Settings (2 fields)
    extra_settings_links: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional settings links from OpenID"
    )
    frontend_settings: Optional[Dict[str, Any]] = Field(
        None, 
        description="Frontend-specific settings"
    )


class UserWithSettings(VikunjaBaseModel):
    """
    Full user profile with settings.
    
    API endpoint: GET /user
    
    Combines basic user info with their complete settings.
    
    Fields from API spec (v1.UserWithSettings):
        - All User fields (id, username, name, email, created, updated)
        - settings: Complete UserSettings object
        - auth_provider: Authentication provider type
        - is_local_user: Whether user is locally authenticated
        - deletion_scheduled_at: Account deletion timestamp (if scheduled)
    
    Example from API response:
        {
            "id": 1,
            "username": "alice",
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "created": "2024-01-15T10:30:00Z",
            "updated": "2024-01-20T14:45:00Z",
            "settings": {...},
            "auth_provider": "local",
            "is_local_user": true
        }
    """
    
    # Core User Fields (6 fields)
    id: Optional[int] = Field(None, description="Unique user ID")
    username: str = Field(
        ..., 
        min_length=1, 
        max_length=250,
        description="Unique username"
    )
    name: Optional[str] = Field(None, description="Full display name")
    email: Optional[str] = Field(
        None, 
        max_length=250,
        description="User's email address"
    )
    created: Optional[datetime] = Field(None, description="Account creation timestamp")
    updated: Optional[datetime] = Field(None, description="Last update timestamp")
    
    # Settings (1 field)
    settings: Optional[UserSettings] = Field(None, description="User settings and preferences")
    
    # Authentication Info (3 fields)
    auth_provider: Optional[str] = Field(None, description="Authentication provider type")
    is_local_user: Optional[bool] = Field(None, description="Whether user is locally authenticated")
    deletion_scheduled_at: Optional[datetime] = Field(
        None, 
        description="Account deletion timestamp (if scheduled)"
    )


# ============================================================================
# Authentication Request Models
# ============================================================================

class LoginRequest(VikunjaBaseModel):
    """
    Request body for user login.
    
    API endpoint: POST /user/login
    
    Required fields: username, password
    Optional fields: totp_passcode (if 2FA enabled), long_token
    
    Example:
        req = LoginRequest(
            username="alice",
            password="secret123",
            totp_passcode="123456",  # If 2FA enabled
            long_token=True           # "Remember me" style login
        )
    """
    username: str = Field(..., description="Username for login")
    password: str = Field(..., description="User's password")
    totp_passcode: Optional[str] = Field(None, description="TOTP passcode if 2FA enabled")
    long_token: Optional[bool] = Field(
        None, 
        description="Long-lived token for 'remember me' style login"
    )
    
    def model_dump_for_api(self) -> dict:
        """Convert to dict for API submission."""
        return self.model_dump(exclude_none=True)


class RegisterRequest(VikunjaBaseModel):
    """
    Request body for user registration.
    
    API endpoint: POST /user
    
    Note: Full structure may vary based on Vikunja configuration.
    This is a placeholder - verify with actual API response.
    
    UNKNOWN: Full register request structure requires API testing
    """
    # Placeholder - needs verification from actual API
    username: Optional[str] = Field(None, description="Desired username")
    email: Optional[str] = Field(None, description="User's email address")
    password: Optional[str] = Field(None, description="Desired password")


class EmailUpdateRequest(VikunjaBaseModel):
    """
    Request body for updating email address.
    
    API endpoint: POST /user/email
    
    Required fields: new_email, password (for confirmation)
    
    Example:
        req = EmailUpdateRequest(
            new_email="alice@newdomain.com",
            password="current_password"
        )
    """
    new_email: str = Field(..., description="New email address (must be valid)")
    password: str = Field(..., description="Current password for confirmation")
    
    def model_dump_for_api(self) -> dict:
        """Convert to dict for API submission."""
        return self.model_dump(exclude_none=True)


class PasswordResetRequest(VikunjaBaseModel):
    """
    Request body for password reset.
    
    API endpoint: POST /user/password/reset
    
    Required fields: token, new_password
    
    Password requirements: 8-72 characters
    
    Example:
        req = PasswordResetRequest(
            token="reset_token_from_email",
            new_password="new_secure_password123"
        )
    """
    token: str = Field(..., description="Password reset token from email")
    new_password: str = Field(
        ..., 
        min_length=8, 
        max_length=72,
        description="New password (8-72 characters)"
    )
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """Basic password validation."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v
    
    def model_dump_for_api(self) -> dict:
        """Convert to dict for API submission."""
        return self.model_dump(exclude_none=True)


# ============================================================================
# TOTP (2FA) Models
# ============================================================================

class TOTPSetupResponse(VikunjaBaseModel):
    """
    Response for TOTP setup initiation.
    
    API endpoint: POST /user/totp
    
    Returns the secret and URL needed to configure TOTP authenticator app.
    
    Fields from API spec (models.TOTP):
        - secret: TOTP secret key
        - url: OTPAuth URL for QR code generation
        - enabled: Whether TOTP is enabled (false until verified)
    
    Example from API response:
        {
            "secret": "JBSWY3DPEHPK3PXP",
            "url": "otpauth://totp/Vikunja:alice?secret=JBSWY3DPEHPK3PXP...",
            "enabled": false
        }
    """
    secret: Optional[str] = Field(None, description="TOTP secret key")
    url: Optional[str] = Field(None, description="OTPAuth URL for QR code")
    enabled: Optional[bool] = Field(None, description="Whether TOTP is enabled")


class TOTPPasscodeRequest(VikunjaBaseModel):
    """
    Request body for TOTP passcode verification.
    
    API endpoint: POST /user/totp/verify
    
    Required fields: passcode
    
    Example:
        req = TOTPPasscodeRequest(passcode="123456")
    """
    passcode: str = Field(..., description="TOTP passcode from authenticator app")
    
    def model_dump_for_api(self) -> dict:
        """Convert to dict for API submission."""
        return self.model_dump(exclude_none=True)


# ============================================================================
# Project User Models (Project Membership)
# ============================================================================

class ProjectUser(VikunjaBaseModel):
    """
    User's membership in a project with permission level.
    
    API endpoint: GET /projects/{id}/users
    
    Represents the relationship between a user and a project.
    
    Fields from API spec (models.ProjectUser):
        - id: Unique relation identifier
        - username: Username of the member
        - permission: Permission level (0=Read, 1=Write, 2=Admin)
        - created: Relation creation timestamp
        - updated: Last update timestamp
    
    Example from API response:
        {
            "id": 5,
            "username": "bob",
            "permission": 1,
            "created": "2024-01-15T10:30:00Z",
            "updated": "2024-01-15T10:30:00Z"
        }
    """
    
    # Core Identification (2 fields)
    id: Optional[int] = Field(None, description="Unique relation ID")
    username: str = Field(..., description="Username of the project member")
    
    # Access Control (1 field)
    permission: Optional[Permission] = Field(
        0,
        description="Permission level: 0=Read, 1=Write, 2=Admin"
    )
    
    # Timestamps (2 fields - auto-managed)
    created: Optional[datetime] = Field(None, description="Relation creation timestamp")
    updated: Optional[datetime] = Field(None, description="Last update timestamp")


class ProjectUserCreateRequest(VikunjaBaseModel):
    """
    Request body for adding a user to a project.
    
    API endpoint: POST /projects/{id}/users
    
    Required fields: username
    Optional fields: permission (defaults to 0 = Read)
    
    Example:
        req = ProjectUserCreateRequest(
            username="bob",
            permission=Permission.WRITE  # or 1
        )
    """
    username: str = Field(..., description="Username to add to project")
    permission: Optional[Permission] = Field(
        0, 
        description="Permission level (default: 0=Read)"
    )
    
    def model_dump_for_api(self) -> dict:
        """Convert to dict for API submission."""
        return self.model_dump(exclude_none=True)


class ProjectUserUpdateRequest(VikunjaBaseModel):
    """
    Request body for updating project membership.
    
    API endpoint: POST /projects/{id}/users/{username}
    
    Only provided fields are updated.
    
    Example:
        req = ProjectUserUpdateRequest(
            permission=Permission.ADMIN  # Promote to admin
        )
    """
    permission: Optional[Permission] = Field(None, description="New permission level")
    
    def model_dump_for_api(self) -> dict:
        """Convert to dict, excluding None values."""
        return self.model_dump(exclude_none=True)


# ============================================================================
# Team Models
# ============================================================================

class TeamUser(VikunjaBaseModel):
    """
    User information within a team context.
    
    API endpoint: Part of Team response (members array)
    
    Similar to basic User but used specifically in team membership lists.
    
    Fields from API spec (models.TeamUser):
        - id: User ID
        - username: Unique username
        - name: Full display name
        - email: User's email
        - admin: Whether user is team admin
        - created/updated: Timestamps
    
    Example from API response:
        {
            "id": 1,
            "username": "alice",
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "admin": true,
            "created": "2024-01-15T10:30:00Z",
            "updated": "2024-01-15T10:30:00Z"
        }
    """
    
    # Core Identification (2 fields)
    id: Optional[int] = Field(None, description="User ID")
    username: str = Field(
        ..., 
        min_length=1, 
        max_length=250,
        description="Unique username"
    )
    
    # Profile Information (2 fields)
    name: Optional[str] = Field(None, description="Full display name")
    email: Optional[str] = Field(
        None, 
        max_length=250,
        description="User's email address"
    )
    
    # Team Role (1 field)
    admin: Optional[bool] = Field(
        None, 
        description="Whether member is team admin"
    )
    
    # Timestamps (2 fields - auto-managed)
    created: Optional[datetime] = Field(None, description="Membership creation timestamp")
    updated: Optional[datetime] = Field(None, description="Last update timestamp")


class TeamMember(VikunjaBaseModel):
    """
    Team membership relation.
    
    API endpoint: GET /teams/{id}/members
    
    Represents a user's membership in a team (without full user details).
    
    Fields from API spec (models.TeamMember):
        - id: Unique relation identifier
        - username: Username of the member
        - admin: Whether member is team admin
        - created: Membership creation timestamp
    
    Example from API response:
        {
            "id": 10,
            "username": "bob",
            "admin": false,
            "created": "2024-01-15T10:30:00Z"
        }
    """
    
    # Core Identification (2 fields)
    id: Optional[int] = Field(None, description="Unique relation ID")
    username: str = Field(
        ..., 
        min_length=1, 
        max_length=250,
        description="Username of the team member"
    )
    
    # Role (1 field)
    admin: Optional[bool] = Field(None, description="Whether member is team admin")
    
    # Timestamp (1 field - auto-managed)
    created: Optional[datetime] = Field(None, description="Membership creation timestamp")


class Team(VikunjaBaseModel):
    """
    A team of users for collaborative access control.
    
    API endpoint: GET /teams
    
    Teams allow grouping users for shared project permissions.
    
    Fields from API spec (models.Team):
        - id: Unique team identifier
        - name: Team name (1-250 chars)
        - description: Optional team description
        - is_public: Whether team is discoverable when sharing projects
        - external_id: External ID from OpenID/LDAP provider
        - members: Array of TeamUser objects
        - created_by: User who created the team
        - created/updated: Timestamps
    
    Example from API response:
        {
            "id": 1,
            "name": "Engineering",
            "description": "Core engineering team",
            "is_public": true,
            "external_id": null,
            "members": [...],
            "created_by": {...},
            "created": "2024-01-15T10:30:00Z",
            "updated": "2024-01-20T14:45:00Z"
        }
    """
    
    # Core Identification (2 fields)
    id: Optional[int] = Field(None, description="Unique team ID")
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=250,
        description="Team name"
    )
    
    # Team Configuration (3 fields)
    description: Optional[str] = Field(None, description="Team description")
    is_public: Optional[bool] = Field(
        None, 
        description="Whether team is discoverable when sharing projects"
    )
    external_id: Optional[str] = Field(
        None, 
        max_length=250,
        description="External ID from OpenID/LDAP provider"
    )
    
    # Members (1 field)
    members: Optional[list[TeamUser]] = Field(
        None, 
        description="Array of team members"
    )
    
    # Metadata (3 fields)
    created_by: Optional[User] = Field(None, description="User who created this team")
    created: Optional[datetime] = Field(None, description="Team creation timestamp")
    updated: Optional[datetime] = Field(None, description="Last update timestamp")


class TeamCreateRequest(VikunjaBaseModel):
    """
    Request body for creating a team.
    
    API endpoint: POST /teams
    
    Required fields: name
    Optional fields: description, is_public
    
    Example:
        req = TeamCreateRequest(
            name="Engineering",
            description="Core engineering team",
            is_public=True
        )
    """
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=250,
        description="Team name (required)"
    )
    description: Optional[str] = Field(None, description="Team description")
    is_public: Optional[bool] = Field(
        None, 
        description="Whether team is discoverable when sharing projects"
    )
    
    def model_dump_for_api(self) -> dict:
        """Convert to dict for API submission."""
        return self.model_dump(exclude_none=True)


class TeamUpdateRequest(VikunjaBaseModel):
    """
    Request body for updating a team.
    
    API endpoint: POST /teams/{id}
    
    All fields are optional - only provided fields are updated.
    
    Example:
        req = TeamUpdateRequest(
            description="Updated engineering team description"
        )
    """
    name: Optional[str] = Field(None, min_length=1, max_length=250, description="New team name")
    description: Optional[str] = Field(None, description="New team description")
    is_public: Optional[bool] = Field(None, description="New public visibility setting")
    
    def model_dump_for_api(self) -> dict:
        """Convert to dict, excluding None values."""
        return self.model_dump(exclude_none=True)


class TeamWithPermission(Team):
    """
    Team with an additional permission level.
    
    API endpoint: Used in team-project contexts
    
    Extends Team with a permission field for project-team relationships.
    
    Fields from API spec (models.TeamWithPermission):
        - All Team fields
        - permission: Permission level for the context (0=Read, 1=Write, 2=Admin)
    """
    permission: Optional[Permission] = Field(
        None, 
        description="Permission level in this context"
    )


class TeamProject(VikunjaBaseModel):
    """
    Team's membership in a project with permission level.
    
    API endpoint: GET /projects/{id}/teams
    
    Represents the relationship between a team and a project.
    
    Fields from API spec (models.TeamProject):
        - id: Unique relation identifier
        - team_id: Team ID
        - permission: Permission level (0=Read, 1=Write, 2=Admin)
        - created/updated: Timestamps
    
    Example from API response:
        {
            "id": 15,
            "team_id": 1,
            "permission": 2,
            "created": "2024-01-15T10:30:00Z",
            "updated": "2024-01-15T10:30:00Z"
        }
    """
    
    # Core Identification (2 fields)
    id: Optional[int] = Field(None, description="Unique relation ID")
    team_id: int = Field(..., description="Team ID")
    
    # Access Control (1 field)
    permission: Optional[Permission] = Field(
        0,
        description="Permission level: 0=Read, 1=Write, 2=Admin"
    )
    
    # Timestamps (2 fields - auto-managed)
    created: Optional[datetime] = Field(None, description="Relation creation timestamp")
    updated: Optional[datetime] = Field(None, description="Last update timestamp")


# ============================================================================
# Response Models
# ============================================================================

class UserGetResponse(VikunjaBaseModel):
    """Response for getting current user."""
    success: bool = Field(True, description="Request succeeded")
    user: Optional[UserWithSettings] = Field(None, description="Current user with settings")
    error: Optional[str] = Field(None, description="Error message if failed")


class LoginResponse(VikunjaBaseModel):
    """Response for login request."""
    success: bool = Field(True, description="Request succeeded")
    token: Optional[str] = Field(None, description="Authentication token")
    user: Optional[User] = Field(None, description="Logged in user")
    error: Optional[str] = Field(None, description="Error message if failed")


class TeamListResponse(VikunjaBaseModel):
    """Response for listing teams."""
    success: bool = Field(True, description="Request succeeded")
    teams: list[Team] = Field(default_factory=list, description="List of teams")
    error: Optional[str] = Field(None, description="Error message if failed")


class TeamGetResponse(VikunjaBaseModel):
    """Response for getting a single team."""
    success: bool = Field(True, description="Request succeeded")
    team: Optional[Team] = Field(None, description="The requested team")
    error: Optional[str] = Field(None, description="Error message if failed")


class ProjectUserListResponse(VikunjaBaseModel):
    """Response for listing project users."""
    success: bool = Field(True, description="Request succeeded")
    users: list[ProjectUser] = Field(default_factory=list, description="List of project users")
    error: Optional[str] = Field(None, description="Error message if failed")
