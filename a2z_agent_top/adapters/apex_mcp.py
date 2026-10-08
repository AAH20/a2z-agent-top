"""
Apex MCP Gateway Kernel Adapter.
Integrates with AAH20/apex-mcp-gateway-kernel and agent-schema-firewall.
Tracks Alien's Trick knapsack compression, Radix LCP cache hits, and Link-Cut Tree deadlock defusals.
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class McpKernelTelemetry:
    """Telemetry metrics emitted by Apex MCP Gateway Kernel."""
    original_schema_tokens: int
    pruned_schema_tokens: int
    radix_lcp_hit_pct: float
    lct_active_locks: int
    lct_deadlocks_defused: int
    swar_distilled_observations: int
    blocked_tool_calls: int
    active_mcp_servers: int
    average_latency_ms: float

    @property
    def knapsack_reduction_pct(self) -> float:
        if self.original_schema_tokens <= 0:
            return 0.0
        saved = self.original_schema_tokens - self.pruned_schema_tokens
        return (saved / self.original_schema_tokens) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_schema_tokens": self.original_schema_tokens,
            "pruned_schema_tokens": self.pruned_schema_tokens,
            "knapsack_reduction_pct": round(self.knapsack_reduction_pct, 1),
            "radix_lcp_hit_pct": round(self.radix_lcp_hit_pct, 1),
            "lct_active_locks": self.lct_active_locks,
            "lct_deadlocks_defused": self.lct_deadlocks_defused,
            "swar_distilled_observations": self.swar_distilled_observations,
            "blocked_tool_calls": self.blocked_tool_calls,
            "active_mcp_servers": self.active_mcp_servers,
            "average_latency_ms": round(self.average_latency_ms, 2),
        }


class ApexMcpKernelAdapter:
    """
    Adapter for Apex MCP Gateway Kernel (github.com/AAH20/apex-mcp-gateway-kernel).
    Monitors algorithmic tool routing, prefix cache hits, and dynamic firewall rules.
    """

    def __init__(self, demo_mode: bool = True):
        self.demo_mode = demo_mode
        self._lock = threading.Lock()
        self._telemetry = McpKernelTelemetry(
            original_schema_tokens=102400,
            pruned_schema_tokens=4250,
            radix_lcp_hit_pct=88.4,
            lct_active_locks=4,
            lct_deadlocks_defused=2,
            swar_distilled_observations=184,
            blocked_tool_calls=1,
            active_mcp_servers=6,
            average_latency_ms=1.25,
        )

    def get_telemetry(self) -> McpKernelTelemetry:
        with self._lock:
            return self._telemetry

    def update_telemetry(
        self,
        orig_tokens: Optional[int] = None,
        pruned_tokens: Optional[int] = None,
        lcp_hit: Optional[float] = None,
        deadlocks: Optional[int] = None,
        blocked: Optional[int] = None,
    ) -> None:
        with self._lock:
            if orig_tokens is not None:
                self._telemetry.original_schema_tokens = orig_tokens
            if pruned_tokens is not None:
                self._telemetry.pruned_schema_tokens = pruned_tokens
            if lcp_hit is not None:
                self._telemetry.radix_lcp_hit_pct = lcp_hit
            if deadlocks is not None:
                self._telemetry.lct_deadlocks_defused += deadlocks
            if blocked is not None:
                self._telemetry.blocked_tool_calls += blocked
