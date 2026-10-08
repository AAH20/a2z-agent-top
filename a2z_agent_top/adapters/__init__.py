"""Adapters package for a2z-agent-top."""
from a2z_agent_top.adapters.paperclip import PaperclipAdapter, EmployeeAgent
from a2z_agent_top.adapters.hermes import HermesAdapter, HermesSession
from a2z_agent_top.adapters.codex import CodexDiffAdapter, CodexHunk
from a2z_agent_top.adapters.apex_mcp import ApexMcpKernelAdapter, McpKernelTelemetry

__all__ = [
    "PaperclipAdapter",
    "EmployeeAgent",
    "HermesAdapter",
    "HermesSession",
    "CodexDiffAdapter",
    "CodexHunk",
    "ApexMcpKernelAdapter",
    "McpKernelTelemetry",
]
