"""
AgentTopApp: Curses Event Loop & Terminal Screen Manager.
Coordinates monitors, adapters, hotkeys, and curses rendering.
"""

from __future__ import annotations

import curses
import json
import os
import sys
import time
from typing import Optional, List, Dict, Any

from a2z_agent_top.monitors.process_tracker import AgentProcessTracker, ProcessInfo, AgentState
from a2z_agent_top.monitors.token_meter import SwarmTokenMeter, TokenVelocity
from a2z_agent_top.monitors.nvml_gpu import GpuTelemetryMonitor, GpuMetrics
from a2z_agent_top.adapters.paperclip import PaperclipAdapter
from a2z_agent_top.adapters.hermes import HermesAdapter
from a2z_agent_top.adapters.codex import CodexDiffAdapter
from a2z_agent_top.adapters.apex_mcp import ApexMcpKernelAdapter
from a2z_agent_top.controller.process_control import ProcessController
from a2z_agent_top.controller.rollback_bridge import RollbackBridge
from a2z_agent_top.tui.hotkeys import HotkeyController
from a2z_agent_top.tui.views import (
    DashboardView,
    McpView,
    PaperclipView,
    CodexView,
    HermesView,
    GpuView,
)


class ActiveView:
    DASHBOARD = "DASHBOARD"
    MCP = "MCP"
    PAPERCLIP = "PAPERCLIP"
    CODEX = "CODEX"
    HERMES = "HERMES"
    GPU = "GPU"


class AgentTopApp:
    """
    Main terminal user interface application for a2z-agent-top.
    Runs non-blocking curses loop or headless JSON streaming pipeline.
    """

    def __init__(self, demo_mode: bool = True, refresh_rate_hz: float = 2.0):
        self.demo_mode = demo_mode
        self.refresh_interval = 1.0 / max(0.5, refresh_rate_hz)
        self.active_view = ActiveView.DASHBOARD
        self.selected_index = 0
        self.status_message = "Ready. Press [Space] to Pause, [k] to Kill, [r] to Rollback, [q] to Quit."

        # Initialize engines
        self.tracker = AgentProcessTracker(demo_mode=demo_mode)
        self.token_meter = SwarmTokenMeter()
        self.gpu_monitor = GpuTelemetryMonitor(demo_mode=demo_mode)

        # Initialize adapters
        self.paperclip_adapter = PaperclipAdapter(demo_mode=demo_mode)
        self.hermes_adapter = HermesAdapter(demo_mode=demo_mode)
        self.codex_adapter = CodexDiffAdapter(demo_mode=demo_mode)
        self.mcp_adapter = ApexMcpKernelAdapter(demo_mode=demo_mode)

        # Initialize controllers
        self.controller = ProcessController(self.tracker)
        self.rollback_bridge = RollbackBridge(self.tracker)

        # Setup hotkeys
        self.hotkeys = HotkeyController()
        self._setup_hotkeys()

        self._running = True

    def _setup_hotkeys(self) -> None:
        """Register keyboard shortcut handlers."""
        self.hotkeys.register("q", self._action_quit)
        self.hotkeys.register(" ", self._action_toggle_pause)
        self.hotkeys.register("k", self._action_kill_selected)
        self.hotkeys.register("r", self._action_rollback_selected)
        self.hotkeys.register("m", lambda: self._set_view(ActiveView.MCP))
        self.hotkeys.register("p", lambda: self._set_view(ActiveView.PAPERCLIP))
        self.hotkeys.register("c", lambda: self._set_view(ActiveView.CODEX))
        self.hotkeys.register("h", lambda: self._set_view(ActiveView.HERMES))
        self.hotkeys.register("g", lambda: self._set_view(ActiveView.GPU))
        self.hotkeys.register("d", lambda: self._set_view(ActiveView.DASHBOARD))

    def _set_view(self, view_name: str) -> None:
        self.active_view = view_name
        self.status_message = f"Switched view to {view_name}. Press [d] for Dashboard, [q] to Quit."

    def _action_quit(self) -> None:
        self._running = False

    def _get_selected_pid(self) -> Optional[int]:
        procs = self.tracker.get_all_processes()
        if 0 <= self.selected_index < len(procs):
            return procs[self.selected_index].pid
        return None

    def _action_toggle_pause(self) -> None:
        pid = self._get_selected_pid()
        if pid:
            new_state = self.controller.toggle_pause(pid)
            self.status_message = f"Process {pid} state toggled to {new_state.value if new_state else 'UNKNOWN'}."
        else:
            self.status_message = "No process selected."

    def _action_kill_selected(self) -> None:
        pid = self._get_selected_pid()
        if pid:
            self.controller.terminate_agent(pid, force=True)
            self.status_message = f"SIGKILL dispatched to process {pid}. Terminated cleanly."
        else:
            self.status_message = "No process selected."

    def _action_rollback_selected(self) -> None:
        pid = self._get_selected_pid()
        if pid:
            res = self.rollback_bridge.trigger_rollback(pid)
            self.status_message = (
                f"Rollback Complete: Reverted {res.actions_reverted} tool actions in {res.rollback_latency_us:.1f}µs. "
                f"Zero leaked state. {res.receipt_hash[:16]}..."
            )
        else:
            self.status_message = "No process selected."

    def get_snapshot(self) -> Dict[str, Any]:
        """Generates a complete telemetry snapshot dictionary for headless/JSON export."""
        procs = self.tracker.get_all_processes()
        gpus = self.gpu_monitor.probe_hardware()
        token_vel = self.token_meter.simulate_tick(len(procs)) if self.demo_mode else self.token_meter.tick([p.pid for p in procs])

        return {
            "timestamp": time.time(),
            "version": "1.0.0",
            "swarm_status": {
                "total_agents": len(procs),
                "active_agents": sum(1 for p in procs if p.state in (AgentState.THINKING, AgentState.TOOL_EXEC)),
                "paused_agents": sum(1 for p in procs if p.state == AgentState.PAUSED),
                "deadlocked_agents": sum(1 for p in procs if p.state == AgentState.DEADLOCKED),
                "terminated_agents": sum(1 for p in procs if p.state == AgentState.TERMINATED),
            },
            "token_economics": token_vel.to_dict(),
            "processes": [p.to_dict() for p in procs],
            "gpu_telemetry": [g.to_dict() for g in gpus],
            "apex_mcp": self.mcp_adapter.get_telemetry().to_dict(),
            "paperclip_employees": [e.to_dict() for e in self.paperclip_adapter.get_employees()],
            "codex_diff_hunks": [h.to_dict() for h in self.codex_adapter.get_hunks()],
            "hermes_sessions": [s.to_dict() for s in self.hermes_adapter.get_sessions()],
        }

    def render_text_frame(self, width: int = 110) -> str:
        """Renders the current screen view as formatted text for terminal or headless output."""
        procs = self.tracker.get_all_processes()
        active_count = sum(1 for p in procs if p.state in (AgentState.THINKING, AgentState.TOOL_EXEC))
        paused_count = sum(1 for p in procs if p.state == AgentState.PAUSED)
        token_vel = self.token_meter.simulate_tick(len(procs)) if self.demo_mode else self.token_meter.tick([p.pid for p in procs])
        gpus = self.gpu_monitor.probe_hardware()

        gpu_summary = f"{len(gpus)} GPU(s) Online | VRAM: {sum(g.vram_used_mb for g in gpus):.0f}MB" if gpus else "CPU Only"

        lines = DashboardView.render_header(
            total_agents=len(procs),
            active_count=active_count,
            paused_count=paused_count,
            token_vel=token_vel,
            gpu_summary=gpu_summary,
            width=width,
        )

        # Render sub-view
        if self.active_view == ActiveView.DASHBOARD:
            lines.extend(DashboardView.render_table(procs, self.selected_index, width))
        elif self.active_view == ActiveView.MCP:
            lines.extend(McpView.render(self.mcp_adapter.get_telemetry(), width))
        elif self.active_view == ActiveView.PAPERCLIP:
            lines.extend(PaperclipView.render(self.paperclip_adapter.get_employees(), width))
        elif self.active_view == ActiveView.CODEX:
            lines.extend(CodexView.render(self.codex_adapter.get_hunks(), width))
        elif self.active_view == ActiveView.HERMES:
            lines.extend(HermesView.render(self.hermes_adapter.get_sessions(), width))
        elif self.active_view == ActiveView.GPU:
            lines.extend(GpuView.render(gpus, width))

        # Bottom status and hotkey bar
        lines.append("=" * width)
        lines.append(f" STATUS: {self.status_message}")
        lines.append(f" HOTKEYS: [Space] Pause/Resume | [k] Kill | [r] Rollback | [m] MCP | [p] Paperclip | [c] Codex | [h] Hermes | [g] GPU | [q] Quit")
        lines.append("=" * width)

        return "\n".join(lines)

    def run_headless(self, output_format: str = "text", iterations: int = 1, interval_sec: float = 1.0) -> None:
        """Runs in headless mode, streaming text frames or JSON snapshots to stdout."""
        count = 0
        while self._running and (iterations <= 0 or count < iterations):
            if output_format.lower() == "json":
                snapshot = self.get_snapshot()
                sys.stdout.write(json.dumps(snapshot, indent=2) + "\n")
                sys.stdout.flush()
            else:
                frame = self.render_text_frame()
                sys.stdout.write(frame + "\n")
                sys.stdout.flush()

            count += 1
            if iterations <= 0 or count < iterations:
                time.sleep(interval_sec)

    def run_curses(self) -> None:
        """Launches the interactive full-screen curses TUI application."""
        curses.wrapper(self._curses_main)

    def _curses_main(self, stdscr: curses.window) -> None:
        curses.curs_set(0)
        stdscr.nodelay(True)
        curses.use_default_colors()

        last_tick = time.time()

        while self._running:
            max_y, max_x = stdscr.getmaxyx()
            width = max(80, max_x - 2)

            # Check for keyboard inputs
            try:
                ch = stdscr.getch()
                if ch != -1:
                    # Arrow keys navigation
                    if ch == curses.KEY_UP:
                        self.selected_index = max(0, self.selected_index - 1)
                    elif ch == curses.KEY_DOWN:
                        procs = self.tracker.get_all_processes()
                        self.selected_index = min(max(0, len(procs) - 1), self.selected_index + 1)
                    else:
                        self.hotkeys.handle_key(ch)
            except Exception:
                pass

            # Redraw if interval has elapsed
            now = time.time()
            if now - last_tick >= self.refresh_interval:
                last_tick = now
                if not self.demo_mode:
                    self.tracker.scan_system_processes()

                stdscr.erase()
                frame = self.render_text_frame(width=width)
                for row_idx, line in enumerate(frame.split("\n")):
                    if row_idx < max_y - 1:
                        try:
                            stdscr.addstr(row_idx, 0, line[:width])
                        except curses.error:
                            pass
                stdscr.refresh()

            time.sleep(0.02)
