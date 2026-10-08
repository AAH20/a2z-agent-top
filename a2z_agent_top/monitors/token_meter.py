"""
Swarm Economics & Token Burn Meter.
Calculates token burn velocity, cost burn rate ($/hr), and context window saturation.
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class TokenVelocity:
    """Real-time token burn and economic velocity metrics."""
    tokens_per_second: float = 0.0
    total_tokens_consumed: int = 0
    cost_per_hour_usd: float = 0.0
    total_cost_usd: float = 0.0
    avg_context_saturation_pct: float = 0.0
    peak_tokens_per_second: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tokens_per_second": round(self.tokens_per_second, 1),
            "total_tokens_consumed": self.total_tokens_consumed,
            "cost_per_hour_usd": round(self.cost_per_hour_usd, 3),
            "total_cost_usd": round(self.total_cost_usd, 4),
            "avg_context_saturation_pct": round(self.avg_context_saturation_pct, 1),
            "peak_tokens_per_second": round(self.peak_tokens_per_second, 1),
        }


class SwarmTokenMeter:
    """
    Tracks aggregate token consumption, burn rates, and financial run rates.
    Defaults to industry-standard blended LLM pricing ($3.00 / 1M prompt tokens, $15.00 / 1M completion tokens).
    """

    # Blended price per token: approx $0.000006 per token ($6 per 1M tokens)
    DEFAULT_BLENDED_COST_PER_TOKEN = 0.000006

    def __init__(self, blended_cost_per_token: float = DEFAULT_BLENDED_COST_PER_TOKEN):
        self.cost_per_token = blended_cost_per_token
        self._lock = threading.Lock()
        self._agent_tokens: Dict[int, int] = {}
        self._last_sample_time: float = time.time()
        self._tokens_in_sample: int = 0
        self._current_tps: float = 0.0
        self._peak_tps: float = 0.0
        self._cumulative_tokens: int = 0

    def record_agent_tokens(self, pid: int, new_tokens: int) -> None:
        """Record newly generated or consumed tokens for an agent."""
        with self._lock:
            self._agent_tokens[pid] = self._agent_tokens.get(pid, 0) + new_tokens
            self._tokens_in_sample += new_tokens
            self._cumulative_tokens += new_tokens

    def tick(self, active_pids: List[int], avg_ctx_pct: float = 0.0) -> TokenVelocity:
        """
        Clock tick to compute instantaneous velocity and cost rates.
        Called once per UI render cycle or sampling period.
        """
        with self._lock:
            now = time.time()
            elapsed = max(0.001, now - self._last_sample_time)

            self._current_tps = self._tokens_in_sample / elapsed
            if self._current_tps > self._peak_tps:
                self._peak_tps = self._current_tps

            # Reset window
            self._last_sample_time = now
            self._tokens_in_sample = 0

            # Cost per hour = tokens_per_sec * 3600 * cost_per_token
            cost_per_hour = self._current_tps * 3600.0 * self.cost_per_token
            total_cost = self._cumulative_tokens * self.cost_per_token

            return TokenVelocity(
                tokens_per_second=self._current_tps,
                total_tokens_consumed=self._cumulative_tokens,
                cost_per_hour_usd=cost_per_hour,
                total_cost_usd=total_cost,
                avg_context_saturation_pct=avg_ctx_pct,
                peak_tokens_per_second=self._peak_tps,
            )

    def simulate_tick(self, num_agents: int) -> TokenVelocity:
        """Generate realistic synthetic token velocity for testing/demo."""
        import random
        synthetic_tokens = int(num_agents * random.uniform(85, 240))
        with self._lock:
            self._tokens_in_sample += synthetic_tokens
            self._cumulative_tokens += synthetic_tokens
            self._current_tps = synthetic_tokens * 1.5
            if self._current_tps > self._peak_tps:
                self._peak_tps = self._current_tps

            cost_per_hour = self._current_tps * 3600.0 * self.cost_per_token
            total_cost = self._cumulative_tokens * self.cost_per_token

            return TokenVelocity(
                tokens_per_second=self._current_tps,
                total_tokens_consumed=self._cumulative_tokens,
                cost_per_hour_usd=cost_per_hour,
                total_cost_usd=total_cost,
                avg_context_saturation_pct=random.uniform(45.0, 72.0),
                peak_tokens_per_second=self._peak_tps,
            )
