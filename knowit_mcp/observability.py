"""
AI Observability Module for Token Usage, Cost Tracking, and Performance Metrics
"""
import json
import time
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass, asdict, field
from functools import wraps
from pathlib import Path
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """Token usage metrics"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CostMetrics:
    """Cost estimation based on model pricing"""
    model: str = "claude-3-5-sonnet"  # Default model
    input_cost: float = 0.0  # Cost for input tokens
    output_cost: float = 0.0  # Cost for output tokens
    total_cost: float = 0.0  # Total estimated cost
    currency: str = "USD"
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PerformanceMetrics:
    """Performance tracking metrics"""
    request_latency_ms: float = 0.0  # Total request time
    tool_execution_time_ms: float = 0.0  # Actual tool execution time
    tool_call_overhead_ms: float = 0.0  # MCP overhead
    number_of_retries: int = 0
    number_of_failures: int = 0
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class InteractionMetrics:
    """Complete metrics for a single interaction"""
    interaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tool_name: str = ""
    tool_input: Dict[str, Any] = field(default_factory=dict)
    tool_output: Dict[str, Any] = field(default_factory=dict)
    tokens: TokenUsage = field(default_factory=TokenUsage)
    costs: CostMetrics = field(default_factory=CostMetrics)
    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    
    def to_dict(self) -> Dict:
        return {
            "interaction_id": self.interaction_id,
            "timestamp": self.timestamp,
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "tool_output": self.tool_output,
            "tokens": self.tokens.to_dict(),
            "costs": self.costs.to_dict(),
            "performance": self.performance.to_dict(),
        }


class PricingConfig:
    """Model-specific pricing configuration (per 1M tokens)"""
    PRICING = {
        "claude-3-5-sonnet": {
            "input": 3.0,  # $3 per 1M input tokens
            "output": 15.0,  # $15 per 1M output tokens
        },
        "claude-3-opus": {
            "input": 15.0,
            "output": 75.0,
        },
        "claude-3-haiku": {
            "input": 0.25,
            "output": 1.25,
        },
        "gpt-4": {
            "input": 30.0,
            "output": 60.0,
        },
        "gpt-3.5-turbo": {
            "input": 0.5,
            "output": 1.5,
        },
    }
    
    @classmethod
    def get_pricing(cls, model: str) -> Dict[str, float]:
        """Get pricing for a model, default to claude-3-5-sonnet"""
        return cls.PRICING.get(model, cls.PRICING["claude-3-5-sonnet"])
    
    @classmethod
    def calculate_cost(cls, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost in USD"""
        pricing = cls.get_pricing(model)
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost


class MetricsStore:
    """Store and manage metrics"""
    
    def __init__(self, storage_path: str = "ai_observability/metrics.jsonl"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.metrics: Dict[str, InteractionMetrics] = {}
        self._load_existing_metrics()
    
    def _load_existing_metrics(self):
        """Load existing metrics from storage"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            interaction_id = data.get("interaction_id")
                            if interaction_id:
                                self.metrics[interaction_id] = data
            except Exception as e:
                logger.warning(f"Failed to load existing metrics: {e}")
    
    def add_metric(self, metric: InteractionMetrics):
        """Add a metric and persist to storage"""
        self.metrics[metric.interaction_id] = metric
        self._persist_metric(metric)
    
    def _persist_metric(self, metric: InteractionMetrics):
        """Persist a single metric to JSONL file"""
        try:
            with open(self.storage_path, 'a') as f:
                f.write(json.dumps(metric.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to persist metric: {e}")
    
    def get_metric(self, interaction_id: str) -> Optional[Dict]:
        """Retrieve a specific metric"""
        if interaction_id in self.metrics:
            metric = self.metrics[interaction_id]
            return metric if isinstance(metric, dict) else metric.to_dict()
        return None
    
    def get_all_metrics(self) -> Dict[str, Dict]:
        """Get all metrics"""
        result = {}
        for interaction_id, metric in self.metrics.items():
            result[interaction_id] = metric if isinstance(metric, dict) else metric.to_dict()
        return result
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        if not self.metrics:
            return {
                "total_interactions": 0,
                "total_tokens_used": 0,
                "total_estimated_cost": 0.0,
                "average_latency_ms": 0.0,
                "success_rate": 0.0,
            }
        
        metrics_list = [m if isinstance(m, dict) else m.to_dict() for m in self.metrics.values()]
        
        total_interactions = len(metrics_list)
        total_tokens = sum(m["tokens"]["total_tokens"] for m in metrics_list)
        total_cost = sum(m["costs"]["total_cost"] for m in metrics_list)
        avg_latency = sum(m["performance"]["request_latency_ms"] for m in metrics_list) / total_interactions
        success_count = sum(1 for m in metrics_list if m["performance"]["success"])
        success_rate = (success_count / total_interactions * 100) if total_interactions > 0 else 0
        
        return {
            "total_interactions": total_interactions,
            "total_tokens_used": total_tokens,
            "total_estimated_cost": round(total_cost, 4),
            "average_latency_ms": round(avg_latency, 2),
            "success_rate": round(success_rate, 2),
            "by_tool": self._get_summary_by_tool(metrics_list),
        }
    
    def _get_summary_by_tool(self, metrics_list) -> Dict[str, Any]:
        """Get summary grouped by tool"""
        tool_stats = {}
        for m in metrics_list:
            tool = m["tool_name"]
            if tool not in tool_stats:
                tool_stats[tool] = {
                    "calls": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "avg_latency_ms": 0.0,
                    "failures": 0,
                }
            
            tool_stats[tool]["calls"] += 1
            tool_stats[tool]["total_tokens"] += m["tokens"]["total_tokens"]
            tool_stats[tool]["total_cost"] += m["costs"]["total_cost"]
            tool_stats[tool]["avg_latency_ms"] += m["performance"]["request_latency_ms"]
            if not m["performance"]["success"]:
                tool_stats[tool]["failures"] += 1
        
        # Calculate averages
        for tool in tool_stats:
            tool_stats[tool]["avg_latency_ms"] = round(
                tool_stats[tool]["avg_latency_ms"] / tool_stats[tool]["calls"], 2
            )
            tool_stats[tool]["total_cost"] = round(tool_stats[tool]["total_cost"], 4)
        
        return tool_stats


# Global metrics store
_metrics_store = None


def get_metrics_store() -> MetricsStore:
    """Get or create the global metrics store"""
    global _metrics_store
    if _metrics_store is None:
        _metrics_store = MetricsStore()
    return _metrics_store


def track_tool_call(
    model: str = "claude-3-5-sonnet",
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None
):
    """
    Decorator to track tool calls with observability metrics
    
    Args:
        model: Model name for cost calculation
        input_tokens: Override input tokens (if not provided, will be estimated)
        output_tokens: Override output tokens (if not provided, will be estimated)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Create metrics for this interaction
            metric = InteractionMetrics()
            metric.tool_name = func.__name__
            metric.tool_input = {
                "args": str(args),
                "kwargs": kwargs,
            }
            metric.costs.model = model
            
            # Track performance
            start_time = time.time()
            exec_start = time.time()
            
            retries = 0
            max_retries = 3
            last_error = None
            result = None
            
            while retries <= max_retries:
                try:
                    result = func(*args, **kwargs)
                    exec_time = time.time() - exec_start
                    metric.performance.tool_execution_time_ms = exec_time * 1000
                    metric.performance.success = True
                    break
                except Exception as e:
                    retries += 1
                    last_error = e
                    if retries <= max_retries:
                        logger.warning(f"Retry {retries} for {func.__name__}: {str(e)}")
                        time.sleep(0.5 * retries)  # Exponential backoff
                    else:
                        metric.performance.success = False
                        metric.performance.error_message = str(e)
                        metric.performance.number_of_failures = 1
                        logger.error(f"Failed after {retries} retries: {str(e)}")
            
            total_time = time.time() - start_time
            metric.performance.request_latency_ms = total_time * 1000
            metric.performance.tool_call_overhead_ms = (total_time - (metric.performance.tool_execution_time_ms / 1000)) * 1000
            metric.performance.number_of_retries = max(0, retries - 1)
            
            # Process result
            if result is not None:
                metric.tool_output = result if isinstance(result, dict) else {"result": str(result)}
                
                # Estimate tokens if not provided
                if input_tokens is None:
                    # Estimate based on input size (rough: 4 chars = 1 token)
                    estimated_input = sum(len(str(v)) // 4 for v in kwargs.values())
                    metric.tokens.input_tokens = max(10, estimated_input)
                else:
                    metric.tokens.input_tokens = input_tokens
                
                if output_tokens is None:
                    # Estimate based on output size
                    estimated_output = len(json.dumps(metric.tool_output)) // 4
                    metric.tokens.output_tokens = max(10, estimated_output)
                else:
                    metric.tokens.output_tokens = output_tokens
                
                metric.tokens.total_tokens = metric.tokens.input_tokens + metric.tokens.output_tokens
                
                # Calculate costs
                total_cost = PricingConfig.calculate_cost(
                    model,
                    metric.tokens.input_tokens,
                    metric.tokens.output_tokens
                )
                metric.costs.input_cost = (metric.tokens.input_tokens / 1_000_000) * PricingConfig.get_pricing(model)["input"]
                metric.costs.output_cost = (metric.tokens.output_tokens / 1_000_000) * PricingConfig.get_pricing(model)["output"]
                metric.costs.total_cost = total_cost
            
            # Store metrics
            store = get_metrics_store()
            store.add_metric(metric)
            
            # Log summary
            logger.info(
                f"Tool: {metric.tool_name} | "
                f"Tokens: {metric.tokens.total_tokens} | "
                f"Cost: ${metric.costs.total_cost:.6f} | "
                f"Latency: {metric.performance.request_latency_ms:.2f}ms | "
                f"Success: {metric.performance.success}"
            )
            
            return result if metric.performance.success else None
        
        return wrapper
    return decorator


def estimate_tokens(text: str) -> int:
    """
    Rough estimation of tokens from text
    Uses the approximation: 1 token ≈ 4 characters
    """
    return max(1, len(text) // 4)


def get_observability_summary() -> Dict[str, Any]:
    """Get current observability summary"""
    store = get_metrics_store()
    return store.get_summary()


def export_metrics(format: str = "json", filepath: Optional[str] = None) -> str:
    """
    Export metrics in different formats
    
    Args:
        format: 'json' or 'csv'
        filepath: Optional path to save to file
    
    Returns:
        Formatted metrics string
    """
    store = get_metrics_store()
    metrics = store.get_summary()
    
    if format == "json":
        output = json.dumps(metrics, indent=2)
    elif format == "csv":
        # Simple CSV export
        lines = ["tool_name,total_calls,total_tokens,total_cost,avg_latency_ms,failures"]
        for tool, stats in metrics.get("by_tool", {}).items():
            lines.append(
                f"{tool},{stats['calls']},{stats['total_tokens']},"
                f"{stats['total_cost']},{stats['avg_latency_ms']},{stats['failures']}"
            )
        output = "\n".join(lines)
    else:
        output = str(metrics)
    
    if filepath:
        Path(filepath).write_text(output)
        logger.info(f"Metrics exported to {filepath}")
    
    return output
