import os
import json
from fastmcp import FastMCP
from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv
from langchain_protocol import Any
from observability import track_tool_call, get_observability_summary, export_metrics, get_metrics_store

load_dotenv()

mcp = FastMCP(
    name="unity-catalog-business-context"
)

# Databricks SDK picks up DATABRICKS_HOST + DATABRICKS_TOKEN from env
w = WorkspaceClient()

@mcp.tool(description="List all catalogs in Unity Catalog")
@track_tool_call(input_tokens=50, output_tokens=200)
def list_catalogs(model: str) -> list[dict]:
    catalogs = w.catalogs.list()
    return [{"name": c.name, "comment": c.comment, "owner": c.owner} for c in catalogs]


@mcp.tool(description="List schemas in a given catalog")
@track_tool_call(input_tokens=100, output_tokens=300)
def list_schemas(catalog_name: str, model: str) -> list[dict]:
    schemas = w.schemas.list(catalog_name=catalog_name)
    return [{"name": s.name, "comment": s.comment, "owner": s.owner} for s in schemas]


@mcp.tool(description="List tables in a given catalog and schema")
@track_tool_call(input_tokens=150, output_tokens=400)
def list_tables(catalog_name: str, schema_name: str, model: str) -> list[dict]:
    tables = w.tables.list(catalog_name=catalog_name, schema_name=schema_name)
    return [{"name": t.name, "comment": t.comment, "owner": t.owner} for t in tables]


@mcp.tool(description="Run a SQL statement directly against the Databricks serverless warehouse.")
@track_tool_call()  # Tokens will be auto-estimated
def run_sql(sql: str, model: str) -> dict[str, Any]:
    response = w.statement_execution.execute_statement(warehouse_id=os.getenv("DATABRICKS_WAREHOUSE_ID"), statement=sql)
    
    result = response.result
    manifest = response.manifest

    columns = [col.name for col in (manifest.schema.columns if manifest and manifest.schema else [])]
    
    rows = []
    if result and result.data_array:
        for row in result.data_array:
            rows.append(dict(zip(columns, row)))

    return {"columns": columns, "rows": rows, "row_count": len(rows)}


@mcp.tool(description="Get observability metrics summary - token usage, costs, and performance statistics")
def get_metrics_summary() -> dict[str, Any]:
    """Returns aggregated metrics including token usage, costs, and performance stats"""
    summary = get_observability_summary()
    return summary


@mcp.tool(description="Get detailed metrics for a specific interaction by ID")
def get_interaction_metrics(interaction_id: str) -> dict[str, Any]:
    """Returns detailed metrics for a specific tool call interaction"""
    store = get_metrics_store()
    metric = store.get_metric(interaction_id)
    if metric:
        return metric
    return {"error": f"Interaction {interaction_id} not found"}


@mcp.tool(description="Get all recorded metrics in a specified format (json or csv)")
def export_metrics_data(format: str = "json") -> dict[str, Any]:
    """Export all metrics in JSON or CSV format"""
    try:
        result = export_metrics(format=format)
        return {
            "format": format,
            "data": result,
            "success": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }


@mcp.tool(description="Get token usage breakdown by tool")
def get_token_breakdown() -> dict[str, Any]:
    """Returns token usage and cost breakdown grouped by tool"""
    summary = get_observability_summary()
    breakdown = {}
    
    for tool, stats in summary.get("by_tool", {}).items():
        breakdown[tool] = {
            "total_calls": stats["calls"],
            "total_tokens": stats["total_tokens"],
            "total_cost_usd": stats["total_cost"],
            "average_cost_per_call": round(stats["total_cost"] / stats["calls"], 6) if stats["calls"] > 0 else 0,
            "average_latency_ms": stats["avg_latency_ms"],
            "failure_count": stats["failures"],
        }
    
    return breakdown


@mcp.tool(description="Get cost analysis and recommendations for optimization")
def get_cost_analysis() -> dict[str, Any]:
    """Returns cost analysis and optimization recommendations"""
    summary = get_observability_summary()
    
    analysis = {
        "total_estimated_cost": f"${summary.get('total_estimated_cost', 0):.4f}",
        "total_interactions": summary.get("total_interactions", 0),
        "average_cost_per_interaction": f"${summary.get('total_estimated_cost', 0) / max(1, summary.get('total_interactions', 1)):.6f}",
        "success_rate": f"{summary.get('success_rate', 0):.2f}%",
        "recommendations": [],
    }
    
    # Add recommendations based on metrics
    if summary.get("success_rate", 100) < 90:
        analysis["recommendations"].append({
            "issue": "High failure rate",
            "suggestion": "Implement retry logic or check tool inputs",
            "potential_savings": "10-20% cost reduction"
        })
    
    # Identify expensive tools
    tool_costs = {
        tool: stats["total_cost"]
        for tool, stats in summary.get("by_tool", {}).items()
    }
    if tool_costs:
        most_expensive = max(tool_costs.items(), key=lambda x: x[1])
        analysis["recommendations"].append({
            "issue": f"Tool '{most_expensive[0]}' has highest cost",
            "suggestion": "Consider optimizing or caching results",
            "cost": f"${most_expensive[1]:.4f}",
            "potential_savings": "5-15% cost reduction"
        })
    
    return analysis



if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8050")),
        path="/mcp"
    )
