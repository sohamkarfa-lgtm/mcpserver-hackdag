import os
from fastmcp import FastMCP
from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv
from langchain_protocol import Any

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

@mcp.tool(description="Run a SQL statement directly against the Databricks serverless warehouse.")
def run_sql(sql: str) -> dict[str, Any]:
    response = w.statement_execution.execute_statement(warehouse_id=os.getenv("DATABRICKS_WAREHOUSE_ID"), statement=sql)
    
    result = response.result
    manifest = response.manifest

    columns = [col.name for col in (manifest.schema.columns if manifest and manifest.schema else [])]
    
    rows = []
    if result and result.data_array:
        for row in result.data_array:
            rows.append(dict(zip(columns, row)))

    return {"columns": columns, "rows": rows, "row_count": len(rows)}

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8050")),
        path="/mcp"
    )