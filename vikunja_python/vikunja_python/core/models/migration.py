"""
CSV Import and Migration Models for Vikunja API

Covers: csv.* (CSV import), migration.Status, microsofttodo.*, todoist.*, trello.*

CSV Import Workflow:
1. Upload CSV file → GET /import/csv/preview
2. Get DetectionResult with suggested column mappings
3. Submit ColumnMapping to configure import
4. POST /import/csv to complete import

Migration Workflow:
1. Authenticate with external service (Microsoft Todo, Todoist, Trello)
2. POST /migration/{service} with auth code
3. Monitor migration status via GET /migration/status

Supported Migration Sources:
- Microsoft Todo
- Todoist  
- Trello
"""

from pydantic import Field
from datetime import datetime
from typing import Optional, List, Any
from .base import VikunjaBaseModel


# ============================================================================
# CSV Task Attribute Enum (11 values)
# ============================================================================

TaskAttribute = str
"""CSV column attribute mapping.

API spec: csv.TaskAttribute

Enum Values:
    "title" - Task title (AttrTitle)
    "description" - Task description (AttrDescription)
    "due_date" - Due date field (AttrDueDate)
    "start_date" - Start date field (AttrStartDate)
    "end_date" - End date field (AttrEndDate)
    "done" - Completion status (AttrDone)
    "priority" - Priority level (AttrPriority)
    "labels" - Labels/Tags (AttrLabels)
    "project" - Project assignment (AttrProject)
    "reminder" - Reminder date/time (AttrReminder)
    "ignore" - Skip this column (AttrIgnore)

Usage:
    from models.migration import TaskAttribute
    
    # Map CSV columns to task attributes
    mapping = ColumnMapping(
        attribute=TaskAttribute("title"),
        column_name="Task Name",
        column_index=0
    )
"""

# Named constants for clarity
AttrTitle = "title"
AttrDescription = "description"
AttrDueDate = "due_date"
AttrStartDate = "start_date"
AttrEndDate = "end_date"
AttrDone = "done"
AttrPriority = "priority"
AttrLabels = "labels"
AttrProject = "project"
AttrReminder = "reminder"
AttrIgnore = "ignore"


# ============================================================================
# CSV Import Models
# ============================================================================

class ColumnMapping(VikunjaBaseModel):
    """
    Mapping between a CSV column and a task attribute.
    
    API endpoint: Part of CSV import configuration
    
    Maps a specific column from the uploaded CSV file to a Vikunja task attribute.
    
    Fields from API spec (csv.ColumnMapping):
        - attribute: The task attribute to map to
        - column_index: Zero-based index of the column in CSV
        - column_name: Human-readable name of the column
    
    Example from API response:
        {
            "attribute": "title",
            "column_index": 0,
            "column_name": "Task Name"
        }
    
    Usage:
        # Map first column to task title
        mapping = ColumnMapping(
            attribute=AttrTitle,
            column_index=0,
            column_name="Task Name"
        )
        
        # Ignore a column (e.g., notes that don't map to any field)
        ignore_mapping = ColumnMapping(
            attribute=AttrIgnore,
            column_index=5,
            column_name="Internal Notes"
        )
    """
    
    # Core Mapping (3 fields)
    attribute: TaskAttribute = Field(
        ..., 
        description="Task attribute to map this column to"
    )
    column_index: int = Field(..., ge=0, description="Zero-based column index in CSV")
    column_name: str = Field(..., description="Human-readable column name")


class DetectionResult(VikunjaBaseModel):
    """
    CSV file detection and analysis result.
    
    API endpoint: GET /import/csv/preview
    
    Returned when uploading a CSV file for import. Contains detected format
    information and suggested column mappings.
    
    Fields from API spec (csv.DetectionResult):
        - columns: List of column names from first row
        - delimiter: Detected delimiter (comma, semicolon, tab, etc.)
        - quote_char: Detected quote character
        - date_format: Detected date format string
        - preview_rows: Sample data rows (typically 5-10 rows)
        - suggested_mapping: Auto-detected column-to-attribute mappings
    
    Example from API response:
        {
            "columns": ["Task Name", "Description", "Due Date", "Done"],
            "delimiter": ",",
            "quote_char": "\"",
            "date_format": "%Y-%m-%d",
            "preview_rows": [
                ["Buy milk", "Groceries", "2024-01-20", "false"],
                ["Write report", "Work", "2024-01-25", "true"]
            ],
            "suggested_mapping": [
                {"attribute": "title", "column_index": 0, "column_name": "Task Name"},
                {"attribute": "description", "column_index": 1, "column_name": "Description"},
                {"attribute": "due_date", "column_index": 2, "column_name": "Due Date"},
                {"attribute": "done", "column_index": 3, "column_name": "Done"}
            ]
        }
    
    Usage:
        # Get detection result after uploading CSV
        detection = DetectionResult.model_validate(api_response)
        
        # Use suggested mappings or customize
        for mapping in detection.suggested_mapping:
            print(f"Column '{mapping.column_name}' → {mapping.attribute}")
    """
    
    # Format Detection (4 fields)
    columns: Optional[List[str]] = Field(
        None, 
        description="Column names from first row of CSV"
    )
    delimiter: Optional[str] = Field(None, description="Detected field delimiter")
    quote_char: Optional[str] = Field(None, description="Detected quote character")
    date_format: Optional[str] = Field(None, description="Detected date format string")
    
    # Preview Data (1 field)
    preview_rows: Optional[List[List[str]]] = Field(
        None, 
        description="Sample data rows from CSV"
    )
    
    # Suggested Mappings (1 field)
    suggested_mapping: Optional[List[ColumnMapping]] = Field(
        None, 
        description="Auto-detected column-to-attribute mappings"
    )


class PreviewTask(VikunjaBaseModel):
    """
    A single task preview from CSV import.
    
    API endpoint: Part of PreviewResult
    
    Represents how a row from the CSV file will be imported as a task.
    
    Fields from API spec (csv.PreviewTask):
        - title: Task title
        - description: Task description
        - due_date: Due date string
        - start_date: Start date string
        - end_date: End date string
        - done: Completion status
        - priority: Priority level
        - labels: List of label names
        - project: Project name
    
    Example from API response:
        {
            "title": "Buy milk",
            "description": "Groceries",
            "due_date": "2024-01-20",
            "start_date": null,
            "end_date": null,
            "done": false,
            "priority": 0,
            "labels": ["shopping"],
            "project": "Personal"
        }
    """
    
    # Core Task Fields (3 fields)
    title: Optional[str] = Field(None, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    done: Optional[bool] = Field(None, description="Completion status")
    
    # Date Fields (3 fields)
    due_date: Optional[str] = Field(None, description="Due date string")
    start_date: Optional[str] = Field(None, description="Start date string")
    end_date: Optional[str] = Field(None, description="End date string")
    
    # Additional Fields (3 fields)
    priority: Optional[int] = Field(None, ge=0, description="Priority level")
    labels: Optional[List[str]] = Field(None, description="List of label names")
    project: Optional[str] = Field(None, description="Project name")


class PreviewResult(VikunjaBaseModel):
    """
    CSV import preview result.
    
    API endpoint: GET /import/csv/preview
    
    Shows how the uploaded CSV file will be imported, with all tasks parsed.
    
    Fields from API spec (csv.PreviewResult):
        - tasks: List of parsed tasks from CSV rows
        - total_rows: Total number of rows in CSV
    
    Example from API response:
        {
            "tasks": [
                {"title": "Buy milk", "done": false, ...},
                {"title": "Write report", "done": true, ...}
            ],
            "total_rows": 25
        }
    
    Usage:
        # Get preview after uploading CSV and configuring mappings
        preview = PreviewResult.model_validate(api_response)
        
        print(f"Importing {preview.total_rows} tasks:")
        for task in preview.tasks:
            status = "✓" if task.done else "○"
            print(f"  {status} {task.title}")
    """
    
    # Preview Data (2 fields)
    tasks: Optional[List[PreviewTask]] = Field(
        None, 
        description="List of parsed tasks from CSV rows"
    )
    total_rows: Optional[int] = Field(None, ge=0, description="Total number of rows in CSV")


# ============================================================================
# Migration Status Model
# ============================================================================

class MigrationStatus(VikunjaBaseModel):
    """
    Status of an ongoing migration from external service.
    
    API endpoint: GET /migration/status
    
    Tracks the progress of a migration job (Microsoft Todo, Todoist, Trello).
    
    Fields from API spec (migration.Status):
        - id: Unique migration job identifier
        - migrator_name: Name of the migration source (e.g., "todoist")
        - started_at: When migration began
        - finished_at: When migration completed (null if still running)
    
    Example from API response:
        {
            "id": 42,
            "migrator_name": "todoist",
            "started_at": "2024-01-15T10:30:00Z",
            "finished_at": "2024-01-15T10:32:15Z"
        }
    
    Usage:
        # Check migration status
        status = MigrationStatus.model_validate(api_response)
        
        if status.finished_at:
            print(f"Migration completed at {status.finished_at}")
        else:
            print(f"Migration in progress since {status.started_at}")
    """
    
    # Core Identification (2 fields)
    id: Optional[int] = Field(None, description="Unique migration job ID")
    migrator_name: Optional[str] = Field(
        None, 
        description="Name of migration source (e.g., 'todoist', 'microsofttodo', 'trello')"
    )
    
    # Timing (2 fields)
    started_at: Optional[datetime] = Field(None, description="Migration start timestamp")
    finished_at: Optional[datetime] = Field(None, description="Migration completion timestamp")


# ============================================================================
# External Service Migration Models
# ============================================================================

class MicrosoftTodoMigrationRequest(VikunjaBaseModel):
    """
    Request body for Microsoft Todo migration.
    
    API endpoint: POST /migration/microsofttodo
    
    Required fields: code (OAuth authorization code)
    
    UNKNOWN: Full request structure requires API testing - only 'code' field confirmed
    
    Example:
        req = MicrosoftTodoMigrationRequest(code="auth_code_from_oauth")
    """
    # Confirmed field from API spec
    code: Optional[str] = Field(None, description="OAuth authorization code from Microsoft Todo")


class TodoistMigrationRequest(VikunjaBaseModel):
    """
    Request body for Todoist migration.
    
    API endpoint: POST /migration/todoist
    
    Required fields: code (OAuth authorization code)
    
    UNKNOWN: Full request structure requires API testing - only 'code' field confirmed
    
    Example:
        req = TodoistMigrationRequest(code="auth_code_from_oauth")
    """
    # Confirmed field from API spec
    code: Optional[str] = Field(None, description="OAuth authorization code from Todoist")


class TrelloMigrationRequest(VikunjaBaseModel):
    """
    Request body for Trello migration.
    
    API endpoint: POST /migration/trello
    
    Required fields: code (OAuth authorization code)
    
    UNKNOWN: Full request structure requires API testing - only 'code' field confirmed
    
    Example:
        req = TrelloMigrationRequest(code="auth_code_from_oauth")
    """
    # Confirmed field from API spec
    code: Optional[str] = Field(None, description="OAuth authorization code from Trello")


# ============================================================================
# Response Models
# ============================================================================

class CSVImportResponse(VikunjaBaseModel):
    """Response for CSV import operations."""
    success: bool = Field(True, description="Request succeeded")
    imported_tasks: Optional[int] = Field(None, description="Number of tasks imported")
    error: Optional[str] = Field(None, description="Error message if failed")


class MigrationResponse(VikunjaBaseModel):
    """Response for migration initiation."""
    success: bool = Field(True, description="Request succeeded")
    migration_id: Optional[int] = Field(None, description="Migration job ID")
    error: Optional[str] = Field(None, description="Error message if failed")


class MigrationStatusResponse(VikunjaBaseModel):
    """Response for migration status check."""
    success: bool = Field(True, description="Request succeeded")
    status: Optional[MigrationStatus] = Field(None, description="Migration status")
    error: Optional[str] = Field(None, description="Error message if failed")
