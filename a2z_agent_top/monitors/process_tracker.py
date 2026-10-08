"""
Agent Swarm Process Discovery and Tracking Engine.
Discovers and tracks AI agent processes across Paperclip, Hermes, Codex, LangGraph, and MCP runtimes.
"""

from __future__ import annotations

import os
import sys
import time
import subprocess
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class AgentState(str, Enum):
    """Lifecycle states of an autonomous agent process."""
    DISPATCHED = "DISPATCHED"
    THINKING = "THINKING"
    TOOL_EXEC = "TOOL_EXEC"
    PAUSED = "PAUSED"
    DEADLOCKED = "DEADLOCKED"
    ROLLING_BACK = "ROLLING_BACK"
    TERMINATED = "TERMINATED"


@dataclass
class ProcessInfo:
    """Detailed telemetry record for an agent or MCP tool worker."""
    pid: int
    name: str
    ppid: int = 1
    state: AgentState = AgentState.THINKING
    cpu_pct: float = 0.0
    mem_mb: float = 0.0
    turns: int = 0
    context_pct: float = 0.0
    framework: str = "custom"
    last_tool: str = "none"
    blast_radius: float = 0.0
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pid": self.pid,
            "name": self.name,
            "ppid": self.ppid,
            "state": self.state.value,
            "cpu_pct": round(self.cpu_pct, 1),
            "mem_mb": round(self.mem_mb, 1),
            "turns": self.turns,
            "context_pct": round(self.context_pct, 1),
            "framework": self.framework,
            "last_tool": self.last_tool,
            "blast_radius": round(self.blast_radius, 2),
            "uptime_sec": round(time.time() - self.created_at, 1),
            "metadata": self.metadata,
        }


class AgentProcessTracker:
    """
    Thread-safe process tracker for autonomous agent swarms.
    Sniffs local OS processes and maintains real-time lifecycle status.
    """

    KNOWN_FRAMEWORKS = [
        ("paperclip", "Paperclip"),
        ("hermes", "Nous Hermes"),
        ("codex", "Codex / Coding Agent"),
        ("claude", "Claude Code"),
        ("langgraph", "LangGraph"),
        ("autogen", "AutoGen"),
        ("crewai", "CrewAI"),
        ("mcp", "Apex MCP Gateway"),
    ]

    def __init__(self, demo_mode: bool = False):
        self.demo_mode = demo_mode
        self._lock = threading.RLock()
        self._processes: Dict[int, ProcessInfo] = {}
        self._history: List[Dict[str, Any]] = []

        if self.demo_mode:
            self._seed_demo_swarm()

    def _seed_demo_swarm(self) -> None:
        """Seed representative demo swarm across major frameworks."""
        now = time.time()
        demo_data = [
            ProcessInfo(
                pid=41021,
                name="paperclip-lead-arch",
                ppid=1024,
                state=AgentState.THINKING,
                cpu_pct=14.2,
                mem_mb=420.5,
                turns=18,
                context_pct=42.5,
                framework="Paperclip",
                last_tool="read_file",
                blast_radius=3.5,
                created_at=now - 240,
                metadata={"dept": "Architecture", "ticket": "TICK-804", "model": "claude-3-7-sonnet"},
            ),
            ProcessInfo(
                pid=41022,
                name="hermes-matrix-worker",
                ppid=41021,
                state=AgentState.TOOL_EXEC,
                cpu_pct=28.7,
                mem_mb=680.1,
                turns=45,
                context_pct=68.9,
                framework="Nous Hermes",
                last_tool="execute_sql",
                blast_radius=12.4,
                created_at=now - 190,
                metadata={"skills": ["cyber_audit", "sql_inspector"], "receipt_hash": "sha256:7b9f..."},
            ),
            ProcessInfo(
                pid=41023,
                name="codex-ast-refactor",
                ppid=41021,
                state=AgentState.THINKING,
                cpu_pct=84.3,
                mem_mb=1120.0,
                turns=32,
                context_pct=81.2,
                framework="Codex",
                last_tool="ast_patch",
                blast_radius=6.8,
                created_at=now - 120,
                metadata={"diff_hunks": 14, "tests_passing": "42/45", "branch": "feature/kernel-v2"},
            ),
            ProcessInfo(
                pid=41024,
                name="apex-mcp-gateway-router",
                ppid=1,
                state=AgentState.TOOL_EXEC,
                cpu_pct=6.5,
                mem_mb=210.4,
                turns=312,
                context_pct=15.0,
                framework="Apex MCP",
                last_tool="radix_lcp_route",
                blast_radius=0.0,
                created_at=now - 600,
                metadata={"knapsack_tokens": "102k->4.2k", "cache_hit": "88.4%", "lct_locks": 3},
            ),
            ProcessInfo(
                pid=41025,
                name="rogue-recursive-fuzzer",
                ppid=41021,
                state=AgentState.DEADLOCKED,
                cpu_pct=99.1,
                mem_mb=1840.2,
                turns=142,
                context_pct=94.5,
                framework="LangGraph",
                last_tool="rm_recursive",
                blast_radius=89.4,
                created_at=now - 85,
                metadata={"alert": "High Blast Radius (Ceiling: 25.0)", "lct_cycle": True},
            ),
        ]
        with self._lock:
            for p in demo_data:
                self._processes[p.pid] = p

    def scan_system_processes(self) -> List[ProcessInfo]:
        """
        Scan host operating system for running agent processes and MCP servers.
        Uses POSIX 'ps' command with cross-platform flags.
        """
        if self.demo_mode:
            return self.get_all_processes()

        discovered: List[ProcessInfo] = []
        try:
            # Query PID, PPID, %CPU, RSS (KB), and command line
            cmd = ["ps", "-eo", "pid,ppid,%cpu,rss,command"]
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True, timeout=1.5)
            lines = output.strip().split("\n")[1:]  # Skip header

            now = time.time()
            for line in lines:
                parts = line.strip().split(None, 4)
                if len(parts) < 5:
                    continue
                pid_str, ppid_str, cpu_str, rss_str, command = parts
                try:
                    pid = int(pid_str)
                    ppid = int(ppid_str)
                    cpu_pct = float(cpu_str)
                    mem_mb = float(rss_str) / 1024.0
                except ValueError:
                    continue

                # Check if this process matches known agent runtimes
                cmd_lower = command.lower()
                matched_framework = None
                for keyword, framework_name in self.KNOWN_FRAMEWORKS:
                    if keyword in cmd_lower:
                        matched_framework = framework_name
                        break

                if matched_framework:
                    proc_name = os.path.basename(command.split()[0])
                    # Derive or keep existing state
                    existing = self._processes.get(pid)
                    state = existing.state if existing else (
                        AgentState.TOOL_EXEC if "tool" in cmd_lower or "mcp" in cmd_lower
                        else AgentState.THINKING
                    )
                    turns = existing.turns + 1 if existing else 1
                    ctx_pct = existing.context_pct if existing else min(100.0, turns * 2.5)

                    p_info = ProcessInfo(
                        pid=pid,
                        name=proc_name,
                        ppid=ppid,
                        state=state,
                        cpu_pct=cpu_pct,
                        mem_mb=mem_mb,
                        turns=turns,
                        context_pct=ctx_pct,
                        framework=matched_framework,
                        last_tool=existing.last_tool if existing else "system_io",
                        blast_radius=existing.blast_radius if existing else 1.0,
                        created_at=existing.created_at if existing else now,
                    )
                    discovered.append(p_info)
        except Exception:
            # Fallback if ps is restricted or errors
            pass

        with self._lock:
            # Merge discovered into internal table
            for p in discovered:
                self._processes[p.pid] = p
            return list(self._processes.values())

    def register_agent(self, proc: ProcessInfo) -> None:
        """Register a new active agent into tracker."""
        with self._lock:
            self._processes[proc.pid] = proc

    def update_agent_state(self, pid: int, state: AgentState, last_tool: Optional[str] = None, blast_radius: Optional[float] = None) -> bool:
        """Update the lifecycle state of a tracked agent."""
        with self._lock:
            if pid not in self._processes:
                return False
            proc = self._processes[pid]
            proc.state = state
            if last_tool is not None:
                proc.last_tool = last_tool
            if blast_radius is not None:
                proc.blast_radius = blast_radius
            proc.turns += 1
            return True

    def get_process(self, pid: int) -> Optional[ProcessInfo]:
        """Retrieve single agent record by PID."""
        with self._lock:
            return self._processes.get(pid)

    def get_all_processes(self) -> List[ProcessInfo]:
        """Return list of all currently tracked agent processes."""
        with self._lock:
            return list(self._processes.values())

    def remove_process(self, pid: int) -> Optional[ProcessInfo]:
        """Remove a terminated agent from active tracking."""
        with self._lock:
            return self._processes.pop(pid, None)

    def total_count(self) -> int:
        """Return total active agent count."""
        with self._lock:
            return len(self._processes)
