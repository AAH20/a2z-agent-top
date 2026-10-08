"""
Nous Hermes Core Adapter.
Integrates with AAH20/hermes-matrix-adapter and a2z-hermes-agent to monitor cognitive turns, skills, and ActionLedger receipts.
"""

from __future__ import annotations

import time
import hashlib
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class HermesSession:
    """Active cognitive session telemetry for a Nous Hermes instance."""
    session_id: str
    agent_name: str
    current_turn: int
    active_skills: List[str]
    memory_query_ms: float
    action_ledger_hash: str
    receipts_verified_count: int
    total_tool_calls: int
    last_reasoning_step: str
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "current_turn": self.current_turn,
            "active_skills": self.active_skills,
            "memory_query_ms": round(self.memory_query_ms, 2),
            "action_ledger_hash": self.action_ledger_hash,
            "receipts_verified_count": self.receipts_verified_count,
            "total_tool_calls": self.total_tool_calls,
            "last_reasoning_step": self.last_reasoning_step,
            "uptime_sec": round(time.time() - self.created_at, 1),
        }


class HermesAdapter:
    """
    Adapter for Nous Hermes Agent and sovereign skill matrix (github.com/AAH20/hermes-matrix-adapter).
    Probes skill execution latency and ActionLedger cryptographic consistency.
    """

    def __init__(self, demo_mode: bool = True):
        self.demo_mode = demo_mode
        self._lock = threading.Lock()
        self._sessions: Dict[str, HermesSession] = {}
        if self.demo_mode:
            self._seed_demo_sessions()

    def _seed_demo_sessions(self) -> None:
        """Seed representative Hermes agent cognitive sessions."""
        now = time.time()
        self._sessions = {
            "hermes-sess-01": HermesSession(
                session_id="hermes-sess-01",
                agent_name="hermes-lead-arch",
                current_turn=18,
                active_skills=["arch_design", "sovereign_memory", "system_audit"],
                memory_query_ms=1.45,
                action_ledger_hash="sha256:8f2a1b9c7d4e3f2a1b9c7d4e3f2a1b9c7d4e3f2a1b9c7d4e3f2a1b9c7d4e3f2a",
                receipts_verified_count=18,
                total_tool_calls=24,
                last_reasoning_step="Evaluating Hoare invariant pre-conditions on mutating DAG",
                created_at=now - 240,
            ),
            "hermes-sess-02": HermesSession(
                session_id="hermes-sess-02",
                agent_name="hermes-matrix-worker",
                current_turn=45,
                active_skills=["cyber_audit", "sql_inspector", "crypto_sign"],
                memory_query_ms=0.88,
                action_ledger_hash="sha256:4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b",
                receipts_verified_count=45,
                total_tool_calls=62,
                last_reasoning_step="Validating RFC 8785 canonical JSON against Merkle root",
                created_at=now - 190,
            ),
        }

    def get_sessions(self) -> List[HermesSession]:
        with self._lock:
            return list(self._sessions.values())

    def get_session(self, session_id: str) -> Optional[HermesSession]:
        with self._lock:
            return self._sessions.get(session_id)
