# Vikunja MCP Skill

This skill enables an AI agent to interact with the Vikunja task management system via the Model Context Protocol (MCP).

## Core Concepts

- **Tasks**: Individual units of work.
- **Projects**: Collections of tasks.
- **Relationships**: Linking tasks together (e.g., subtasks, dependencies).
- **Comments**: Discussion threads attached to tasks.
- **Labels**: Tags for cross-project categorization.

## Operational Procedures

### Finding Information
1. **Search First**: Use `search_tasks(query="...")` to find tasks by title across the entire system.
2. **Context Discovery**: Use `list_projects()` to understand the available buckets of work.
3. **Task Listing**: Use `list_tasks()` for paginated, detailed retrieval. 
   - **Hierarchy**: Always use `expand=["subtasks"]` to see parent-child relationships.
   - **Details**: Use `expand=["subtasks", "comments"]` to see all dates, sub-items, and comments in one call. (Note: Labels are included automatically, do not add them to expand).
   - **Efficiency**: Use `per_page=50` to minimize round-trips for large projects.
4. **Deep Dive**: Use `list_task_comments(task_id=...)` to understand the history and rationale behind a task.

### Task Management
- **Creation**: Use `create_task(title=..., project_id=...)`.
- **Labels**: Use `create_label(title=..., hex_color="#RRGGBB")` to create new tags.
- **Bulk Setup**: Use `setup_new_project(title=..., tasks=[...])` to initialize a project with multiple tasks in one turn.
- **Updates**: Use `update_task(task_id=..., title=...)` to change the title.
- **Completion**: Use `complete_task(task_id=...)` to mark as done, or `mark_task_incomplete(task_id=...)` to undo.

### Hierarchies & Relationships
- **Subtasks**: Use `add_subtask(parent_task_id=..., subtask_task_id=...)`.
- **Dependencies**: Use `add_task_link(task_id=..., other_task_id=..., link_type="blocked")`.

## Data Formats
- **Dates**: Always use `parse_date(date_string=...)` to convert natural language (e.g., "tomorrow at 5pm") into the required ISO 8601 format.
- **IDs**: All operations require integer IDs retrieved from `list` or `search` tools.
