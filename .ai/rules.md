# Vikunja Python Project Rules

## Repository Architecture & Packaging
- **Structure**:
  - `/vikunja_python/core`: Core logic, models, and HTTP client. Minimal dependencies (httpx, pydantic).
  - `/vikunja_python/cli`: Command-line interface using `typer`.
  - `/vikunja_python/mcp`: MCP server using `fastmcp`.
- **Packaging**: Use a modern `pyproject.toml` with `[cli]` and `[mcp]` defined as optional dependencies (extras).
- **Imports**: Cross-module imports must only pull from `/core`. `/cli` and `/mcp` must never import from each other.

## Coding Standards (Python 3.13)
- **Data Models**: Use `pydantic>=2.0`.
  - All models must include `model_config = ConfigDict(extra='ignore')`.
  - Every field must have a rich `description="..."` tag for downstream LLM consumption.
- **Asynchronous Design**:
  - Use `httpx` for all API calls.
  - Leverage modern Python 3.13 async patterns, specifically `asyncio.TaskGroup` for concurrent operations.
- **Zero-Inference**: Never hallucinate API endpoints or payload fields. If a schema is unknown, halt and request clarification.

## Error Handling & LLM Bridging
- **Exceptions**: Never return raw stack traces or raw `httpx.HTTPStatusError` exceptions to downstream clients.
- **Structured Errors**: Catch errors and return them as structured, descriptive JSON so the calling agent can self-correct.

## MCP Skill & Guidance
- **SKILL.md**: Maintain a high-signal `SKILL.md` in `/vikunja_python/mcp/` that explains tool usage patterns and operational procedures for downstream LLMs.
- **Guidance**: When modifying MCP tools, ensure the `SKILL.md` is updated to reflect the most efficient interaction patterns (e.g., preferring search over listing).
- **Validation**: Every update to MCP tool docstrings or parameter annotations MUST be validated using the "Clean-Room Subagent" workflow defined in `.ai/mcp_validation.md`. This ensures discoverability and token efficiency.

## Maintenance & Operations Workflow
- **API Spec Updates**:
  1. Fetch the latest spec via `curl $VIKUNJA_URL/api/v1/docs.json`.
  2. Strictly map new endpoints to Pydantic models using the established baseline.
  3. Validate against live server responses before committing.

## Testing Strategy
- **Integration Tests**: Use `testcontainers-python` to spin up ephemeral Vikunja instances.
- **No Mocking**: Do not rely on mocked HTTP responses for integration tests. Use real server instances.
- **Scaffolding**: Generate random alpha username and 32-64 character alphanum password for ephemeral test instances.

## Logging
- **Core**: Use a centralized `setup_logging` function. When configuring the root logger, **ALWAYS** use `force=True` to ensure our logging configuration overrides any handlers set by underlying libraries (like uvicorn or fastmcp).
- **MCP**: Explicitly configure the root logger to output exclusively to `sys.stderr` to avoid corrupting the MCP JSON-RPC protocol on `stdout`.
- **Debug Flag**: Support a `VIKUNJA_DEBUG` environment variable. If set to `"1"`, `"true"`, `"yes"`, or `"on"` (case-insensitive), set the log level to `DEBUG`. Otherwise, default to `INFO`.
- **Agentic Errors**: Return errors the LLM needs for self-correction as structured JSON in the tool's return payload.

## Style & Documentation
- Follow PEP 8 standards.
- Use type hints for all function signatures and variables.
- Write clear, concise docstrings for all public classes and methods.
