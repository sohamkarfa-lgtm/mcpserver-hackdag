import os
from fastmcp import FastMCP
from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv

load_dotenv()


mcp = FastMCP(
    name="unity-catalog-business-context"
)

# Databricks SDK picks up DATABRICKS_HOST + DATABRICKS_TOKEN from env
w = WorkspaceClient()

@mcp.tool(description="List all catalogs in Unity Catalog")
def list_catalogs() -> list[dict]:
    catalogs = w.catalogs.list()
    return [{"name": c.name, "comment": c.comment, "owner": c.owner} for c in catalogs]

@mcp.tool(description="List schemas in a given catalog")
def list_schemas(catalog_name: str) -> list[dict]:
    schemas = w.schemas.list(catalog_name=catalog_name)
    return [{"name": s.name, "comment": s.comment, "owner": s.owner} for s in schemas]

@mcp.tool(description="List tables in a given catalog and schema")
def list_tables(catalog_name: str, schema_name: str) -> list[dict]:
    tables = w.tables.list(catalog_name=catalog_name, schema_name=schema_name)
    return [{"name": t.name, "comment": t.comment, "owner": t.owner} for t in tables]

if __name__ == "__main__":
    import uvicorn
    app = mcp.http_app()  # Streamable HTTP transport
    uvicorn.run(app, host="0.0.0.0", port=8050)
