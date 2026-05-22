# AI Observability System - Token Usage & Cost Tracking

Complete observability toolkit for monitoring LLM token usage, estimating costs, and tracking performance metrics integrated with your MCP Databricks server.

## 🎯 Features

### Token Tracking
- **Input/Output Tokens**: Automatic tracking of tokens per request
- **Token Estimation**: Automatic estimation when explicit token counts unavailable
- **Token Aggregation**: Summary statistics by tool and time period

### Cost Analysis
- **Real-time Cost Calculation**: Automatic cost estimation based on token usage
- **Multi-Model Support**: Pricing for Claude, GPT-4, and other models
- **Cost Breakdown**: Detailed cost analysis by tool, model, and time period
- **Optimization Recommendations**: Intelligent suggestions to reduce costs

### Performance Metrics
- **Request Latency**: Track total request time
- **Tool Execution Time**: Measure actual tool execution duration
- **Tool Call Overhead**: MCP framework overhead measurement
- **Retry Tracking**: Monitor failed requests and automatic retries
- **Success Rate**: Track and analyze failure patterns

### Observability Tools
- **Interactive Dashboard**: CLI tool for viewing metrics
- **HTML Reports**: Export metrics as HTML reports
- **JSON Export**: Export data in JSON format for analysis
- **CSV Export**: Export for spreadsheet analysis

## 📦 Integration

### 1. Basic Setup

The observability module is already integrated in `mcp_server_databricks_observability.py`:

```python
from observability import track_tool_call, get_observability_summary

@mcp.tool(description="List all catalogs in Unity Catalog")
@track_tool_call(model="claude-3-5-sonnet", input_tokens=50, output_tokens=200)
def list_catalogs() -> list[dict]:
    # Your tool implementation
    pass
```

### 2. Decorator Usage

#### Basic Usage (Auto Token Estimation)
```python
@track_tool_call()  # Tokens auto-estimated
def my_tool():
    pass
```

#### With Explicit Token Counts
```python
@track_tool_call(model="claude-3-5-sonnet", input_tokens=100, output_tokens=200)
def my_tool():
    pass
```

#### With Different Model Pricing
```python
@track_tool_call(model="claude-3-opus")  # Uses Claude 3 Opus pricing
@track_tool_call(model="gpt-4")  # Uses GPT-4 pricing
@track_tool_call(model="claude-3-haiku")  # Uses Claude 3 Haiku pricing
```

## 🛠️ MCP Tools Available

### `get_metrics_summary()`
Returns aggregated metrics including:
- Total interactions
- Total tokens used
- Total estimated cost
- Success rate
- Average latency
- Breakdown by tool

**Example Response:**
```json
{
  "total_interactions": 25,
  "total_tokens_used": 45000,
  "total_estimated_cost": 0.1234,
  "success_rate": 96.0,
  "average_latency_ms": 245.67,
  "by_tool": {
    "list_catalogs": {
      "calls": 10,
      "total_tokens": 10000,
      "total_cost": 0.025,
      "avg_latency_ms": 200.0,
      "failures": 0
    }
  }
}
```

### `get_interaction_metrics(interaction_id: str)`
Get detailed metrics for a specific interaction:

```json
{
  "interaction_id": "abc123...",
  "timestamp": "2024-05-22T10:30:45.123456",
  "tool_name": "list_catalogs",
  "tokens": {
    "input_tokens": 50,
    "output_tokens": 150,
    "total_tokens": 200
  },
  "costs": {
    "model": "claude-3-5-sonnet",
    "input_cost": 0.00015,
    "output_cost": 0.00225,
    "total_cost": 0.0024
  },
  "performance": {
    "request_latency_ms": 245.67,
    "tool_execution_time_ms": 200.45,
    "tool_call_overhead_ms": 45.22,
    "number_of_retries": 0,
    "number_of_failures": 0,
    "success": true
  }
}
```

### `get_token_breakdown()`
Returns token usage and cost by tool:

```json
{
  "list_catalogs": {
    "total_calls": 10,
    "total_tokens": 2000,
    "total_cost_usd": 0.025,
    "average_cost_per_call": 0.0025,
    "average_latency_ms": 200.0,
    "failure_count": 0
  }
}
```

### `get_cost_analysis()`
Returns cost analysis and optimization recommendations:

```json
{
  "total_estimated_cost": "$0.1234",
  "total_interactions": 25,
  "average_cost_per_interaction": "$0.004936",
  "success_rate": "96.00%",
  "recommendations": [
    {
      "issue": "Tool 'run_sql' has highest cost",
      "suggestion": "Consider optimizing or caching results",
      "cost": "$0.0800",
      "potential_savings": "5-15% cost reduction"
    }
  ]
}
```

### `export_metrics_data(format: str)`
Export all metrics in specified format (json or csv):

```json
{
  "format": "json",
  "data": "{ full metrics as JSON }",
  "success": true
}
```

## 📊 Dashboard Usage

### View Summary
```bash
cd knowit_mcp
python observability_dashboard.py --view summary
```

Output:
```
================================================================================
  📊 OBSERVABILITY METRICS SUMMARY
================================================================================

Total Interactions:        25
Total Tokens Used:         45,000
Total Estimated Cost:      $0.1234
Success Rate:              96.00%
Average Latency:           245.67ms
```

### View Detailed Metrics
```bash
python observability_dashboard.py --view detailed
```

Shows each interaction with timestamp, tokens, cost, latency, and status.

### View Cost Breakdown
```bash
python observability_dashboard.py --view costs
```

Shows costs grouped by model and tool.

### View Performance Analysis
```bash
python observability_dashboard.py --view performance
```

Shows latency statistics, retry counts, and failure analysis.

### View Recommendations
```bash
python observability_dashboard.py --view recommendations
```

Shows AI-generated optimization recommendations:
- High failure rate detection
- Expensive tool identification
- Latency bottleneck detection
- Retry pattern analysis

### View Cost Trends
```bash
python observability_dashboard.py --view trends --hours 24
```

Shows cost trend over specified hours with ASCII charts.

### View All
```bash
python observability_dashboard.py --view all
```

Comprehensive report with all views.

### Export HTML Report
```bash
python observability_dashboard.py --export-html metrics_report.html
```

Creates a professional HTML report in `metrics_report.html`.

### JSON Output
```bash
python observability_dashboard.py --json
```

Outputs metrics as JSON for programmatic use.

## 📈 Pricing Configuration

### Supported Models

**Claude Models:**
- `claude-3-5-sonnet`: $3/$15 per 1M input/output tokens
- `claude-3-opus`: $15/$75 per 1M tokens
- `claude-3-haiku`: $0.25/$1.25 per 1M tokens

**OpenAI Models:**
- `gpt-4`: $30/$60 per 1M tokens
- `gpt-3.5-turbo`: $0.5/$1.5 per 1M tokens

### Updating Pricing

To update model pricing, edit `observability.py` and modify the `PRICING` dict in `PricingConfig`:

```python
class PricingConfig:
    PRICING = {
        "your-model": {
            "input": 10.0,   # $ per 1M tokens
            "output": 50.0,  # $ per 1M tokens
        },
    }
```

## 💾 Data Storage

### Metrics Storage
- **Location**: `result/metrics.jsonl`
- **Format**: JSONL (one JSON object per line)
- **Persistence**: Automatic, appended on each interaction
- **Retention**: All historical data retained

### Directory Structure
```
knowit_mcp/
├── observability.py              # Core observability module
├── observability_dashboard.py    # CLI dashboard
└── mcp_server_databricks_observability.py  # MCP server with integration
result/
└── metrics.jsonl                 # Metrics storage
```

## 🔧 Advanced Usage

### Custom Token Estimation

```python
from observability import estimate_tokens

# Estimate tokens from text
token_count = estimate_tokens("your text here")
```

### Programmatic Access

```python
from observability import get_metrics_store, get_observability_summary

# Get metrics store
store = get_metrics_store()

# Get all metrics
all_metrics = store.get_all_metrics()

# Get summary
summary = get_observability_summary()

# Get specific interaction
metric = store.get_metric(interaction_id)
```

### Export Metrics

```python
from observability import export_metrics

# Export as JSON
json_data = export_metrics(format="json")

# Export as CSV
csv_data = export_metrics(format="csv")

# Export to file
export_metrics(format="json", filepath="metrics_export.json")
```

## 📊 Metrics Schema

Each interaction records:

```python
{
    "interaction_id": "uuid",
    "timestamp": "ISO 8601",
    "tool_name": "str",
    "tool_input": {...},
    "tool_output": {...},
    "tokens": {
        "input_tokens": int,
        "output_tokens": int,
        "total_tokens": int
    },
    "costs": {
        "model": "str",
        "input_cost": float,
        "output_cost": float,
        "total_cost": float,
        "currency": "str"
    },
    "performance": {
        "request_latency_ms": float,
        "tool_execution_time_ms": float,
        "tool_call_overhead_ms": float,
        "number_of_retries": int,
        "number_of_failures": int,
        "success": bool,
        "error_message": null|str
    }
}
```

## 💡 Cost Optimization Tips

1. **Monitor Tool Costs**: Use `get_token_breakdown()` to identify expensive tools
2. **Implement Caching**: Cache frequent queries to reduce token usage
3. **Optimize Prompts**: Shorter, more focused prompts reduce input tokens
4. **Batch Operations**: Group multiple operations to reduce overhead
5. **Use Smaller Models**: Consider using Claude Haiku for simple operations
6. **Set Up Alerts**: Monitor cost trends to catch anomalies early
7. **A/B Test**: Compare different prompt approaches using metrics

## 🚀 Integration with Claude Desktop

The MCP server exposes observability tools as Claude functions:

1. Query metrics: "Get my recent token usage"
2. Analyze costs: "Show cost breakdown by tool"
3. Find optimization opportunities: "What are my cost optimization recommendations?"
4. Export reports: "Export all metrics as HTML"

## 📝 Example: Monitoring Token Usage

```python
# In your Claude conversation:
# 1. Run your normal queries
# 2. Ask: "Get metrics summary"
# 3. Claude returns token usage, costs, and performance stats
# 4. Ask: "Show recommendations"
# 5. Get optimization suggestions
```

## 🐛 Troubleshooting

### Metrics not being recorded
1. Ensure `@track_tool_call()` decorator is applied to tools
2. Check that `result/` directory exists and is writable
3. Verify observability.py is in the same directory as MCP server

### Incorrect token counts
- Token estimation is approximate (1 token ≈ 4 characters)
- For accurate counts, provide explicit token values in decorator
- Monitor actual costs and adjust estimates as needed

### Slow dashboard performance
- Dashboard may be slow with 1000+ interactions
- Use `--view summary` for quick overview
- Export to JSON and analyze programmatically for large datasets

## 📞 Support

For issues or questions:
1. Check metrics.jsonl file for raw data
2. Review decorator configuration
3. Verify pricing matches your model
4. Check observability_dashboard.py for detailed error messages

## 📄 License

Part of MCP Server Hackdag project.
