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

from vikunja_python.core.client import VikunjaClient
from vikunja_python.core.models.task import Task
from vikunja_python.core.models.project import Project

load_dotenv()

app = typer.Typer(help="Vikunja CLI - Manage your tasks from the terminal")
console = Console()

def get_client():
    base_url = os.getenv("VIKUNJA_URL")
    token = os.getenv("VIKUNJA_API_TOKEN")
    if not base_url or not token:
        rprint("[bold red]Error:[/bold red] VIKUNJA_URL and VIKUNJA_API_TOKEN must be set in .env")
        raise typer.Exit(1)
    return VikunjaClient(base_url, token)

@app.command()
def list_tasks(
    project_id: Optional[int] = typer.Option(None, "--project-id", "-p", help="Project ID to list tasks from"),
    page: int = typer.Option(1, help="Page number"),
    per_page: int = typer.Option(20, help="Items per page"),
    filter: Optional[str] = typer.Option(None, help="Vikunja filter string"),
    expand: Optional[List[str]] = typer.Option(
        None, 
        help=(
            "Fields to expand: 'subtasks', 'comments', 'reactions', 'buckets', 'comment_count', 'is_unread'. "
            "Note: list-tasks returns descriptions and assignees by default."
        )
    )
):
    """List tasks with rich formatting."""
    async def _list():
        async with get_client() as client:
            params = {"page": page, "per_page": per_page}
            if filter: params["filter"] = filter
            if expand: params["expand"] = expand
            
            path = "/tasks" if project_id is None else f"/projects/{project_id}/tasks"
            data = await client.request("GET", path, params=params)
            
            if isinstance(data, dict) and "error" in data:
                rprint(f"[bold red]Error:[/bold red] {data['error']}")
                return

            table = Table(title="Vikunja Tasks")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Status", width=6)
            table.add_column("Title", style="magenta")
            table.add_column("Assignees", style="green")
            table.add_column("Due Date", style="yellow")
            table.add_column("Labels", style="blue")

            tasks = [Task(**item) for item in data]
            for t in tasks:
                status = "[green]DONE[/green]" if t.done else "[yellow]TODO[/yellow]"
                due = t.due_date.strftime("%Y-%m-%d %H:%M") if t.due_date else ""
                labels = ", ".join(l.title for l in t.labels) if t.labels else ""
                assignees = ", ".join(u.username for u in t.assignees) if t.assignees else ""
                
                table.add_row(str(t.id), status, t.title, assignees, due, labels)
                if t.description:
                    # Add description preview in a dimmed style
                    desc = t.description.split('\n')[0]
                    if len(desc) > 80: desc = desc[:77] + "..."
                    table.add_row("", "", f"[dim]  Desc: {desc}[/dim]", "", "", "")

            console.print(table)

    asyncio.run(_list())

@app.command()
def get_project(project_id: int):
    """Get project details and views."""
    async def _get():
        async with get_client() as client:
            data = await client.request("GET", f"/projects/{project_id}")
            if isinstance(data, dict) and "error" in data:
                rprint(f"[bold red]Error:[/bold red] {data['error']}")
                return
            
            p = Project(**data)
            rprint(Panel(f"[bold cyan]Project:[/bold cyan] {p.title} (ID: {p.id})\n[dim]{p.description or 'No description'}[/dim]"))
            
            if p.views:
                table = Table(title="Project Views")
                table.add_column("ID", style="cyan")
                table.add_column("Title", style="magenta")
                table.add_column("Kind", style="yellow")
                for v in p.views:
                    table.add_row(str(v.get('id')), v.get('title'), v.get('view_kind'))
                console.print(table)
    asyncio.run(_get())

@app.command()
def list_view_tasks(project_id: int, view_id: int):
    """List all tasks in a specific project view with full descriptions."""
    async def _list():
        async with get_client() as client:
            data = await client.request("GET", f"/projects/{project_id}/views/{view_id}/tasks")
            if isinstance(data, dict) and "error" in data:
                rprint(f"[bold red]Error:[/bold red] {data['error']}")
                return
            
            # Flatten buckets if needed
            all_tasks = []
            if isinstance(data, list) and len(data) > 0:
                if "tasks" in data[0]:
                    for bucket in data:
                        for t_item in bucket.get("tasks", []):
                            all_tasks.append(Task(**t_item))
                else:
                    all_tasks = [Task(**item) for item in data]
            
            for t in all_tasks:
                status = "[green]DONE[/green]" if t.done else "[yellow]TODO[/yellow]"
                rprint(f"[bold cyan]ID: {t.id}[/bold cyan] {status} [bold magenta]{t.title}[/bold magenta]")
                if t.assignees:
                    rprint(f"[dim]  Assignees: {', '.join(u.username for u in t.assignees)}[/dim]")
                if t.description:
                    rprint(Panel(t.description, subtitle="Description", border_style="dim"))
                rprint("-" * 20)
    asyncio.run(_list())

@app.command()
def get_task(task_id: int):
    """Get full details for a single task."""
    async def _get():
        async with get_client() as client:
            data = await client.request("GET", f"/tasks/{task_id}")
            if isinstance(data, dict) and "error" in data:
                rprint(f"[bold red]Error:[/bold red] {data['error']}")
                return
            
            t = Task(**data)
            status = "[bold green]DONE[/bold green]" if t.done else "[bold yellow]TODO[/bold yellow]"
            
            rprint(Panel(
                f"[bold cyan]ID:[/bold cyan] {t.id} {status}\n"
                f"[bold cyan]Title:[/bold cyan] {t.title}\n"
                f"[bold cyan]Project:[/bold cyan] {t.project_id}\n"
                f"[bold cyan]Due:[/bold cyan] {t.due_date or 'None'}\n"
                f"[bold cyan]Priority:[/bold cyan] {t.priority}\n"
                f"[bold cyan]Labels:[/bold cyan] {', '.join(l.title for l in t.labels) if t.labels else 'None'}\n"
                f"[bold cyan]Assignees:[/bold cyan] {', '.join(u.username for u in t.assignees) if t.assignees else 'None'}\n\n"
                f"[bold white]Description:[/bold white]\n{t.description or 'No description'}",
                title=f"Task {t.id}",
                border_style="blue"
            ))
    asyncio.run(_get())

@app.command()
def create_task(
    title: str, 
    project_id: int, 
    description: Optional[str] = typer.Option(None, help="Task description"),
    due_date: Optional[str] = typer.Option(None, help="Due date (natural language ok)")
):
    """Create a new task."""
    async def _create():
        async with get_client() as client:
            payload = {"title": title}
            if description: payload["description"] = description
            if due_date: payload["due_date"] = due_date
            
            data = await client.request("PUT", f"/projects/{project_id}/tasks", json=payload)
            if isinstance(data, dict) and "error" in data:
                rprint(f"[bold red]Error:[/bold red] {data['error']}")
            else:
                rprint(f"[bold green]Task created![/bold green] ID: {data['id']}")

    asyncio.run(_create())

@app.command()
def create_label(title: str, hex_color: Optional[str] = typer.Option(None, help="Label color")):
    """Create a new label."""
    async def _create():
        async with get_client() as client:
            payload = {"title": title}
            if hex_color: payload["hex_color"] = hex_color
            data = await client.request("PUT", "/labels", json=payload)
            if isinstance(data, dict) and "error" in data:
                rprint(f"[bold red]Error:[/bold red] {data['error']}")
            else:
                rprint(f"[bold green]Label created![/bold green] ID: {data['id']} - {data['title']}")

    asyncio.run(_create())

if __name__ == "__main__":
    app()
