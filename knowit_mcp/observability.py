"""
AI Observability Module for Token Usage, Cost Tracking, and Performance Metrics
"""
import json
import inspect
import time
import logging
import os
from hashlib import sha256
from datetime import datetime
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass, asdict, field
from functools import wraps
from pathlib import Path
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


UNKNOWN_CLIENT_ID = "unknown_client"
UNKNOWN_PROMPT_ID = "unknown_prompt"
CLIENT_ID_KEYS = ("client_id", "client_name", "client", "user_id")
PROMPT_ID_KEYS = ("prompt_id", "conversation_id", "request_id", "trace_id")
PROMPT_TEXT_KEYS = ("prompt", "user_prompt", "question", "query", "sql", "message")
METADATA_INPUT_KEYS = set(CLIENT_ID_KEYS + PROMPT_ID_KEYS + PROMPT_TEXT_KEYS + ("model",))


def _clean_text(value: Any) -> Optional[str]:
    """Return a stripped string value, or None when it is empty/missing."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _json_safe(value: Any) -> Any:
    """Convert values to JSON-safe structures without losing useful context."""
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def _stable_prompt_id(source: str) -> str:
    """Build a stable prompt id for calls that do not provide one."""
    if not source:
        return UNKNOWN_PROMPT_ID
    digest = sha256(source.encode("utf-8")).hexdigest()[:16]
    return f"prompt-{digest}"


def _metric_to_dict(metric: Any) -> Dict[str, Any]:
    if isinstance(metric, dict):
        return metric
    return metric.to_dict()


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
    client_id: str = UNKNOWN_CLIENT_ID
    prompt_id: str = UNKNOWN_PROMPT_ID
    prompt_text: Optional[str] = None
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
            "client_id": self.client_id,
            "prompt_id": self.prompt_id,
            "prompt_text": self.prompt_text,
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
    
    def __init__(self, storage_path: str = "metrics.jsonl"):
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
            result[interaction_id] = _metric_to_dict(metric)
        return result
    
    def get_summary(self, include_prompt_breakdown: bool = False) -> Dict[str, Any]:
        """Get summary statistics"""
        if not self.metrics:
            summary = {
                "total_interactions": 0,
                "total_tokens_used": 0,
                "total_estimated_cost": 0.0,
                "average_latency_ms": 0.0,
                "success_rate": 0.0,
                "by_tool": {},
            }
            if include_prompt_breakdown:
                summary["by_client_prompt"] = {}
            return summary
        
        metrics_list = [_metric_to_dict(m) for m in self.metrics.values()]
        summary = self._summarize_metrics(metrics_list)
        if include_prompt_breakdown:
            summary["by_client_prompt"] = self.get_prompt_summary()["by_client"]
        return summary

    def get_prompt_summary(
        self,
        client_id: Optional[str] = None,
        prompt_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get metrics grouped by client and prompt."""
        metrics_list = [_metric_to_dict(m) for m in self.metrics.values()]
        grouped_metrics = []

        for metric in metrics_list:
            metadata = self._get_prompt_metadata(metric)
            if client_id and metadata["client_id"] != client_id:
                continue
            if prompt_id and metadata["prompt_id"] != prompt_id:
                continue

            metric_with_metadata = dict(metric)
            metric_with_metadata.update(metadata)
            grouped_metrics.append(metric_with_metadata)

        summary = self._summarize_metrics(grouped_metrics)
        summary["total_clients"] = len({m["client_id"] for m in grouped_metrics})
        summary["total_prompts"] = len(
            {(m["client_id"], m["prompt_id"]) for m in grouped_metrics}
        )
        summary["by_client"] = self._get_summary_by_client_prompt(grouped_metrics)
        return summary

    def _summarize_metrics(self, metrics_list) -> Dict[str, Any]:
        """Summarize a list of metrics without changing its grouping."""
        if not metrics_list:
            return {
                "total_interactions": 0,
                "total_tokens_used": 0,
                "total_estimated_cost": 0.0,
                "average_latency_ms": 0.0,
                "success_rate": 0.0,
                "by_tool": {},
            }

        total_interactions = len(metrics_list)
        total_tokens = sum(m.get("tokens", {}).get("total_tokens", 0) for m in metrics_list)
        total_cost = sum(m.get("costs", {}).get("total_cost", 0.0) for m in metrics_list)
        avg_latency = (
            sum(m.get("performance", {}).get("request_latency_ms", 0.0) for m in metrics_list)
            / total_interactions
        )
        success_count = sum(
            1 for m in metrics_list if m.get("performance", {}).get("success", False)
        )
        success_rate = (success_count / total_interactions * 100) if total_interactions else 0

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
            tool = m.get("tool_name", "unknown_tool")
            if tool not in tool_stats:
                tool_stats[tool] = {
                    "calls": 0,
                    "total_tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_cost": 0.0,
                    "avg_latency_ms": 0.0,
                    "failures": 0,
                }
            
            tokens = m.get("tokens", {})
            costs = m.get("costs", {})
            performance = m.get("performance", {})
            tool_stats[tool]["calls"] += 1
            tool_stats[tool]["total_tokens"] += tokens.get("total_tokens", 0)
            tool_stats[tool]["input_tokens"] += tokens.get("input_tokens", 0)
            tool_stats[tool]["output_tokens"] += tokens.get("output_tokens", 0)
            tool_stats[tool]["total_cost"] += costs.get("total_cost", 0.0)
            tool_stats[tool]["avg_latency_ms"] += performance.get("request_latency_ms", 0.0)
            if not performance.get("success", False):
                tool_stats[tool]["failures"] += 1
        
        # Calculate averages
        for tool in tool_stats:
            tool_stats[tool]["avg_latency_ms"] = round(
                tool_stats[tool]["avg_latency_ms"] / tool_stats[tool]["calls"], 2
            )
            tool_stats[tool]["total_cost"] = round(tool_stats[tool]["total_cost"], 4)
        
        return tool_stats

    def _get_summary_by_client_prompt(self, metrics_list) -> Dict[str, Any]:
        """Get summary grouped first by client, then by prompt."""
        grouped_by_client = {}
        grouped_by_prompt = {}
        prompt_texts = {}

        for metric in metrics_list:
            client_id = metric["client_id"]
            prompt_id = metric["prompt_id"]
            grouped_by_client.setdefault(client_id, []).append(metric)
            grouped_by_prompt.setdefault((client_id, prompt_id), []).append(metric)
            if metric.get("prompt_text") and (client_id, prompt_id) not in prompt_texts:
                prompt_texts[(client_id, prompt_id)] = metric["prompt_text"]

        client_stats = {}
        for client_id, client_metrics in sorted(grouped_by_client.items()):
            client_summary = self._summarize_metrics(client_metrics)
            client_prompts = {
                key[1]: prompt_metrics
                for key, prompt_metrics in grouped_by_prompt.items()
                if key[0] == client_id
            }

            prompt_stats = {}
            for prompt_key, prompt_metrics in sorted(client_prompts.items()):
                prompt_summary = self._summarize_metrics(prompt_metrics)
                prompt_text = prompt_texts.get((client_id, prompt_key))
                prompt_summary.update(
                    {
                        "prompt_id": prompt_key,
                        "prompt_text": prompt_text,
                        "prompt_preview": self._preview_text(prompt_text),
                        "interaction_ids": [
                            m.get("interaction_id") for m in prompt_metrics
                        ],
                    }
                )
                prompt_stats[prompt_key] = prompt_summary

            client_summary["total_prompts"] = len(prompt_stats)
            client_summary["prompts"] = prompt_stats
            client_stats[client_id] = client_summary

        return client_stats

    def _get_prompt_metadata(self, metric: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve client/prompt metadata, including legacy metrics."""
        client_id = (
            _clean_text(metric.get("client_id"))
            or self._extract_input_value(metric, CLIENT_ID_KEYS)
            or _clean_text(os.getenv("MCP_CLIENT_ID"))
            or UNKNOWN_CLIENT_ID
        )

        prompt_text = (
            _clean_text(metric.get("prompt_text"))
            or self._extract_input_value(metric, PROMPT_TEXT_KEYS)
        )
        prompt_id = (
            _clean_text(metric.get("prompt_id"))
            or self._extract_input_value(metric, PROMPT_ID_KEYS)
        )

        if not prompt_id or prompt_id == UNKNOWN_PROMPT_ID:
            prompt_id = _stable_prompt_id(
                prompt_text or self._canonical_tool_input(metric)
            )

        return {
            "client_id": client_id,
            "prompt_id": prompt_id,
            "prompt_text": prompt_text,
        }

    def _extract_input_value(
        self, metric: Dict[str, Any], keys: tuple[str, ...]
    ) -> Optional[str]:
        """Extract a metadata value from stored tool inputs."""
        tool_input = metric.get("tool_input", {})
        if not isinstance(tool_input, dict):
            return None

        kwargs = tool_input.get("kwargs", {})
        if isinstance(kwargs, dict):
            for key in keys:
                value = _clean_text(kwargs.get(key))
                if value:
                    return value

        return None

    def _canonical_tool_input(self, metric: Dict[str, Any]) -> str:
        """Build a stable fallback identity from the tool call input."""
        tool_input = metric.get("tool_input", {})
        kwargs = {}
        args = None

        if isinstance(tool_input, dict):
            raw_kwargs = tool_input.get("kwargs", {})
            if isinstance(raw_kwargs, dict):
                kwargs = {
                    key: _json_safe(value)
                    for key, value in raw_kwargs.items()
                    if key not in METADATA_INPUT_KEYS
                }
            args = tool_input.get("args")

        source = {
            "tool_name": metric.get("tool_name", "unknown_tool"),
            "args": args,
            "kwargs": kwargs,
        }
        return json.dumps(source, sort_keys=True, default=str)

    def _preview_text(self, text: Optional[str], max_length: int = 120) -> Optional[str]:
        """Return a compact prompt preview for dashboard/export views."""
        if not text:
            return None
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."


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
    output_tokens: Optional[int] = None,
    model_parameter: str = "model",
    client_parameter: str = "client_id",
    prompt_parameter: str = "prompt",
    prompt_id_parameter: str = "prompt_id",
):
    """
    Decorator to track tool calls with observability metrics
    
    Args:
        model: Model name for cost calculation
        input_tokens: Override input tokens (if not provided, will be estimated)
        output_tokens: Override output tokens (if not provided, will be estimated)
        model_parameter: Function argument name that can override the model
        client_parameter: Function argument name used for client identity
        prompt_parameter: Function argument name used for prompt text
        prompt_id_parameter: Function argument name used for prompt identity
    """
    def decorator(func: Callable) -> Callable:
        func_signature = inspect.signature(func)

        def resolve_argument(args, kwargs, parameter_name: str, aliases=()) -> Optional[Any]:
            try:
                bound_args = func_signature.bind_partial(*args, **kwargs)
                arguments = bound_args.arguments
            except TypeError:
                arguments = kwargs

            for key in (parameter_name, *aliases):
                if key in arguments and arguments[key] is not None:
                    return arguments[key]
                if key in kwargs and kwargs[key] is not None:
                    return kwargs[key]

            return None

        def resolve_model(args, kwargs) -> str:
            runtime_model = resolve_argument(args, kwargs, model_parameter)

            return str(runtime_model or model)

        def resolve_prompt_metadata(args, kwargs) -> Dict[str, Optional[str]]:
            client_id = (
                _clean_text(resolve_argument(args, kwargs, client_parameter, CLIENT_ID_KEYS))
                or _clean_text(os.getenv("MCP_CLIENT_ID"))
                or UNKNOWN_CLIENT_ID
            )
            prompt_text = _clean_text(
                resolve_argument(args, kwargs, prompt_parameter, PROMPT_TEXT_KEYS)
            )
            prompt_id = _clean_text(
                resolve_argument(args, kwargs, prompt_id_parameter, PROMPT_ID_KEYS)
            )

            if not prompt_id:
                fallback_source = prompt_text
                if not fallback_source:
                    try:
                        bound_args = func_signature.bind_partial(*args, **kwargs)
                        cleaned_arguments = {
                            key: _json_safe(value)
                            for key, value in bound_args.arguments.items()
                            if key not in METADATA_INPUT_KEYS
                        }
                    except TypeError:
                        cleaned_arguments = {
                            key: _json_safe(value)
                            for key, value in kwargs.items()
                            if key not in METADATA_INPUT_KEYS
                        }

                    fallback_source = json.dumps(
                        {
                            "tool_name": func.__name__,
                            "arguments": cleaned_arguments,
                        },
                        sort_keys=True,
                        default=str,
                    )
                prompt_id = _stable_prompt_id(fallback_source)

            return {
                "client_id": client_id,
                "prompt_id": prompt_id,
                "prompt_text": prompt_text,
            }

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            selected_model = resolve_model(args, kwargs)
            prompt_metadata = resolve_prompt_metadata(args, kwargs)

            # Create metrics for this interaction
            metric = InteractionMetrics()
            metric.tool_name = func.__name__
            metric.client_id = prompt_metadata["client_id"]
            metric.prompt_id = prompt_metadata["prompt_id"]
            metric.prompt_text = prompt_metadata["prompt_text"]
            metric.tool_input = {
                "args": str(args),
                "kwargs": {key: _json_safe(value) for key, value in kwargs.items()},
            }
            metric.costs.model = selected_model
            
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
                    selected_model,
                    metric.tokens.input_tokens,
                    metric.tokens.output_tokens
                )
                pricing = PricingConfig.get_pricing(selected_model)
                metric.costs.input_cost = (
                    metric.tokens.input_tokens / 1_000_000
                ) * pricing["input"]
                metric.costs.output_cost = (
                    metric.tokens.output_tokens / 1_000_000
                ) * pricing["output"]
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


def get_observability_summary(include_prompt_breakdown: bool = False) -> Dict[str, Any]:
    """Get current observability summary"""
    store = get_metrics_store()
    return store.get_summary(include_prompt_breakdown=include_prompt_breakdown)


def get_prompt_metrics_summary(
    client_id: Optional[str] = None,
    prompt_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Get metrics grouped by client and prompt."""
    store = get_metrics_store()
    return store.get_prompt_summary(client_id=client_id, prompt_id=prompt_id)


def export_metrics(
    format: str = "json",
    filepath: Optional[str] = None,
    scope: str = "summary",
) -> str:
    """
    Export metrics in different formats
    
    Args:
        format: 'json' or 'csv'
        filepath: Optional path to save to file
        scope: 'summary' for cumulative metrics or 'prompts' for client/prompt metrics
    
    Returns:
        Formatted metrics string
    """
    store = get_metrics_store()
    if scope in {"prompts", "client_prompts", "by_prompt"}:
        metrics = store.get_prompt_summary()
    else:
        metrics = store.get_summary()
    
    if format == "json":
        output = json.dumps(metrics, indent=2)
    elif format == "csv":
        if scope in {"prompts", "client_prompts", "by_prompt"}:
            lines = [
                "client_id,prompt_id,prompt_preview,total_calls,input_tokens,"
                "output_tokens,total_tokens,total_cost,avg_latency_ms,success_rate"
            ]
            for exported_client_id, client_stats in metrics.get("by_client", {}).items():
                for exported_prompt_id, prompt_stats in client_stats.get("prompts", {}).items():
                    prompt_preview = (prompt_stats.get("prompt_preview") or "").replace('"', '""')
                    lines.append(
                        f'"{exported_client_id}","{exported_prompt_id}","{prompt_preview}",'
                        f"{prompt_stats['total_interactions']},"
                        f"{sum(t['input_tokens'] for t in prompt_stats['by_tool'].values())},"
                        f"{sum(t['output_tokens'] for t in prompt_stats['by_tool'].values())},"
                        f"{prompt_stats['total_tokens_used']},"
                        f"{prompt_stats['total_estimated_cost']},"
                        f"{prompt_stats['average_latency_ms']},"
                        f"{prompt_stats['success_rate']}"
                    )
        else:
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
