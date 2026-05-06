# Vikunja Python

An open-source (WTFPL) API wrapper, rich CLI tool, and Model Context Protocol (MCP) server for the [Vikunja](https://vikunja.io/) task management system.

Built for **Python 3.13** using `httpx`, `pydantic v2`, and `fastmcp`.

## 🏗 Architecture

The project is structured into three distinct layers to ensure modularity and clean dependency management:

- **`/core`**: The engine. Handles Pydantic models, HTTP client logic, and error handling. (Minimal dependencies).
- **`/cli`**: A high-visual-impact command-line interface built with `typer` and `rich`.
- **`/mcp`**: A Model Context Protocol server designed for agentic workflows, optimized for smaller LLMs (like Gemma).

## 🚀 Getting Started

### Installation
This project uses `uv` for modern Python package management.

```bash
uv sync --all-extras
```

### Environment Variables
Configure your Vikunja instance in a `.env` file or your shell:

```bash
VIKUNJA_URL="https://your-vikunja-instance.com/api/v1"
VIKUNJA_API_TOKEN="your_api_token_here"  # Recommended for MCP
VIKUNJA_JWT_TOKEN="your_jwt_here"        # Required for Buckets/Reactions in CLI
```

## 🛠 Features & Tooling

### CLI (`vikunja`)
The CLI provides a rich, human-friendly interface for managing your workspace.
- **Tasks & Projects**: Full CRUD support with formatted tables.
- **Buckets (Kanban)**: List and manage columns (Requires JWT).
- **Reactions**: Add emojis to tasks (Requires JWT).
- **Labels**: List and categorize tasks.
- **Auth**: Built-in `login` command to generate JWTs.

```bash
uv run vikunja list-tasks
uv run vikunja login
```

### MCP Server (`vikunja-mcp`)
A powerful server that gives LLMs "hands" to manage your Vikunja instance. Optimized for reliability and low turn-count.
- **Global Search**: Find tasks across all projects in one turn.
- **Bulk Scaffolding**: Create projects and multiple tasks in a single operation.
- **Smart Dates**: Natural language date parsing (e.g., "remind me next Friday").
- **Task Memory**: Full support for reading and writing task comments.
- **Explicit Hierarchy**: Clear directional tools for subtasks and dependencies.

```bash
# Start via STDIO (for Claude Desktop)
uv run vikunja-mcp

# Start via SSE (HTTP)
uv run vikunja-mcp dev --transport sse
```

## 🔒 Security & Auth Policy

- **MCP Protocol**: The MCP server is strictly limited to **API Key Authentication**. We do not support user/password login via MCP to ensure secure, scoped agentic access.
- **UI-Only Features**: Features like Buckets (Kanban columns) and Reactions currently require a JWT (UI Session). These are supported in the CLI but are excluded from the MCP server to maintain protocol security.

## 🧪 Testing

We use `testcontainers-python` to run integration tests against a live, ephemeral Vikunja instance. No mocks, just real API verification.

```bash
uv run pytest
```

## 🗺 Future Roadmap
- [ ] **Backgrounds**: Support for Unsplash project backgrounds.
- [ ] **Attachments**: File upload/download support.
- [ ] **Webhooks**: Core models for receiving Vikunja events.
- [ ] **Bulk Labels**: Tools for mass-tagging tasks.

## 📜 License
WTFPL - Do What the Fuck You Want to Public License.
