import asyncio
import os
from typing import Optional, List
import typer
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from dotenv import load_dotenv

from vikunja_python.core.client import VikunjaClient, setup_logging
from vikunja_python.core.models.task import Task
from vikunja_python.core.models.project import Project

# Load .env if present
load_dotenv()

app = typer.Typer(help="Vikunja CLI - Manage your tasks and projects with ease.")
console = Console()

def get_client() -> VikunjaClient:
    base_url = os.getenv("VIKUNJA_URL")
    token = os.getenv("VIKUNJA_API_TOKEN") or os.getenv("VIKUNJA_JWT_TOKEN")
    
    if not base_url or not token:
        rprint("[bold red]Error:[/bold red] VIKUNJA_URL and VIKUNJA_API_TOKEN (or VIKUNJA_JWT_TOKEN) must be set in environment or .env file.")
        raise typer.Exit(code=1)
    
    return VikunjaClient(base_url, token)

@app.command()
def list_tasks(
    project_id: Optional[int] = typer.Option(None, help="Filter by project ID"),
    page: int = typer.Option(1, help="Page number"),
    per_page: int = typer.Option(20, help="Items per page"),
    filter: Optional[str] = typer.Option(None, help="Vikunja filter string"),
    expand: Optional[List[str]] = typer.Option(None, help="Valid options ONLY: subtasks, buckets, reactions, comments, comment_count, is_unread, attachments, reminders")
):
    """List all tasks with pagination and optional filtering."""
    async def _list():
        async with get_client() as client:
            params = {
                "page": page,
                "per_page": per_page,
            }
            if filter:
                params["filter"] = filter
            if expand:
                params["expand"] = expand

            path = "/tasks" if project_id is None else f"/projects/{project_id}/tasks"
            data = await client.request("GET", path, params=params)
            
            if isinstance(data, dict) and "error" in data:
                rprint(f"[bold red]API Error:[/bold red] {data['error']}")
                return

            if not data:
                rprint("No tasks found.")
                return

            table = Table(title="Vikunja Tasks")
            table.add_column("ID", justify="right", style="cyan", no_wrap=True)
            table.add_column("Title", style="magenta")
            table.add_column("Done", justify="center")
            table.add_column("Due", style="green")
            table.add_column("Labels", style="blue")

            for item in data:
                task = Task(**item)
                done_str = "✅" if task.done else "❌"
                due_str = task.due_date.strftime("%Y-%m-%d %H:%M") if task.due_date else "-"
                labels_str = ", ".join(l.title for l in task.labels) if task.labels else "-"
                table.add_row(str(task.id), task.title, done_str, due_str, labels_str)

            console.print(table)

    asyncio.run(_list())

@app.command()
def list_projects():
    """List all projects."""
    async def _list():
        async with get_client() as client:
            data = await client.request("GET", "/projects")
            
            if isinstance(data, dict) and "error" in data:
                rprint(f"[bold red]API Error:[/bold red] {data['error']}")
                return

            table = Table(title="Vikunja Projects")
            table.add_column("ID", justify="right", style="cyan")
            table.add_column("Title", style="magenta")
            table.add_column("Owner", style="green")

            for item in data:
                project = Project(**item)
                owner_name = project.owner.username if project.owner else "Unknown"
                table.add_row(str(project.id), project.title, owner_name)

            console.print(table)

    asyncio.run(_list())

@app.command()
def create_task(
    title: str, 
    project_id: int,
    description: Optional[str] = typer.Option(None, help="Markdown description"),
    due_date: Optional[str] = typer.Option(None, help="Due date (e.g., 'tomorrow')"),
    priority: Optional[int] = typer.Option(None, help="Priority 1-5"),
    labels: Optional[List[int]] = typer.Option(None, help="Label IDs to attach"),
    recurrence_freq: Optional[str] = typer.Option(None, help="daily, weekly, monthly, yearly"),
    recurrence_interval: int = typer.Option(1, help="Interval for recurrence")
):
    """Create a new task in a project."""
    import dateparser
    async def _create():
        async with get_client() as client:
            payload = {"title": title}
            if description is not None: payload["description"] = description
            if priority is not None: payload["priority"] = priority
            if labels: payload["label_ids"] = labels
            if due_date is not None:
                dt = dateparser.parse(due_date)
                if dt: payload["due_date"] = dt.isoformat()

            if recurrence_freq:
                freq = recurrence_freq.lower()
                multiplier = 0
                if freq == "daily": multiplier = 86400
                elif freq == "weekly": multiplier = 604800
                elif freq == "monthly": multiplier = 2592000
                elif freq == "yearly": multiplier = 31536000
                
                if multiplier > 0:
                    payload["repeat_after"] = multiplier * recurrence_interval
                    payload["repeat_mode"] = 0

            data = await client.request("PUT", f"/projects/{project_id}/tasks", json=payload)
            
            if isinstance(data, dict) and "error" in data:
                rprint(f"[bold red]Error creating task:[/bold red] {data['error']}")
                return

            task = Task(**data)
            rprint(f"[bold green]Task created![/bold green] ID: {task.id} - {task.title}")

    asyncio.run(_create())

@app.command()
def login(username: str = typer.Option(..., prompt=True), password: str = typer.Option(..., prompt=True, hide_input=True)):
    """Login with username/password to get a JWT token (for Buckets/Reactions)."""
    async def _login():
        base_url = os.getenv("VIKUNJA_URL")
        if not base_url:
            rprint("[bold red]Error:[/bold red] VIKUNJA_URL must be set.")
            return
            
        async with httpx.AsyncClient(base_url=base_url.rstrip("/")) as client:
            resp = await client.post("/login", json={"username": username, "password": password})
            if resp.status_code == 200:
                token = resp.json().get("token")
                rprint("[bold green]Login successful![/bold green]")
                rprint(f"Set this as [bold]VIKUNJA_JWT_TOKEN[/bold] in your environment or .env file.")
                rprint(f"JWT: [dim]{token}[/dim]")
            else:
                rprint(f"[bold red]Login failed:[/bold red] {resp.text}")

    asyncio.run(_login())

@app.command()
def delete_task(task_id: int):
    """Delete a task."""
    async def _delete():
        async with get_client() as client:
            data = await client.request("DELETE", f"/tasks/{task_id}")
            if isinstance(data, dict) and "error" in data:
                rprint(f"[bold red]Error:[/bold red] {data['error']}")
            else:
                rprint(f"[bold green]Task {task_id} deleted.[/bold green]")
    asyncio.run(_delete())

@app.command()
def update_task(
    task_id: int, 
    title: Optional[str] = typer.Option(None, help="New title"),
    description: Optional[str] = typer.Option(None, help="New description"),
    due_date: Optional[str] = typer.Option(None, help="New due date"),
    priority: Optional[int] = typer.Option(None, help="New priority 1-5"),
    labels: Optional[List[int]] = typer.Option(None, help="New label IDs"),
    recurrence_freq: Optional[str] = typer.Option(None, help="daily, weekly, monthly, yearly"),
    recurrence_interval: int = typer.Option(1, help="Interval for recurrence")
):
    """Update a task's fields. Use complete-task or mark-task-incomplete for status changes."""
    import dateparser
    async def _update():
        async with get_client() as client:
            payload = {}
            if title is not None: payload["title"] = title
            if description is not None: payload["description"] = description
            if priority is not None: payload["priority"] = priority
            if labels is not None: payload["label_ids"] = labels
            if due_date is not None:
                dt = dateparser.parse(due_date)
                if dt: payload["due_date"] = dt.isoformat()

            if recurrence_freq:
                freq = recurrence_freq.lower()
                multiplier = 0
                if freq == "daily": multiplier = 86400
                elif freq == "weekly": multiplier = 604800
                elif freq == "monthly": multiplier = 2592000
                elif freq == "yearly": multiplier = 31536000
                
                if multiplier > 0:
                    payload["repeat_after"] = multiplier * recurrence_interval
                    payload["repeat_mode"] = 0

            if not payload:
                rprint("[bold yellow]No changes provided.[/bold yellow] Provide a field to update.")
                return

            data = await client.request("POST", f"/tasks/{task_id}", json=payload)
            if isinstance(data, dict) and "error" in data:
                rprint(f"[bold red]Error:[/bold red] {data['error']}")
            else:
                rprint(f"[bold green]Task {task_id} updated.[/bold green]")
    asyncio.run(_update())

@app.command()
def complete_task(task_id: int):
    """Mark a task as completed."""
    async def _complete():
        async with get_client() as client:
            data = await client.request("POST", f"/tasks/{task_id}", json={"done": True})
            if isinstance(data, dict) and "error" in data:
                rprint(f"[bold red]Error:[/bold red] {data['error']}")
            else:
                rprint(f"[bold green]Task {task_id} marked as completed.[/bold green]")
    asyncio.run(_complete())

@app.command()
def mark_task_incomplete(task_id: int):
    """Mark a task as incomplete."""
    async def _incomplete():
        async with get_client() as client:
            data = await client.request("POST", f"/tasks/{task_id}", json={"done": False})
            if isinstance(data, dict) and "error" in data:
                rprint(f"[bold red]Error:[/bold red] {data['error']}")
            else:
                rprint(f"[bold green]Task {task_id} marked as incomplete.[/bold green]")
    asyncio.run(_incomplete())
@app.command()
def list_buckets(project_id: int):
    """List buckets for a project (Requires JWT)."""
    async def _list():
        async with get_client() as client:
            # 1. Get views
            views = await client.request("GET", f"/projects/{project_id}/views")
            if not views or "error" in views:
                rprint("[bold red]Error fetching views.[/bold red]")
                return
            
            view_id = views[0]["id"]
            # 2. Get buckets
            data = await client.request("GET", f"/projects/{project_id}/views/{view_id}/buckets")
            
            if isinstance(data, dict) and "error" in data:
                rprint(f"[bold red]API Error:[/bold red] {data['error']}")
                return

            table = Table(title=f"Buckets for Project {project_id}")
            table.add_column("ID", justify="right", style="cyan")
            table.add_column("Title", style="magenta")
            table.add_column("Position", justify="right")

            for item in data:
                table.add_row(str(item["id"]), item["title"], str(item["position"]))

            console.print(table)
    asyncio.run(_list())

@app.command()
def react(task_id: int, emoji: str):
    """Add a reaction to a task (Requires JWT)."""
    async def _react():
        async with get_client() as client:
            data = await client.request("PUT", f"/tasks/{task_id}/reactions", json={"value": emoji})
            if isinstance(data, dict) and "error" in data:
                rprint(f"[bold red]Error:[/bold red] {data['error']}")
            else:
                rprint(f"[bold green]Reacted with {emoji} to task {task_id}[/bold green]")
    asyncio.run(_react())

@app.command()
def list_labels():
    """List all available labels."""
    async def _list():
        async with get_client() as client:
            data = await client.request("GET", "/labels")
            
            if isinstance(data, dict) and "error" in data:
                rprint(f"[bold red]API Error:[/bold red] {data['error']}")
                return

            table = Table(title="Vikunja Labels")
            table.add_column("ID", justify="right", style="cyan")
            table.add_column("Title", style="magenta")
            table.add_column("Color", style="green")
            table.add_column("Description", style="blue")

            for item in data:
                from vikunja_python.core.models.base import Label
                label = Label(**item)
                table.add_row(str(label.id), label.title, f"#{label.hex_color}", label.description or "-")

            console.print(table)

    asyncio.run(_list())

@app.command()
def create_label(
    title: str, 
    hex_color: Optional[str] = typer.Option(None, help="Hex color code (e.g. #ff0000)"),
    description: Optional[str] = typer.Option(None, help="Label description")
):
    """Create a new label."""
    async def _create():
        async with get_client() as client:
            payload = {"title": title}
            if hex_color: payload["hex_color"] = hex_color
            if description: payload["description"] = description
            
            data = await client.request("PUT", "/labels", json=payload)
            if isinstance(data, dict) and "error" in data:
                rprint(f"[bold red]Error:[/bold red] {data['error']}")
            else:
                rprint(f"[bold green]Label created![/bold green] ID: {data['id']} - {data['title']}")

    asyncio.run(_create())

if __name__ == "__main__":
    app()

