"""
Observability Dashboard - CLI tool for monitoring metrics
"""
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from observability import get_metrics_store, get_observability_summary
import os


class ObservabilityDashboard:
    """CLI Dashboard for monitoring observability metrics"""
    
    def __init__(self):
        self.store = get_metrics_store()
    
    def print_header(self, text: str):
        """Print a formatted header"""
        width = 80
        print(f"\n{'=' * width}")
        print(f"  {text}")
        print(f"{'=' * width}\n")
    
    def print_section(self, text: str):
        """Print a section header"""
        print(f"\n>>> {text}")
        print("-" * 80)
    
    def show_summary(self):
        """Display metrics summary"""
        self.print_header("📊 OBSERVABILITY METRICS SUMMARY")
        
        summary = get_observability_summary()
        
        # Overall stats
        print(f"Total Interactions:        {summary['total_interactions']}")
        print(f"Total Tokens Used:         {summary['total_tokens_used']:,}")
        print(f"Total Estimated Cost:      ${summary['total_estimated_cost']:.4f}")
        print(f"Success Rate:              {summary['success_rate']:.2f}%")
        print(f"Average Latency:           {summary['average_latency_ms']:.2f}ms")
        
        # Tool breakdown
        if summary['by_tool']:
            self.print_section("Breakdown by Tool")
            print(f"{'Tool Name':<20} {'Calls':<8} {'Tokens':<10} {'Cost':<12} {'Latency':<12} {'Failures':<8}")
            print("-" * 80)
            
            for tool, stats in sorted(summary['by_tool'].items()):
                print(
                    f"{tool:<20} {stats['calls']:<8} {stats['total_tokens']:<10} "
                    f"${stats['total_cost']:<11.4f} {stats['avg_latency_ms']:<11.2f}ms {stats['failures']:<8}"
                )
    
    def show_detailed_metrics(self):
        """Display detailed metrics for each interaction"""
        self.print_header("📋 DETAILED INTERACTION METRICS")
        
        metrics = self.store.get_all_metrics()
        
        if not metrics:
            print("No metrics recorded yet.")
            return
        
        # Sort by timestamp
        sorted_metrics = sorted(metrics.items(), key=lambda x: x[1].get('timestamp', ''), reverse=True)
        
        for idx, (interaction_id, metric) in enumerate(sorted_metrics[:20], 1):  # Show last 20
            print(f"\n[{idx}] Interaction ID: {interaction_id}")
            print(f"    Tool: {metric.get('tool_name', 'Unknown')}")
            print(f"    Timestamp: {metric.get('timestamp', 'Unknown')}")
            print(f"    Tokens: Input={metric['tokens']['input_tokens']}, "
                  f"Output={metric['tokens']['output_tokens']}, "
                  f"Total={metric['tokens']['total_tokens']}")
            print(f"    Cost: ${metric['costs']['total_cost']:.6f}")
            print(f"    Latency: {metric['performance']['request_latency_ms']:.2f}ms")
            print(f"    Status: {'✓ Success' if metric['performance']['success'] else '✗ Failed'}")
            
            if not metric['performance']['success']:
                print(f"    Error: {metric['performance']['error_message']}")
    
    def show_cost_breakdown(self):
        """Display cost breakdown by model and tool"""
        self.print_header("💰 COST BREAKDOWN ANALYSIS")
        
        metrics = self.store.get_all_metrics()
        cost_by_model = {}
        cost_by_tool = {}
        
        for metric in metrics.values():
            model = metric['costs']['model']
            tool = metric['tool_name']
            cost = metric['costs']['total_cost']
            
            if model not in cost_by_model:
                cost_by_model[model] = 0
            cost_by_model[model] += cost
            
            if tool not in cost_by_tool:
                cost_by_tool[tool] = 0
            cost_by_tool[tool] += cost
        
        self.print_section("Cost by Model")
        for model, cost in sorted(cost_by_model.items(), key=lambda x: x[1], reverse=True):
            percentage = (cost / sum(cost_by_model.values()) * 100) if cost_by_model else 0
            print(f"{model:<30} ${cost:<12.4f} ({percentage:.1f}%)")
        
        self.print_section("Cost by Tool")
        for tool, cost in sorted(cost_by_tool.items(), key=lambda x: x[1], reverse=True):
            percentage = (cost / sum(cost_by_tool.values()) * 100) if cost_by_tool else 0
            print(f"{tool:<30} ${cost:<12.4f} ({percentage:.1f}%)")
    
    def show_performance_analysis(self):
        """Display performance metrics"""
        self.print_header("⚡ PERFORMANCE ANALYSIS")
        
        metrics = self.store.get_all_metrics()
        
        if not metrics:
            print("No metrics recorded yet.")
            return
        
        latencies = [m['performance']['request_latency_ms'] for m in metrics.values()]
        overheads = [m['performance']['tool_call_overhead_ms'] for m in metrics.values()]
        failures = sum(1 for m in metrics.values() if not m['performance']['success'])
        retries = sum(m['performance']['number_of_retries'] for m in metrics.values())
        
        print(f"Total Calls:               {len(metrics)}")
        print(f"Successful:                {len(metrics) - failures}")
        print(f"Failed:                    {failures}")
        print(f"Total Retries:             {retries}")
        
        print("\nLatency Statistics:")
        print(f"  Min:                     {min(latencies):.2f}ms" if latencies else "  N/A")
        print(f"  Max:                     {max(latencies):.2f}ms" if latencies else "  N/A")
        print(f"  Average:                 {sum(latencies)/len(latencies):.2f}ms" if latencies else "  N/A")
        
        print("\nTool Call Overhead:")
        print(f"  Min:                     {min(overheads):.2f}ms" if overheads else "  N/A")
        print(f"  Max:                     {max(overheads):.2f}ms" if overheads else "  N/A")
        print(f"  Average:                 {sum(overheads)/len(overheads):.2f}ms" if overheads else "  N/A")
    
    def show_recommendations(self):
        """Display cost optimization recommendations"""
        self.print_header("💡 OPTIMIZATION RECOMMENDATIONS")
        
        summary = get_observability_summary()
        metrics = self.store.get_all_metrics()
        
        recommendations = []
        
        # Check failure rate
        if summary['success_rate'] < 90:
            recommendations.append({
                "priority": "HIGH",
                "title": "High Failure Rate Detected",
                "description": f"Success rate is {summary['success_rate']:.2f}%, which is below 90%",
                "impact": "Reduces efficiency and increases unnecessary costs",
                "action": "Review error messages and improve error handling",
                "potential_savings": "10-20%"
            })
        
        # Check for retries
        total_retries = sum(m['performance']['number_of_retries'] for m in metrics.values())
        if total_retries > 5:
            recommendations.append({
                "priority": "MEDIUM",
                "title": "High Retry Count",
                "description": f"Total retries: {total_retries}",
                "impact": "Increases latency and token usage",
                "action": "Implement exponential backoff and request deduplication",
                "potential_savings": "5-15%"
            })
        
        # Check for expensive tools
        tool_costs = {
            tool: stats['total_cost']
            for tool, stats in summary.get('by_tool', {}).items()
        }
        if tool_costs:
            most_expensive = max(tool_costs.items(), key=lambda x: x[1])
            total_cost = sum(tool_costs.values())
            if most_expensive[1] / total_cost > 0.5:
                recommendations.append({
                    "priority": "MEDIUM",
                    "title": "Single Tool Dominates Costs",
                    "description": f"Tool '{most_expensive[0]}' accounts for {most_expensive[1]/total_cost*100:.1f}% of costs",
                    "impact": f"${most_expensive[1]:.4f}",
                    "action": "Consider caching, result deduplication, or query optimization",
                    "potential_savings": "5-15%"
                })
        
        # Check latency
        if summary['average_latency_ms'] > 1000:
            recommendations.append({
                "priority": "LOW",
                "title": "High Average Latency",
                "description": f"Average latency: {summary['average_latency_ms']:.2f}ms",
                "impact": "May indicate bottlenecks in tool execution",
                "action": "Profile tool execution and optimize slow components",
                "potential_savings": "Improved UX"
            })
        
        if not recommendations:
            print("✓ Your system is well-optimized! No critical issues found.")
        else:
            for idx, rec in enumerate(recommendations, 1):
                priority_symbol = "🔴" if rec["priority"] == "HIGH" else "🟡" if rec["priority"] == "MEDIUM" else "🟢"
                print(f"\n[{idx}] {priority_symbol} {rec['priority']} PRIORITY: {rec['title']}")
                print(f"    Description:  {rec['description']}")
                print(f"    Impact:       {rec['impact']}")
                print(f"    Action:       {rec['action']}")
                print(f"    Savings:      {rec['potential_savings']}")
    
    def show_time_series(self, hours: int = 24):
        """Display cost over time"""
        self.print_header(f"📈 COST TREND (Last {hours} hours)")
        
        metrics = self.store.get_all_metrics()
        now = datetime.utcnow()
        
        # Group by hour
        hourly_costs = {}
        for metric in metrics.values():
            timestamp = datetime.fromisoformat(metric['timestamp'])
            if now - timedelta(hours=hours) <= timestamp <= now:
                hour_key = timestamp.replace(minute=0, second=0, microsecond=0).isoformat()
                if hour_key not in hourly_costs:
                    hourly_costs[hour_key] = 0
                hourly_costs[hour_key] += metric['costs']['total_cost']
        
        if not hourly_costs:
            print("No metrics in the specified time range.")
            return
        
        total = sum(hourly_costs.values())
        print(f"Total cost in last {hours} hours: ${total:.4f}\n")
        
        for hour, cost in sorted(hourly_costs.items()):
            bar_length = int(cost / max(hourly_costs.values()) * 40)
            bar = "█" * bar_length
            print(f"{hour} │ {bar} ${cost:.4f}")
    
    def export_to_html(self, filepath: str = "metrics_report.html"):
        """Export metrics as HTML report"""
        summary = get_observability_summary()
        metrics = self.store.get_all_metrics()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Observability Metrics Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background: #f0f0f0; padding: 15px; border-radius: 5px; }}
                .metric {{ display: inline-block; margin: 10px 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .cost {{ color: #d32f2f; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Observability Metrics Report</h1>
            <p>Generated: {datetime.now().isoformat()}</p>
            
            <div class="summary">
                <h2>Summary</h2>
                <div class="metric">Total Interactions: <strong>{summary['total_interactions']}</strong></div>
                <div class="metric">Total Tokens: <strong>{summary['total_tokens_used']:,}</strong></div>
                <div class="metric">Total Cost: <strong class="cost">${summary['total_estimated_cost']:.4f}</strong></div>
                <div class="metric">Success Rate: <strong>{summary['success_rate']:.2f}%</strong></div>
            </div>
            
            <h2>Metrics by Tool</h2>
            <table>
                <tr>
                    <th>Tool</th>
                    <th>Calls</th>
                    <th>Tokens</th>
                    <th>Cost</th>
                    <th>Avg Latency</th>
                    <th>Failures</th>
                </tr>
        """
        
        for tool, stats in summary.get('by_tool', {}).items():
            html += f"""
                <tr>
                    <td>{tool}</td>
                    <td>{stats['calls']}</td>
                    <td>{stats['total_tokens']}</td>
                    <td class="cost">${stats['total_cost']:.4f}</td>
                    <td>{stats['avg_latency_ms']:.2f}ms</td>
                    <td>{stats['failures']}</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        Path(filepath).write_text(html)
        print(f"HTML report exported to {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Observability Dashboard - Monitor LLM token usage and costs"
    )
    parser.add_argument(
        "--view",
        choices=["summary", "detailed", "costs", "performance", "recommendations", "trends", "all"],
        default="summary",
        help="What to display"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Hours to analyze for trends"
    )
    parser.add_argument(
        "--export-html",
        type=str,
        help="Export metrics to HTML file"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    
    args = parser.parse_args()
    dashboard = ObservabilityDashboard()
    
    if args.json:
        print(json.dumps(get_observability_summary(), indent=2))
    elif args.export_html:
        dashboard.export_to_html(args.export_html)
    elif args.view == "all":
        dashboard.show_summary()
        dashboard.show_detailed_metrics()
        dashboard.show_cost_breakdown()
        dashboard.show_performance_analysis()
        dashboard.show_recommendations()
        dashboard.show_time_series(args.hours)
    elif args.view == "summary":
        dashboard.show_summary()
    elif args.view == "detailed":
        dashboard.show_detailed_metrics()
    elif args.view == "costs":
        dashboard.show_cost_breakdown()
    elif args.view == "performance":
        dashboard.show_performance_analysis()
    elif args.view == "recommendations":
        dashboard.show_recommendations()
    elif args.view == "trends":
        dashboard.show_time_series(args.hours)


if __name__ == "__main__":
    main()
