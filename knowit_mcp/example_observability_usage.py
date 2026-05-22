"""
Example Usage - AI Observability System
Demonstrates how to use the observability system programmatically
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from observability import (
    track_tool_call,
    get_metrics_store,
    get_observability_summary,
    export_metrics,
    estimate_tokens,
    PricingConfig,
)


# Example 1: Using the decorator
@track_tool_call(model="claude-3-5-sonnet", input_tokens=100, output_tokens=200)
def example_tool_with_explicit_tokens(query: str) -> dict:
    """Example tool with explicit token counts"""
    print(f"Executing query: {query}")
    return {"result": "sample data", "count": 42}


# Example 2: Auto-estimated tokens
@track_tool_call(model="claude-3-5-sonnet")
def example_tool_auto_tokens(catalog: str) -> list:
    """Example tool with auto-estimated tokens"""
    print(f"Listing catalogs in: {catalog}")
    return [
        {"name": "catalog1", "owner": "user1"},
        {"name": "catalog2", "owner": "user2"},
    ]


# Example 3: Different model pricing
@track_tool_call(model="claude-3-opus")
def expensive_operation() -> dict:
    """Operation using more expensive Claude 3 Opus model"""
    print("Running expensive operation...")
    return {"status": "complete", "data": "large response" * 100}


# Example 4: Using Haiku for simple operations
@track_tool_call(model="claude-3-haiku")
def cheap_operation() -> str:
    """Simple operation using cheaper Haiku model"""
    print("Running simple operation...")
    return "quick response"


def demonstrate_manual_tracking():
    """Show how to manually work with metrics"""
    print("\n=== Manual Metrics Access ===\n")
    
    store = get_metrics_store()
    
    # Get all metrics
    all_metrics = store.get_all_metrics()
    print(f"Total metrics recorded: {len(all_metrics)}")
    
    # Get summary
    summary = get_observability_summary()
    print("\nMetrics Summary:")
    print(f"  Total interactions: {summary['total_interactions']}")
    print(f"  Total tokens used: {summary['total_tokens_used']}")
    print(f"  Total cost: ${summary['total_estimated_cost']:.4f}")
    print(f"  Success rate: {summary['success_rate']:.2f}%")
    print(f"  Average latency: {summary['average_latency_ms']:.2f}ms")
    
    # Get breakdown by tool
    print("\nBreakdown by Tool:")
    for tool, stats in summary.get('by_tool', {}).items():
        print(f"  {tool}:")
        print(f"    Calls: {stats['calls']}")
        print(f"    Tokens: {stats['total_tokens']}")
        print(f"    Cost: ${stats['total_cost']:.6f}")
        print(f"    Avg Latency: {stats['avg_latency_ms']:.2f}ms")


def demonstrate_pricing():
    """Show pricing configuration"""
    print("\n=== Pricing Configuration ===\n")
    
    # Check pricing for different models
    models = ["claude-3-5-sonnet", "claude-3-opus", "claude-3-haiku", "gpt-4"]
    
    for model in models:
        pricing = PricingConfig.get_pricing(model)
        cost = PricingConfig.calculate_cost(model, 1_000_000, 1_000_000)
        print(f"{model}:")
        print(f"  Input: ${pricing['input']}/1M tokens")
        print(f"  Output: ${pricing['output']}/1M tokens")
        print(f"  Cost for 1M input + 1M output: ${cost:.2f}")


def demonstrate_token_estimation():
    """Show token estimation"""
    print("\n=== Token Estimation ===\n")
    
    text_samples = [
        "Hello",
        "This is a medium length text with several words.",
        "This is a very long text with many more words. " * 10,
    ]
    
    for text in text_samples:
        tokens = estimate_tokens(text)
        print(f"Text length: {len(text):4d} chars → ~{tokens:4d} tokens")


def demonstrate_export():
    """Show how to export metrics"""
    print("\n=== Exporting Metrics ===\n")
    
    # Export as JSON
    print("Exporting as JSON...")
    json_export = export_metrics(format="json")
    print(f"  JSON export size: {len(json_export)} bytes")
    
    # Export as CSV
    print("\nExporting as CSV...")
    csv_export = export_metrics(format="csv")
    print(f"  CSV export size: {len(csv_export)} bytes")
    print("  First few lines:")
    for line in csv_export.split('\n')[:3]:
        print(f"    {line}")
    
    # Save to files
    print("\nSaving exports to files...")
    export_metrics(format="json", filepath="metrics_export.json")
    export_metrics(format="csv", filepath="metrics_export.csv")
    print("  ✓ Saved to metrics_export.json")
    print("  ✓ Saved to metrics_export.csv")


def demonstrate_specific_interaction():
    """Show how to get details of a specific interaction"""
    print("\n=== Getting Specific Interaction Details ===\n")
    
    store = get_metrics_store()
    metrics = store.get_all_metrics()
    
    if metrics:
        # Get the most recent interaction
        recent_id = list(metrics.keys())[-1]
        metric = store.get_metric(recent_id)
        
        print(f"Recent Interaction ID: {recent_id}")
        print(json.dumps(metric, indent=2))
    else:
        print("No metrics recorded yet. Run some tools first!")


def cost_analysis():
    """Demonstrate cost analysis"""
    print("\n=== Cost Analysis ===\n")
    
    store = get_metrics_store()
    metrics = store.get_all_metrics()
    
    if not metrics:
        print("No metrics recorded yet.")
        return
    
    # Calculate various metrics
    total_cost = sum(m['costs']['total_cost'] for m in metrics.values())
    total_interactions = len(metrics)
    
    # Group by tool
    tool_costs = {}
    for m in metrics.values():
        tool = m['tool_name']
        if tool not in tool_costs:
            tool_costs[tool] = {"count": 0, "cost": 0}
        tool_costs[tool]["count"] += 1
        tool_costs[tool]["cost"] += m['costs']['total_cost']
    
    print(f"Total Cost: ${total_cost:.4f}")
    print(f"Total Interactions: {total_interactions}")
    print(f"Average Cost per Interaction: ${total_cost/total_interactions:.6f}")
    
    print("\nMost Expensive Tools:")
    for tool, stats in sorted(tool_costs.items(), key=lambda x: x[1]['cost'], reverse=True):
        pct = (stats['cost'] / total_cost * 100) if total_cost > 0 else 0
        print(f"  {tool}: ${stats['cost']:.4f} ({pct:.1f}%) - {stats['count']} calls")


def main():
    """Run all demonstrations"""
    print("=" * 80)
    print("AI OBSERVABILITY SYSTEM - EXAMPLE USAGE")
    print("=" * 80)
    
    # Run example tools
    print("\n>>> Running Example Tools <<<\n")
    
    print("[1] Tool with explicit tokens...")
    result1 = example_tool_with_explicit_tokens("SELECT * FROM table")
    print(f"    Result: {result1}\n")
    
    print("[2] Tool with auto-estimated tokens...")
    result2 = example_tool_auto_tokens("main")
    print(f"    Result: {result2}\n")
    
    print("[3] Expensive operation (Claude Opus)...")
    result3 = expensive_operation()
    print(f"    Result: {result3}\n")
    
    print("[4] Cheap operation (Claude Haiku)...")
    result4 = cheap_operation()
    print(f"    Result: {result4}\n")
    
    # Demonstrate various features
    demonstrate_token_estimation()
    demonstrate_pricing()
    demonstrate_manual_tracking()
    demonstrate_specific_interaction()
    cost_analysis()
    demonstrate_export()
    
    print("\n" + "=" * 80)
    print("✓ Examples complete! Check metrics_export.json and metrics_export.csv")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
