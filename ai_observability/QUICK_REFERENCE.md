# 🎯 AI Observability System - Quick Reference Card

## 📌 Essential Commands

### Start Server
```bash
cd knowit_mcp
python mcp_server_databricks_observability.py
```

### View Dashboard
```bash
# Summary view (recommended to start)
python observability_dashboard.py --view summary

# All views
python observability_dashboard.py --view all

# Specific views
python observability_dashboard.py --view costs
python observability_dashboard.py --view performance
python observability_dashboard.py --view recommendations
python observability_dashboard.py --view trends
```

### Export Reports
```bash
# HTML report
python observability_dashboard.py --export-html report.html

# JSON output
python observability_dashboard.py --json
```

---

## 🗂️ Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `observability.py` | Core engine | 430 |
| `observability_dashboard.py` | CLI dashboard | 450 |
| `mcp_server_databricks_observability.py` | MCP + tracking | Updated |
| `result/metrics.jsonl` | Metrics storage | Auto-created |

---

## 🔧 Tracked Metrics

```
Per Interaction:
├── interaction_id (unique UUID)
├── timestamp (ISO-8601)
├── tool_name (which tool was called)
├── tokens (input/output/total)
├── costs (USD amount)
└── performance (latency, overhead, retries)
```

---

## 💻 MCP Tools Available

### In Claude Desktop

```
1. get_metrics_summary()
   → Total tokens, cost, success rate, by-tool breakdown

2. get_token_breakdown()
   → Token usage per tool

3. get_cost_analysis()
   → Cost breakdown + optimization recommendations

4. get_interaction_metrics(interaction_id)
   → Detailed metrics for one interaction

5. export_metrics_data(format)
   → Export all metrics (json or csv)
```

---

## 💰 Pricing (Per 1M Tokens)

| Model | Input | Output |
|-------|-------|--------|
| Claude 3.5 Sonnet | $3 | $15 |
| Claude 3 Opus | $15 | $75 |
| Claude 3 Haiku | $0.25 | $1.25 |
| GPT-4 | $30 | $60 |
| GPT-3.5-turbo | $0.5 | $1.5 |

---

## 📊 Dashboard Views

```
--view summary     → Overall metrics
--view detailed    → Per-interaction details
--view costs       → Cost breakdown
--view performance → Latency & reliability
--view recommendations → Optimization tips
--view trends      → Cost trends (24h default)
--view all         → Everything
```

---

## 🔄 Data Flow

```
Claude Desktop
    ↓ (Query)
MCP Server
    ↓ (Tool Call)
@track_tool_call decorator
    ↓ (Capture Metrics)
MetricsStore
    ↓ (Append to JSONL)
result/metrics.jsonl
    ↓
get_metrics_store() / get_observability_summary()
    ↓
Dashboard / Export / Claude
```

---

## 📈 Usage Pattern

### Step 1: Run Queries
```
User: "List all catalogs"
System: Tracks tokens, cost, performance automatically
```

### Step 2: View Metrics
```bash
python observability_dashboard.py --view summary
```

### Step 3: Analyze & Optimize
```
User: "Get cost analysis"
Claude: Returns recommendations
```

---

## 🎯 Common Queries

### "How much have I spent?"
```bash
python observability_dashboard.py --view costs
# Or in Claude: "Get metrics summary"
```

### "Which tool is most expensive?"
```bash
python observability_dashboard.py --view costs
# Look for highest total_cost entry
```

### "How can I reduce costs?"
```bash
python observability_dashboard.py --view recommendations
# Or in Claude: "Get cost analysis"
```

### "What's my performance?"
```bash
python observability_dashboard.py --view performance
```

### "Export for reporting"
```bash
python observability_dashboard.py --export-html report.html
```

---

## 🚀 Integration Points

### Existing Tools (All Tracked)
- `list_catalogs()` ✓
- `list_schemas()` ✓
- `list_tables()` ✓
- `run_sql()` ✓

### New Tools (Observability)
- `get_metrics_summary()` ✓
- `get_token_breakdown()` ✓
- `get_cost_analysis()` ✓
- `get_interaction_metrics()` ✓
- `export_metrics_data()` ✓

---

## 📝 Add Tracking to New Tools

```python
from observability import track_tool_call

@mcp.tool(description="Your tool")
@track_tool_call(model="claude-3-5-sonnet", input_tokens=50, output_tokens=100)
def your_tool():
    pass
```

---

## 🔍 Storage Location

```
result/metrics.jsonl  (JSONL format, one object per line)

Example record:
{
  "interaction_id": "uuid",
  "tool_name": "run_sql",
  "tokens": {"total_tokens": 1700},
  "costs": {"total_cost": 0.0195},
  "performance": {"request_latency_ms": 450.23}
}
```

---

## 📚 Documentation Files

| Doc | Purpose | Read Time |
|-----|---------|-----------|
| `QUICKSTART.md` | Get started | 5 min |
| `OBSERVABILITY.md` | Full reference | 20 min |
| `FILES_CREATED.md` | What was built | 10 min |
| `IMPLEMENTATION_SUMMARY.md` | Technical | 15 min |
| `AI_OBSERVABILITY_COMPLETE.md` | Complete guide | 25 min |

---

## ⚡ Pro Tips

✓ Use `--view summary` for quick status
✓ Use `--view recommendations` to find optimization opportunities
✓ Use `--export-html` to share with team
✓ Check `result/metrics.jsonl` for raw data
✓ Run `example_observability_usage.py` to learn API

---

## 🐛 Quick Troubleshooting

**"No metrics appearing"**
→ Ensure decorator applied to tools
→ Check `result/` directory exists

**"Tokens look wrong"**
→ Token estimation is approximate (4 chars = 1 token)
→ Provide explicit tokens: `input_tokens=100`

**"Can't import observability"**
→ Run from `knowit_mcp/` directory
→ Ensure `observability.py` in same directory

---

## 📊 Expected Metrics Output

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
      "total_tokens": 2500,
      "total_cost": 0.0375,
      "avg_latency_ms": 200.0,
      "failures": 0
    }
  }
}
```

---

## ✅ Status

**Implementation:** ✅ Complete
**Testing:** ✅ Ready
**Documentation:** ✅ Complete
**Production Ready:** ✅ Yes

---

## 🎯 Next Actions

1. ✅ Start MCP server
2. ✅ Make queries in Claude
3. ✅ View dashboard: `python observability_dashboard.py --view summary`
4. ✅ Export report: `python observability_dashboard.py --export-html report.html`
5. ✅ Implement recommendations

---

**Version:** 1.0
**Date:** May 22, 2026
**Status:** Production Ready ✅
