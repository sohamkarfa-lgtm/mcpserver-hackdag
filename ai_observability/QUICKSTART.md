# 🚀 Quick Start Guide - AI Observability System

## 5-Minute Setup

### Step 1: Verify Integration
The observability system is already integrated into your MCP server. No installation needed!

✅ Core files are in place:
- `knowit_mcp/observability.py` - Core tracking engine
- `knowit_mcp/observability_dashboard.py` - CLI dashboard
- `knowit_mcp/mcp_server_databricks_observability.py` - Updated with tracking

### Step 2: Start Your MCP Server
```bash
cd knowit_mcp
# Start your MCP server as usual (it already has observability enabled)
python mcp_server_databricks_observability.py
```

The server is now tracking all interactions automatically! ✅

### Step 3: Use Claude Desktop
Open Claude Desktop and use your Databricks tools normally. They're now being monitored:

```
User: List all catalogs in my Databricks Unity Catalog
Claude: [Uses list_catalogs tool - tracks tokens & cost automatically]

User: Get metrics summary
Claude: [Uses get_metrics_summary tool - shows tracking data]
```

### Step 4: View Metrics

**Option A: In Claude Desktop**
```
User: Get metrics summary
User: Show cost analysis
User: What are my optimization recommendations?
```

**Option B: CLI Dashboard**
```bash
cd knowit_mcp
python observability_dashboard.py --view summary
```

## Common Commands

### 1. Get Overall Summary
```bash
python observability_dashboard.py --view summary
```

### 2. See Cost Breakdown by Tool
```bash
python observability_dashboard.py --view costs
```

### 3. Get Performance Analysis
```bash
python observability_dashboard.py --view performance
```

### 4. Get Optimization Recommendations
```bash
python observability_dashboard.py --view recommendations
```

### 5. Export Everything as HTML
```bash
python observability_dashboard.py --export-html metrics_report.html
```
Open `metrics_report.html` in your browser 🌐

### 6. Show All Metrics
```bash
python observability_dashboard.py --view all
```

### 7. Get JSON Output
```bash
python observability_dashboard.py --json
```

## What's Being Tracked?

Every time you use a Databricks tool, we track:

| Metric | Description |
|--------|-------------|
| **Input Tokens** | Tokens used for the request |
| **Output Tokens** | Tokens in the response |
| **Total Cost** | Estimated USD cost |
| **Latency** | Total request time in ms |
| **Tool Overhead** | MCP framework overhead |
| **Execution Time** | Actual tool execution time |
| **Retries** | Number of automatic retries |
| **Status** | Success or failure |

## Example Workflow

### Run Your Queries
```
User: List all schemas in the 'main' catalog
```

### Check Metrics in Claude
```
User: Get metrics summary
Claude: Returns:
- Total Interactions: 1
- Total Tokens: ~450
- Total Cost: $0.0067
- Success Rate: 100%
```

### View Details
```
User: Show token breakdown by tool
Claude: Returns detailed breakdown with cost per tool
```

### Optimize
```
User: What are my cost optimization recommendations?
Claude: Returns specific recommendations based on your usage
```

## Data Storage

All metrics are automatically saved to:
```
result/metrics.jsonl
```

This file grows with each interaction. Each line is a complete JSON record.

Example single record:
```json
{
  "interaction_id": "abc123...",
  "timestamp": "2024-05-22T10:30:45",
  "tool_name": "list_catalogs",
  "tokens": {"input_tokens": 50, "output_tokens": 200, "total_tokens": 250},
  "costs": {"model": "claude-3-5-sonnet", "total_cost": 0.0045},
  "performance": {"request_latency_ms": 245.67, "success": true}
}
```

## Pro Tips 💡

### Tip 1: Monitor Expensive Operations
```bash
python observability_dashboard.py --view costs
```
Look for tools with high `total_cost_usd` - these are your optimization targets.

### Tip 2: Check for Failure Patterns
```bash
python observability_dashboard.py --view recommendations
```
The system automatically detects high failure rates and suggests fixes.

### Tip 3: Track Trends
```bash
python observability_dashboard.py --view trends --hours 24
```
See how your costs vary throughout the day.

### Tip 4: Export for Analysis
```bash
python observability_dashboard.py --export-html report.html
```
Share detailed reports with team members.

## Cost Estimation Guide

Costs are calculated based on token usage and model pricing:

**Default Model: Claude 3.5 Sonnet**
- Input: $3 per 1M tokens
- Output: $15 per 1M tokens

**Other Models Supported:**
- Claude 3 Opus: $15/$75 per 1M tokens
- Claude 3 Haiku: $0.25/$1.25 per 1M tokens
- GPT-4: $30/$60 per 1M tokens
- GPT-3.5-turbo: $0.5/$1.5 per 1M tokens

To use a different model:
```python
@track_tool_call(model="claude-3-opus")
def my_tool():
    pass
```

## Troubleshooting

### "No metrics recorded yet"
- The system just started and no tools have been called
- Call a tool first, then check metrics

### Dashboard seems slow
- If you have many interactions (1000+), the dashboard might be slow
- Use `--view summary` for quick results
- Export to JSON and analyze with other tools for large datasets

### Metrics look incorrect
- Token counts are estimates (rough: 4 chars = 1 token)
- For accurate tracking, specify token counts in the decorator:
  ```python
  @track_tool_call(model="claude-3-5-sonnet", input_tokens=50, output_tokens=200)
  ```

## Architecture Overview

```
Claude Desktop
    ↓
MCP Server (mcp_server_databricks_observability.py)
    ├─ Tool 1: list_catalogs [decorated with @track_tool_call]
    ├─ Tool 2: list_schemas [decorated with @track_tool_call]
    ├─ Tool 3: run_sql [decorated with @track_tool_call]
    └─ Tool 4: get_metrics_summary [new observability tool]
    ↓
Observability Engine (observability.py)
    ├─ Captures metrics (tokens, time, performance)
    ├─ Calculates costs
    ├─ Stores to result/metrics.jsonl
    └─ Provides access methods
    ↓
Dashboard (observability_dashboard.py)
    ├─ CLI views (summary, costs, performance, etc.)
    └─ HTML export
```

## Next Steps

1. **Run a query** in Claude Desktop to generate metrics
2. **View summary**: `python observability_dashboard.py --view summary`
3. **Check recommendations**: Look for optimization opportunities
4. **Monitor trends**: Track costs over time
5. **Export reports**: Share insights with stakeholders

## Need Help?

Check the detailed guide: [OBSERVABILITY.md](OBSERVABILITY.md)

**Quick Reference:**
- Features: [OBSERVABILITY.md#-features](OBSERVABILITY.md)
- MCP Tools: [OBSERVABILITY.md#-mcp-tools-available](OBSERVABILITY.md)
- Dashboard Usage: [OBSERVABILITY.md#-dashboard-usage](OBSERVABILITY.md)
- Advanced Usage: [OBSERVABILITY.md#-advanced-usage](OBSERVABILITY.md)

---

**You're all set!** Start using your Databricks tools and watch your costs and performance. 🎉
