# MCP Usability Validation Subskill

This subskill defines the mandatory validation process for updating MCP tool definitions to ensure they remain "discoverable" and efficient for downstream LLMs.

## Prerequisites
- Docker (for ephemeral container)
- `pytest-asyncio` and `testcontainers` installed in the dev environment.

## Validation Workflow

### 1. Environment Preparation
- Spin up a persistent or ephemeral Vikunja container. 
- Example: `docker run -d -p 3456:3456 --name vikunja_val vikunja/vikunja:2.3.0`
- Populate the instance with sample data (projects, tasks with descriptions, labels, etc.) using the core `VikunjaClient`.

### 2. Clean-Room Subagent Invocation
- Invoke a light subagent (e.g., `generalist`) using the `invoke_agent` tool.
- **Strict Requirement**: Provide the subagent with **zero prior context** about the specific changes or the system state.
- **The Prompt**: 
  - "You are a light subagent validating a refactored MCP server."
  - Provide access to `vikunja_python/mcp/server.py` as the only documentation.
  - Define a discovery-based goal (e.g., "Find the secret code hidden in the description of Task X").

### 3. Success Criteria
- **Discoverability**: The subagent correctly identifies which tool to use based on the `Annotated` descriptions and docstrings.
- **Efficiency**: The subagent completes the task in the minimum possible number of turns (ideally 1-2 for project-wide discovery).
- **Correctness**: The subagent accurately retrieves and interprets the data from the live server.

### 4. Cleanup
- Stop and remove the validation container.
- Delete any temporary validation scripts or tests.
