# mcpserver-hackdag

Python project for experimenting with Model Context Protocol (MCP) servers using
FastMCP. The repository contains a small arithmetic MCP server, a LangChain MCP
client, and a Databricks Unity Catalog MCP server.

## Project Structure

```text
.
├── knowit_mcp/
│   ├── mcp_client.py
│   ├── mcp_server_first.py
│   ├── mcp_server_databricks.py
│   └── mcp_server_databricks_uvicorn.py
├── result/
│   ├── KnowitMCP_Privilege_Audit_Report.docx
│   └── Knowit_MCP_Value_Positioning.docx
├── main.py
├── pyproject.toml
├── uv.lock
└── README.md
```

## Requirements

- Python 3.12
- `uv`
- Databricks workspace access for the Databricks MCP server
- A Databricks personal access token or another auth method supported by the
  Databricks SDK

Install dependencies:

```powershell
uv sync
```

The current dependency list includes:

- `fastmcp`
- `langchain`
- `langchain-mcp-adapters`
- `databricks-sdk`
- `python-dotenv`
- `uvicorn`

If these are missing in another checkout, add them with:

```powershell
uv add fastmcp langchain langchain-mcp-adapters databricks-sdk python-dotenv uvicorn
```

## Simple MCP Server

`knowit_mcp/mcp_server_first.py` exposes two demo tools:

- `add(a: int, b: int) -> int`
- `subtract(a: int, b: int) -> int`

Run it:

```powershell
uv run python .\knowit_mcp\mcp_server_first.py
```

The server starts on:

```text
http://localhost:8050/mcp
```

## MCP Client

`knowit_mcp/mcp_client.py` connects to the local MCP server over streamable HTTP,
lists available tools, asks the user for two integers, and invokes the first
available tool.

Run the simple server first, then in another terminal run:

```powershell
uv run python .\knowit_mcp\mcp_client.py
```

Example flow:

```text
Tools available in the MCP server: 2
- add: Add two numbers together.
- subtract: Subtract one number from another.
Enter value for a: 5
Enter value for b: 3
Result from add: 8
```

## Databricks MCP Server

Use `knowit_mcp/mcp_server_databricks.py` as the preferred Databricks server.
It exposes Databricks Unity Catalog and SQL capabilities through MCP tools.

Current tools:

- `list_catalogs()`
- `list_schemas(catalog_name: str)`
- `list_tables(catalog_name: str, schema_name: str)`
- `run_sql(sql: str)`

### Environment Variables

Create `knowit_mcp/.env` for local development:

```text
DATABRICKS_HOST=https://adb-<workspace-id>.<region>.azuredatabricks.net
DATABRICKS_TOKEN=<your-token>
DATABRICKS_WAREHOUSE_ID=<sql-warehouse-id>

DEFAULT_CATALOG=main
DEFAULT_SCHEMA=information_schema
```

Do not commit `.env`. Commit a `.env.example` instead if shared configuration
documentation is needed.

### Run Databricks Server

```powershell
uv run python .\knowit_mcp\mcp_server_databricks.py
```

Default endpoint:

```text
http://localhost:8050/mcp
```

The server reads `HOST` and `PORT` from the environment when present, which is
useful for container or cloud hosting:

```powershell
$env:PORT = "8080"
uv run python .\knowit_mcp\mcp_server_databricks.py
```

## Uvicorn Variant

`knowit_mcp/mcp_server_databricks_uvicorn.py` is a manual uvicorn hosting
variant. Keep it only if direct ASGI hosting is needed. For normal local MCP
development, prefer `mcp_server_databricks.py` because it uses FastMCP's own
runner.

If embedding the FastMCP app in another ASGI app, make sure the FastMCP app
lifespan is wired into the parent application. Otherwise streamable HTTP may
fail because the session manager is not initialized.

## Security Notes

- `DATABRICKS_TOKEN` must be treated as a secret.
- Use a Databricks service principal or token with the minimum privileges needed.
- The current `run_sql` tool executes the SQL text it receives. For production,
  restrict this to read-only statements, add query limits, log usage, and avoid
  exposing write or admin permissions.
- Add pagination or result limits for large catalog/table responses.

## Troubleshooting

### `ModuleNotFoundError: No module named 'databricks.sdk'`

Install the Databricks SDK package:

```powershell
uv add databricks-sdk
```

Do not use the older `databricks` package for `from databricks.sdk import
WorkspaceClient`.

### `ModuleNotFoundError: No module named 'dotenv'`

Install dotenv support:

```powershell
uv add python-dotenv
```

### `uvicorn` Import Error

Only the manual uvicorn server variant needs this directly:

```powershell
uv add uvicorn
```

### Port Already In Use

Set another port:

```powershell
$env:PORT = "8050"
uv run python .\knowit_mcp\mcp_server_databricks.py
```

## Next Improvements
- Split Databricks client creation into a helper so environment validation gives
  clearer errors.
- Add read-only validation and row limits to `run_sql`.
- Add tests for tool registration and input/output shapes.
