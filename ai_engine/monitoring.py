"""Performance monitoring and metrics collection."""
from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class RequestMetrics:
    """Track metrics for a single request."""
    
    endpoint: str
    method: str
    start_time: float
    end_time: Optional[float] = None
    status_code: int = 200
    error: Optional[str] = None
    gemini_tokens_estimated: int = 0
    db_queries: int = 0
    rag_chunks_retrieved: int = 0
    
    @property
    def duration_ms(self) -> float:
        """Duration in milliseconds."""
        if self.end_time is None:
            return (time.time() - self.start_time) * 1000
        return (self.end_time - self.start_time) * 1000
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        data = asdict(self)
        data["duration_ms"] = self.duration_ms
        return data


class PerformanceMonitor:
    """Monitor and log performance metrics."""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.metrics_history: list[RequestMetrics] = []
    
    def start_request(self, endpoint: str, method: str = "POST") -> RequestMetrics:
        """Start tracking a request."""
        return RequestMetrics(
            endpoint=endpoint,
            method=method,
            start_time=time.time(),
        )
    
    def end_request(self, metric: RequestMetrics, status_code: int = 200, error: Optional[str] = None) -> None:
        """End tracking a request."""
        metric.end_time = time.time()
        metric.status_code = status_code
        metric.error = error
        
        self.metrics_history.append(metric)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history.pop(0)
    
    def get_stats(self) -> dict:
        """Get aggregated statistics."""
        if not self.metrics_history:
            return {
                "requests_total": 0,
                "avg_duration_ms": 0,
                "p50_duration_ms": 0,
                "p95_duration_ms": 0,
                "p99_duration_ms": 0,
                "error_rate": 0,
                "avg_gemini_tokens": 0,
            }
        
        durations = [m.duration_ms for m in self.metrics_history]
        errors = sum(1 for m in self.metrics_history if m.error)
        gemini_tokens = [m.gemini_tokens_estimated for m in self.metrics_history]
        
        durations.sort()
        
        return {
            "requests_total": len(self.metrics_history),
            "avg_duration_ms": sum(durations) / len(durations),
            "p50_duration_ms": durations[len(durations) // 2],
            "p95_duration_ms": durations[int(len(durations) * 0.95)],
            "p99_duration_ms": durations[int(len(durations) * 0.99)],
            "error_rate": (errors / len(self.metrics_history)) * 100,
            "avg_gemini_tokens": sum(gemini_tokens) / len(gemini_tokens) if gemini_tokens else 0,
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
        }
    
    def get_endpoint_stats(self, endpoint: str) -> dict:
        """Get stats for a specific endpoint."""
        endpoint_metrics = [m for m in self.metrics_history if m.endpoint == endpoint]
        
        if not endpoint_metrics:
            return {}
        
        durations = [m.duration_ms for m in endpoint_metrics]
        durations.sort()
        
        return {
            "endpoint": endpoint,
            "count": len(endpoint_metrics),
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "p95_duration_ms": durations[int(len(durations) * 0.95)] if len(durations) > 0 else 0,
        }


# Global monitor instance
_monitor: Optional[PerformanceMonitor] = None


def get_monitor() -> PerformanceMonitor:
    """Get or create the global performance monitor."""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor


def estimate_gemini_tokens(text: str) -> int:
    """Estimate tokens for Gemini (rough approximation: 1 token ~= 4 chars)."""
    return max(1, len(text) // 4)
