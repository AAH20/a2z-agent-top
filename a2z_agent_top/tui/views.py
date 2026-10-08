"""
TUI View Renderers for a2z-agent-top.
Provides structured visual components for Dashboard, MCP Gateway, Paperclip, Codex, Hermes, and GPU.
"""

from __future__ import annotations

import math
from typing import List, Dict, Optional, Any

from a2z_agent_top.monitors.process_tracker import ProcessInfo, AgentState
from a2z_agent_top.monitors.token_meter import TokenVelocity
from a2z_agent_top.monitors.nvml_gpu import GpuMetrics
from a2z_agent_top.adapters.paperclip import EmployeeAgent
from a2z_agent_top.adapters.hermes import HermesSession
from a2z_agent_top.adapters.codex import CodexHunk
from a2z_agent_top.adapters.apex_mcp import McpKernelTelemetry


def make_bar(percent: float, width: int = 16) -> str:
    """Generate a high-contrast progress bar, e.g. [████████░░░░░░░░] 50.0%"""
    pct = max(0.0, min(100.0, percent))
    filled_len = int(round(width * pct / 100.0))
    bar = "█" * filled_len + "░" * (width - filled_len)
    return f"[{bar}] {pct:5.1f}%"


class DashboardView:
    """Renders main agent swarm process table and summary header."""

    @staticmethod
    def render_header(
        total_agents: int,
        active_count: int,
        paused_count: int,
        token_vel: TokenVelocity,
        gpu_summary: str,
        width: int = 110,
    ) -> List[str]:
        lines = [
            "=" * width,
            f" a2z-agent-top v1.0.0 — Unified Agent Swarm Console | Apex Growth Systems LLC (a2zsoc.com) ",
            "-" * width,
            f" Swarm Status: {total_agents} Agents ({active_count} Active, {paused_count} Paused) | "
            f"Token Velocity: {token_vel.tokens_per_second:6.1f} tok/s | Burn Rate: ${token_vel.cost_per_hour_usd:6.2f}/hr | "
            f"Total: {token_vel.total_tokens_consumed:,} tok (${token_vel.total_cost_usd:5.3f})",
            f" Hardware: {gpu_summary} | Context Saturation: {make_bar(token_vel.avg_context_saturation_pct, 12)}",
            "=" * width,
        ]
        return lines

    @staticmethod
    def render_table(
        processes: List[ProcessInfo],
        selected_index: int = 0,
        width: int = 110,
    ) -> List[str]:
        lines = []
        # Header row
        header = f" {'PID':<6} {'NAME':<24} {'FRAMEWORK':<14} {'STATE':<11} {'CPU%':<6} {'MEM':<8} {'TURNS':<6} {'CTX%':<6} {'BLAST':<6} {'LAST TOOL':<16}"
        lines.append(header)
        lines.append("-" * width)

        for idx, p in enumerate(processes):
            prefix = "▶" if idx == selected_index else " "
            mem_str = f"{p.mem_mb:.1f}MB"
            cpu_str = f"{p.cpu_pct:.1f}%"
            blast_str = f"{p.blast_radius:.1f}"

            row = (
                f"{prefix}{p.pid:<6} {p.name[:23]:<24} {p.framework[:13]:<14} {p.state.value:<11} "
                f"{cpu_str:<6} {mem_str:<8} {p.turns:<6} {p.context_pct:4.1f}% {blast_str:<6} {p.last_tool[:15]:<16}"
            )
            lines.append(row)

        if not processes:
            lines.append(" (No active agent processes detected. Press [d] to reload or run demo mode.)")

        return lines


class McpView:
    """Renders Apex MCP Gateway Kernel algorithmic telemetry."""

    @staticmethod
    def render(telemetry: McpKernelTelemetry, width: int = 110) -> List[str]:
        lines = [
            "=" * width,
            " APEX MCP GATEWAY KERNEL TELEMETRY (AAH20/apex-mcp-gateway-kernel) ",
            "=" * width,
            f" Knapsack Pruning (Alien's Trick WQS): {telemetry.original_schema_tokens:,} -> {telemetry.pruned_schema_tokens:,} tokens "
            f"({make_bar(telemetry.knapsack_reduction_pct, 14)} Reduction)",
            f" Radix Prefix-Cache LCP Hit Rate:     {make_bar(telemetry.radix_lcp_hit_pct, 18)}",
            f" Link-Cut Tree (LCT) Locks:           {telemetry.lct_active_locks} Active Leases | {telemetry.lct_deadlocks_defused} Circular Deadlocks Auto-Defused",
            f" SWAR Observation Distiller:          {telemetry.swar_distilled_observations} High-SNR Distillations Executed",
            f" Dynamic Schema Firewall:             {telemetry.blocked_tool_calls} Rogue / Shadowed Tools Blocked",
            f" MCP Mesh Servers:                    {telemetry.active_mcp_servers} Connected | Avg Latency: {telemetry.average_latency_ms:.2f} ms",
            "-" * width,
            " Hotkey: Press [d] to return to Main Dashboard",
        ]
        return lines


class PaperclipView:
    """Renders Paperclip Company OS employee hierarchy and departmental budgets."""

    @staticmethod
    def render(employees: List[EmployeeAgent], width: int = 110) -> List[str]:
        lines = [
            "=" * width,
            " PAPERCLIP COMPANY OS — AGENT EMPLOYEE DIRECTORY (AAH20/paperclip) ",
            "=" * width,
            f" {'ID':<8} {'EMPLOYEE NAME':<24} {'DEPARTMENT':<18} {'STATUS':<10} {'BUDGET ($)':<12} {'SPENT ($)':<12} {'UTILIZATION':<16} {'TICKET':<20}",
            "-" * width,
        ]
        for emp in employees:
            util_str = make_bar(emp.budget_util_pct, 8)
            lines.append(
                f" {emp.id:<8} {emp.name[:23]:<24} {emp.department[:17]:<18} {emp.status:<10} "
                f"${emp.budget_usd:<11.2f} ${emp.spent_usd:<11.2f} {util_str:<16} {emp.ticket_id[:19]:<20}"
            )
        lines.append("-" * width)
        lines.append(" Hotkey: Press [d] to return to Main Dashboard")
        return lines


class CodexView:
    """Renders autonomous coding agent diff hunks and test execution states."""

    @staticmethod
    def render(hunks: List[CodexHunk], width: int = 110) -> List[str]:
        lines = [
            "=" * width,
            " CODEX & AUTONOMOUS CODING SWARM — AST DIFF HUNKS & TEST CYCLES ",
            "=" * width,
            f" {'FILE PATH':<44} {'HUNKS':<6} {'DIFF':<12} {'AST':<8} {'TEST STATUS':<16} {'BRANCH':<16}",
            "-" * width,
        ]
        for h in hunks:
            diff_str = f"+{h.additions} / -{h.deletions}"
            ast_str = "VALID" if h.ast_valid else "INVALID"
            lines.append(
                f" {h.file_path[:43]:<44} #{h.hunk_index:<5} {diff_str:<12} {ast_str:<8} {h.test_status:<16} {h.git_branch[:15]:<16}"
            )
        lines.append("-" * width)
        lines.append(" Hotkey: Press [d] to return to Main Dashboard")
        return lines


class HermesView:
    """Renders Nous Hermes cognitive sessions and ActionLedger receipts."""

    @staticmethod
    def render(sessions: List[HermesSession], width: int = 110) -> List[str]:
        lines = [
            "=" * width,
            " NOUS HERMES CORE & SOVEREIGN SKILL MATRIX (AAH20/hermes-matrix-adapter) ",
            "=" * width,
        ]
        for s in sessions:
            lines.append(f" Session ID: {s.session_id} | Agent: {s.agent_name} | Turn: #{s.current_turn} | Tools: {s.total_tool_calls}")
            lines.append(f"  Active Skills: {', '.join(s.active_skills)} | Memory Latency: {s.memory_query_ms:.2f} ms")
            lines.append(f"  ActionLedger Merkle Hash: {s.action_ledger_hash} ({s.receipts_verified_count} RFC 8785 Receipts Verified)")
            lines.append(f"  Last Reasoning Step: {s.last_reasoning_step}")
            lines.append("-" * width)
        lines.append(" Hotkey: Press [d] to return to Main Dashboard")
        return lines


class GpuView:
    """Renders NVIDIA NVML and AI accelerator telemetry."""

    @staticmethod
    def render(gpus: List[GpuMetrics], width: int = 110) -> List[str]:
        lines = [
            "=" * width,
            " NVIDIA HARDWARE & ACCELERATOR TELEMETRY (NVML / vLLM KV-CACHE) ",
            "=" * width,
            f" {'GPU':<5} {'NAME':<36} {'VRAM UTILIZATION':<26} {'COMPUTE%':<10} {'TEMP':<8} {'KV-CACHE':<16}",
            "-" * width,
        ]
        for g in gpus:
            vram_bar = f"{make_bar(g.vram_util_pct, 10)} ({g.vram_used_mb:.0f}/{g.vram_total_mb:.0f}MB)"
            kv_bar = make_bar(g.kv_cache_used_pct, 8)
            lines.append(
                f" #{g.gpu_id:<4} {g.name[:35]:<36} {vram_bar:<26} {g.compute_util_pct:5.1f}%    {g.temperature_c:4.1f}°C  {kv_bar:<16}"
            )
        lines.append("-" * width)
        lines.append(" Hotkey: Press [d] to return to Main Dashboard")
        return lines
