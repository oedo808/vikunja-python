import os
import logging
from typing import Optional, List, Annotated
from pydantic import Field
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import dateparser

from vikunja_python.core.client import VikunjaClient, setup_logging
from vikunja_python.core.models.task import Task
from vikunja_python.core.models.project import Project
from vikunja_python.core.models.label import Label

# Load .env if present
load_dotenv()

# Setup logging correctly for MCP
setup_logging(is_mcp=True)
debug_mode = os.getenv("VIKUNJA_DEBUG", "").lower() in ("1", "true", "yes", "on")

# Initialize FastMCP server
# Flat naming for small models: create_task, list_projects, etc.
mcp = FastMCP("Vikunja", debug=debug_mode, log_level="DEBUG" if debug_mode else "INFO")

def get_client() -> VikunjaClient:
    """Helper to initialize client from environment."""
    base_url = os.getenv("VIKUNJA_URL")
    # MCP prioritized for API Key usage
    token = os.getenv("VIKUNJA_API_TOKEN")
    
    if not base_url or not token:
        logging.error("VIKUNJA_URL and VIKUNJA_API_TOKEN must be set.")
        raise RuntimeError("VIKUNJA_URL and VIKUNJA_API_TOKEN must be set for MCP server.")
    
    logging.debug(f"Initializing client for {base_url}")
    return VikunjaClient(base_url, token)

@mcp.tool()
async def list_tasks(
    project_id: Annotated[Optional[int], Field(description="Optional ID of the project to list tasks from")] = None,
    include_descriptions: Annotated[bool, Field(description="Include full task descriptions. Set to False for bulk operations to save tokens.")] = True,
    page: Annotated[int, Field(description="Page number for pagination (default: 1)")] = 1,
    per_page: Annotated[int, Field(description="Number of tasks per page (default: 20)")] = 20,
    filter: Annotated[Optional[str], Field(description="Vikunja filter string (e.g., 'done = false')")] = None,
    expand: Annotated[Optional[List[str]], Field(description=(
        "Fields to expand in the response. "
        "Valid: subtasks, comments, reactions, buckets, comment_count, is_unread. "
        "Note: attachments and reminders are often better fetched via get_task() or project view listing."
    ))] = None,
    sort_by: Annotated[Optional[List[str]], Field(description="List of fields to sort by (e.g., ['due_date', 'priority'])")] = None,
    order_by: Annotated[Optional[str], Field(description="Sort order, 'asc' or 'desc' (default: 'asc')")] = None,
) -> str:
    """List tasks from Vikunja with pagination."""
    async with get_client() as client:
        params = {
            "page": page,
            "per_page": per_page,
        }
        if filter:
            # Strip extra quotes if provided by the model/MCP (Fixes 400 Bad Request)
            params["filter"] = filter.strip('"\'')
        if expand:
            # Filter out invalid expand fields for this endpoint to avoid 412 errors
            valid_expands = {"subtasks", "buckets", "reactions", "comments", "comment_count", "is_unread"}
            valid_requested = [e for e in expand if e in valid_expands]
            if valid_requested:
                params["expand"] = valid_requested
        if sort_by:
            params["sort_by"] = sort_by
        if order_by:
            params["order_by"] = order_by

        path = "/tasks" if project_id is None else f"/projects/{project_id}/tasks"
        data = await client.request("GET", path, params=params)
        
        if isinstance(data, dict) and "error" in data:
            return f"Error fetching tasks: {data['error']}"
        
        if not data:
            return "No tasks found."

        tasks = [Task(**item) for item in data]
        result = []

        def format_task(t: Task, indent: int = 0) -> str:
            prefix = "  " * indent
            status = "[DONE]" if t.done else "[TODO]"
            due = f" (Due: {t.due_date.strftime('%Y-%m-%d %H:%M')})" if t.due_date else ""
            
            labels_list = t.labels or []
            labels_str = f" [Labels: {', '.join(l.title for l in labels_list)}]" if labels_list else ""
            
            assignees_str = f" [Assignees: {', '.join(u.username for u in t.assignees)}]" if t.assignees else ""
            
            priority = f" [P{t.priority}]" if t.priority > 0 else ""
            
            # Expanded info
            extra = []
            if t.comment_count is not None: extra.append(f"{t.comment_count} comments")
            if t.reactions: 
                extra.append(f"{len(t.reactions)} reactions")
            if t.buckets:
                extra.append(f"Buckets: {', '.join(b.get('title', 'Unknown') if isinstance(b, dict) else str(b) for b in t.buckets)}")
            
            extra_str = f" ({', '.join(extra)})" if extra else ""
            
            line = f"{prefix}ID: {t.id} {status} {t.title}{priority}{due}{labels_str}{assignees_str}{extra_str}"
            if include_descriptions and t.description:
                # Include full description with indentation
                desc_indented = t.description.replace('\n', f'\n{prefix}  ')
                line += f"\n{prefix}  Desc: {desc_indented}"

            lines = [line]
            
            subtasks_list = t.subtasks or []
            if subtasks_list:
                for st in subtasks_list:
                    lines.append(format_task(st, indent + 1))
            
            # Links/Relations
            related = t.related_tasks or {}
            if related:
                for rel_type, rel_tasks in related.items():
                    if rel_type == "subtask": continue # Already handled by expand=subtasks
                    if not rel_tasks: continue
                    for rt_data in rel_tasks:
                        # rt_data is likely a dict or ID depending on expansion
                        rt_id = rt_data.get("id") if isinstance(rt_data, dict) else rt_data
                        lines.append(f"{prefix}  -> {rel_type.capitalize()}: {rt_id}")

            return "\n".join(lines)

        for t in tasks:
            result.append(format_task(t))
        
        return "\n".join(result)

@mcp.tool()
async def get_project(project_id: Annotated[int, Field(description="The ID of the project to fetch")]) -> str:
    """Get detailed information about a project, including its views."""
    async with get_client() as client:
        data = await client.request("GET", f"/projects/{project_id}")
        if isinstance(data, dict) and "error" in data:
            return f"Error fetching project: {data['error']}"
        
        p = Project(**data)
        lines = [f"ID: {p.id} - Title: {p.title}"]
        if p.description: lines.append(f"Description: {p.description}")
        
        if p.views:
            lines.append("\nViews:")
            for v in p.views:
                # v is a ProjectView model object
                lines.append(f"  - {v.title} (ID: {v.id}, Kind: {v.view_kind})")
        
        return "\n".join(lines)

@mcp.tool()
async def list_project_view_tasks(
    project_id: Annotated[int, Field(description="ID of the project")],
    view_id: Annotated[int, Field(description="ID of the view")],
    include_descriptions: Annotated[bool, Field(description="Include full task descriptions. Set to False for bulk operations to save tokens.")] = True,
    page: Annotated[int, Field(description="Page number (default: 1)")] = 1,
    per_page: Annotated[int, Field(description="Tasks per page (default: 50)")] = 50,
    expand: Annotated[Optional[List[str]], Field(description=(
        "Fields to expand. Valid: subtasks, comments, reactions, buckets, comment_count, is_unread. "
        "This endpoint often returns more metadata (like descriptions) by default."
    ))] = None
) -> str:
    """List tasks for a specific project view."""
    async with get_client() as client:
        params = {"page": page, "per_page": per_page}
        if expand:
            params["expand"] = expand
            
        data = await client.request("GET", f"/projects/{project_id}/views/{view_id}/tasks", params=params)
        
        if isinstance(data, dict) and "error" in data:
            return f"Error fetching view tasks: {data['error']}"
        
        if not data:
            return "No tasks found in this view."

        all_tasks = []
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            if "tasks" in first_item and "id" in first_item and "title" in first_item:
                # It's a list of buckets (Kanban view)
                for bucket in data:
                    b_tasks = bucket.get("tasks") or []
                    for t_item in b_tasks:
                        # Inject bucket title for context
                        t_item["_bucket_title"] = bucket.get("title")
                        all_tasks.append(Task(**t_item))
            else:
                # It's a list of tasks
                all_tasks = [Task(**item) for item in data]

        if not all_tasks:
            return "No tasks found in this view."

        result = []
        def format_task_rich(t: Task) -> str:
            status = "[DONE]" if t.done else "[TODO]"
            due = f" (Due: {t.due_date.strftime('%Y-%m-%d %H:%M')})" if t.due_date else ""
            labels = f" [Labels: {', '.join(l.title for l in t.labels)}]" if t.labels else ""
            assignees = f" [Assignees: {', '.join(u.username for u in t.assignees)}]" if t.assignees else ""
            
            # Check for injected bucket title in model_extra
            bucket_title = t.model_extra.get("_bucket_title") if t.model_extra else None
            bucket = f" [Bucket: {bucket_title}]" if bucket_title else ""
            
            line = f"ID: {t.id} {status} {t.title}{due}{labels}{assignees}{bucket}"
            if include_descriptions and t.description:
                desc_indented = t.description.replace('\n', '\n  ')
                line += f"\n  Desc: {desc_indented}"
            return line

        for t in all_tasks:
            result.append(format_task_rich(t))
            
        return "\n\n".join(result)

@mcp.tool()
async def get_task(
    task_id: Annotated[int, Field(description="The ID of the task to fetch")],
    expand: Annotated[Optional[List[str]], Field(description=(
        "Fields to expand for full details. Valid: subtasks, comments, attachments, reminders, assignees, reactions, buckets. "
        "Use this for a deep-dive into a single task."
    ))] = None
) -> str:
    """Get the full details of a specific task, including its description, recurrence, and all metadata."""
    async with get_client() as client:
        # 1. Try with expansion
        params = {}
        if expand:
            params["expand"] = expand
            
        data = await client.request("GET", f"/tasks/{task_id}", params=params)
        
        # 2. Fallback if 412 (Precondition Failed) - Some servers don't support certain expansions
        if isinstance(data, dict) and "error" in data and "412" in str(data["error"]):
            logging.warning(f"Task expansion failed with 412 for task {task_id}, falling back to manual fetch.")
            data = await client.request("GET", f"/tasks/{task_id}")
            if isinstance(data, dict) and "error" in data:
                return f"Error fetching task: {data['error']}"
            
            # If expansion was requested, try manual fetch for known sub-resources
            if expand:
                if "assignees" in expand:
                    assignees = await client.request("GET", f"/tasks/{task_id}/assignees")
                    if isinstance(assignees, list): data["assignees"] = assignees
                if "attachments" in expand:
                    attachments = await client.request("GET", f"/tasks/{task_id}/attachments")
                    if isinstance(attachments, list): data["attachments"] = attachments
                if "comments" in expand:
                    comments = await client.request("GET", f"/tasks/{task_id}/comments")
                    if isinstance(comments, list): data["comments"] = comments

        if isinstance(data, dict) and "error" in data:
            return f"Error fetching task: {data['error']}"
        
        t = Task(**data)
        
        lines = []
        status = "[DONE]" if t.done else "[TODO]"
        lines.append(f"ID: {t.id} {status} {t.title}")
        lines.append(f"Project ID: {t.project_id}")
        lines.append(f"Identifier: {t.identifier}")
        if t.due_date: lines.append(f"Due: {t.due_date.isoformat()}")
        if t.priority > 0: lines.append(f"Priority: {t.priority}")
        
        if t.labels: 
            lines.append(f"Labels: {', '.join(l.title for l in t.labels)}")
            
        if t.assignees:
            lines.append(f"Assignees: {', '.join(u.username for u in t.assignees)}")
        
        if t.reactions:
            lines.append(f"Reactions: {len(t.reactions)} total")

        # Recurrence
        if t.repeat_after > 0:
            lines.append(f"Recurrence: repeats after {t.repeat_after} seconds (Mode: {t.repeat_mode})")
            
        if t.description:
            lines.append("\n--- Description ---")
            lines.append(t.description)
            lines.append("-------------------")
            
        # Attachments/Reminders summaries
        if t.attachments:
            lines.append(f"\nAttachments ({len(t.attachments)}):")
            for att in t.attachments:
                name = "Unknown"
                if isinstance(att, dict):
                    name = att.get("file", {}).get("name") or att.get("name") or "Unnamed"
                lines.append(f"  - {name} (ID: {att.get('id') if isinstance(att, dict) else '?'})")
        
        if t.reminders:
            lines.append(f"\nReminders ({len(t.reminders)}):")
            for rem in t.reminders:
                if isinstance(rem, dict):
                    rem_time = rem.get("reminder") or f"Relative to {rem.get('relative_to')} ({rem.get('relative_period')}s)"
                    lines.append(f"  - {rem_time}")

        return "\n".join(lines)

@mcp.tool()
async def create_task(
    title: Annotated[str, Field(description="Task title")],
    project_id: Annotated[int, Field(description="ID of the project")],
    description: Annotated[Optional[str], Field(description="Optional markdown description")] = None,
    due_date: Annotated[Optional[str], Field(description="Natural language or ISO date string (e.g., 'tomorrow')")] = None,
    priority: Annotated[Optional[int], Field(description="Integer 1-5 (5 is highest)")] = None,
    labels: Annotated[Optional[List[int]], Field(description="List of label IDs to attach")] = None,
    recurrence: Annotated[Optional[dict], Field(description='Optional dict with {"frequency": "daily|weekly|monthly|yearly", "interval": int}')] = None
) -> str:
    """Create a new task in a specific project."""
    async with get_client() as client:
        payload = {"title": title}
        if description is not None: payload["description"] = description
        if priority is not None: payload["priority"] = priority
        if labels is not None: payload["label_ids"] = labels
        if due_date is not None:
            dt = dateparser.parse(due_date)
            if dt:
                payload["due_date"] = dt.isoformat()

        if recurrence:
            freq = recurrence.get("frequency", "").lower()
            interval = recurrence.get("interval", 1)
            # Rough mapping to seconds for Vikunja repeat_after
            multiplier = 0
            if freq == "daily": multiplier = 86400
            elif freq == "weekly": multiplier = 604800
            elif freq == "monthly": multiplier = 2592000 # 30 days
            elif freq == "yearly": multiplier = 31536000 # 365 days
            
            if multiplier > 0:
                payload["repeat_after"] = multiplier * interval
                payload["repeat_mode"] = 0 # 0/1 usually means repeat after due date

        data = await client.request("PUT", f"/projects/{project_id}/tasks", json=payload)
        
        if isinstance(data, dict) and "error" in data:
            return f"Error creating task: {data['error']}"
            
        task = Task(**data)
        return f"Successfully created task '{task.title}' with ID {task.id} in project {project_id}."

@mcp.tool()
async def list_projects() -> str:
    """List all available projects."""
    async with get_client() as client:
        data = await client.request("GET", "/projects")
        
        if isinstance(data, dict) and "error" in data:
            return f"Error fetching projects: {data['error']}"
            
        projects = [Project(**item) for item in data]
        result = []
        for p in projects:
            result.append(f"ID: {p.id} - Title: {p.title}")
            
        return "\n".join(result) if result else "No projects found."

@mcp.tool()
async def list_labels() -> str:
    """List all available labels."""
    async with get_client() as client:
        data = await client.request("GET", "/labels")
        
        if isinstance(data, dict) and "error" in data:
            return f"Error fetching labels: {data['error']}"
            
        labels = [Label(**item) for item in data]
        result = []
        for l in labels:
            result.append(f"ID: {l.id} - Title: {l.title} (Color: {l.hex_color})")
            
        return "\n".join(result) if result else "No labels found."

@mcp.tool()
async def create_label(
    title: Annotated[str, Field(description="The name of the label")],
    hex_color: Annotated[Optional[str], Field(description="The color of the label in #RRGGBB format")] = None,
    description: Annotated[Optional[str], Field(description="A description for the label")] = None
) -> str:
    """Create a new label."""
    async with get_client() as client:
        payload = {"title": title}
        if hex_color:
            payload["hex_color"] = hex_color
        if description:
            payload["description"] = description
            
        data = await client.request("PUT", "/labels", json=payload)
        
        if isinstance(data, dict) and "error" in data:
            return f"Error creating label: {data['error']}"
            
        label = Label(**data)
        return f"Successfully created label '{label.title}' with ID {label.id}."

@mcp.tool()
async def update_task(
    task_id: Annotated[int, Field(description="The ID of the task to update")],
    title: Annotated[Optional[str], Field(description="New title for the task")] = None,
    description: Annotated[Optional[str], Field(description="New markdown description for the task")] = None,
    due_date: Annotated[Optional[str], Field(description="Natural language or ISO date string (e.g., 'tomorrow')")] = None,
    priority: Annotated[Optional[int], Field(description="Integer 1-5 (5 is highest)")] = None,
    labels: Annotated[Optional[List[int]], Field(description="List of label IDs to set (overwrites existing)")] = None,
    recurrence: Annotated[Optional[dict], Field(description='Optional dict with {"frequency": "daily|weekly|monthly|yearly", "interval": int}')] = None
) -> str:
    """Update a task's fields. To mark as done/incomplete, use complete_task or mark_task_incomplete."""
    async with get_client() as client:
        payload = {}
        if title is not None: payload["title"] = title
        if description is not None: payload["description"] = description
        if priority is not None: payload["priority"] = priority
        if labels is not None: payload["label_ids"] = labels
        if due_date is not None:
            dt = dateparser.parse(due_date)
            if dt:
                payload["due_date"] = dt.isoformat()

        if recurrence:
            freq = recurrence.get("frequency", "").lower()
            interval = recurrence.get("interval", 1)
            # Rough mapping to seconds for Vikunja repeat_after
            multiplier = 0
            if freq == "daily": multiplier = 86400
            elif freq == "weekly": multiplier = 604800
            elif freq == "monthly": multiplier = 2592000 # 30 days
            elif freq == "yearly": multiplier = 31536000 # 365 days
            
            if multiplier > 0:
                payload["repeat_after"] = multiplier * interval
                payload["repeat_mode"] = 0 # 0/1 usually means repeat after due date

        if not payload:
            return "No changes provided for update_task."

        data = await client.request("POST", f"/tasks/{task_id}", json=payload)
        if isinstance(data, dict) and "error" in data:
            return f"Error updating task: {data['error']}"
        return f"Successfully updated task {task_id}."

@mcp.tool()
async def complete_task(task_id: Annotated[int, Field(description="The ID of the task to mark as completed")]) -> str:
    """Mark a task as completed (done = true)."""
    async with get_client() as client:
        payload = {"done": True}
        data = await client.request("POST", f"/tasks/{task_id}", json=payload)
        if isinstance(data, dict) and "error" in data:
            return f"Error completing task: {data['error']}"
        return f"Task {task_id} marked as completed."

@mcp.tool()
async def mark_task_incomplete(task_id: Annotated[int, Field(description="The ID of the task to mark as incomplete")]) -> str:
    """Mark a task as incomplete (done = false)."""
    async with get_client() as client:
        payload = {"done": False}
        data = await client.request("POST", f"/tasks/{task_id}", json=payload)
        if isinstance(data, dict) and "error" in data:
            return f"Error marking task as incomplete: {data['error']}"
        return f"Task {task_id} marked as incomplete."

@mcp.tool()
async def delete_task(task_id: Annotated[int, Field(description="The ID of the task to delete")]) -> str:
    """Delete a task."""
    async with get_client() as client:
        data = await client.request("DELETE", f"/tasks/{task_id}")
        if isinstance(data, dict) and "error" in data:
            return f"Error deleting task: {data['error']}"
        return f"Successfully deleted task {task_id}."

@mcp.tool()
async def add_subtask(
    parent_task_id: Annotated[int, Field(description="The ID of the parent task")],
    subtask_task_id: Annotated[int, Field(description="The ID of the task that will become a subtask")]
) -> str:
    """Explicitly make one task a subtask of another."""
    async with get_client() as client:
        payload = {"other_task_id": subtask_task_id, "relation_kind": "subtask"}
        data = await client.request("PUT", f"/tasks/{parent_task_id}/relations", json=payload)
        if isinstance(data, dict) and "error" in data:
            return f"Error creating subtask: {data['error']}"
        return f"Task {subtask_task_id} is now a subtask of {parent_task_id}."

@mcp.tool()
async def add_task_link(
    task_id: Annotated[int, Field(description="The source task ID")],
    other_task_id: Annotated[int, Field(description="The target task ID")],
    link_type: Annotated[str, Field(description="Link type (related, duplicate, blocked, blocking, predecessor, successor)")] = "related"
) -> str:
    """Link two tasks together with a specific relationship type."""
    async with get_client() as client:
        payload = {"other_task_id": other_task_id, "relation_kind": link_type}
        data = await client.request("PUT", f"/tasks/{task_id}/relations", json=payload)
        if isinstance(data, dict) and "error" in data:
            return f"Error creating relationship: {data['error']}"
        return f"Successfully created {link_type} link between {task_id} and {other_task_id}."

@mcp.tool()
async def list_filters() -> str:
    """List all saved filters."""
    async with get_client() as client:
        data = await client.request("GET", "/filters")
        if isinstance(data, dict) and "error" in data:
            return f"Error fetching filters: {data['error']}"
        
        result = [f"ID: {f['id']} - Title: {f['title']}" for f in data]
        return "\n".join(result) if result else "No filters found."

@mcp.tool()
async def search_tasks(query: Annotated[str, Field(description="Search string to match task titles")]) -> str:
    """Search for tasks globally across all projects."""
    async with get_client() as client:
        # Strip extra quotes if provided (Consistency fix)
        clean_query = query.strip('"\'')
        data = await client.request("GET", "/tasks", params={"s": clean_query})
        
        if isinstance(data, dict) and "error" in data:
            return f"Error searching tasks: {data['error']}"
        
        tasks = [Task(**item) for item in data]
        result = []
        for t in tasks:
            status = "[DONE]" if t.done else "[TODO]"
            result.append(f"ID: {t.id} {status} {t.title} (Project ID: {t.project_id})")
        
        return "\n".join(result) if result else f"No tasks found matching '{query}'."

@mcp.tool()
async def add_task_comment(
    task_id: Annotated[int, Field(description="The ID of the task to comment on")],
    comment: Annotated[str, Field(description="The markdown comment text")]
) -> str:
    """Add a comment to a task."""
    async with get_client() as client:
        data = await client.request("PUT", f"/tasks/{task_id}/comments", json={"comment": comment})
        if isinstance(data, dict) and "error" in data:
            return f"Error adding comment: {data['error']}"
        return f"Successfully added comment to task {task_id}."

@mcp.tool()
async def list_task_comments(task_id: Annotated[int, Field(description="The ID of the task")]) -> str:
    """List all comments on a task."""
    async with get_client() as client:
        data = await client.request("GET", f"/tasks/{task_id}/comments")
        if isinstance(data, dict) and "error" in data:
            return f"Error fetching comments: {data['error']}"
        
        if not data:
            return "No comments found on this task."
            
        result = []
        for c in data:
            author = c.get("author", {}).get("username", "Unknown")
            result.append(f"[{c['created']}] {author}: {c['comment']}")
        
        return "\n".join(result)

@mcp.tool()
async def add_label_to_task(
    task_id: Annotated[int, Field(description="The ID of the task")],
    label_id: Annotated[int, Field(description="The ID of the label to add")]
) -> str:
    """Link an existing label to a task."""
    async with get_client() as client:
        data = await client.request("PUT", f"/tasks/{task_id}/labels", json={"label_id": label_id})
        if isinstance(data, dict) and "error" in data:
            return f"Error adding label: {data['error']}"
        return f"Successfully added label {label_id} to task {task_id}."

@mcp.tool()
async def setup_new_project(
    title: Annotated[str, Field(description="The title of the new project")],
    tasks: Annotated[List[str], Field(description="List of task titles to create in the project")]
) -> str:
    """Create a new project and multiple tasks in one operation."""
    async with get_client() as client:
        # 1. Create Project
        proj_data = await client.request("PUT", "/projects", json={"title": title})
        if isinstance(proj_data, dict) and "error" in proj_data:
            return f"Error creating project: {proj_data['error']}"
        
        project = Project(**proj_data)
        results = [f"Project '{project.title}' created with ID {project.id}."]
        
        # 2. Create Tasks
        for task_title in tasks:
            t_data = await client.request("PUT", f"/projects/{project.id}/tasks", json={"title": task_title})
            if isinstance(t_data, dict) and "error" in t_data:
                results.append(f"  - Error creating task '{task_title}': {t_data['error']}")
            else:
                results.append(f"  - Task '{task_title}' created with ID {t_data['id']}.")
        
        return "\n".join(results)

@mcp.tool()
async def parse_date(date_string: Annotated[str, Field(description="Natural language date (e.g., 'next Friday at 2pm')")]) -> str:
    """Convert natural language dates into ISO 8601 format."""
    dt = dateparser.parse(date_string)
    if not dt:
        return f"Could not parse date: '{date_string}'"
    return dt.isoformat()

def main():
    logging.info("Starting Vikunja MCP Server...")
    mcp.run()

if __name__ == "__main__":
    main()
