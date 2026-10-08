"""
Process Controller Engine.
Provides operator controls: Pause (SIGSTOP), Resume (SIGCONT), and Terminate (SIGTERM/SIGKILL).
"""

from __future__ import annotations

import os
import signal
import threading
from enum import Enum
from typing import Optional, Dict, Any

from a2z_agent_top.monitors.process_tracker import AgentProcessTracker, AgentState


class ControlAction(str, Enum):
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    TERMINATE = "TERMINATE"
    KILL = "KILL"


class ProcessController:
    """
    Manages operational state changes for running agent processes.
    Dispatches POSIX signals to real processes and handles virtual/demo PIDs safely.
    """

    def __init__(self, tracker: AgentProcessTracker):
        self.tracker = tracker
        self._lock = threading.RLock()

    def pause_agent(self, pid: int) -> bool:
        """Pause agent execution thread via SIGSTOP."""
        with self._lock:
            proc = self.tracker.get_process(pid)
            if not proc:
                return False

            if not self.tracker.demo_mode:
                try:
                    os.kill(pid, signal.SIGSTOP)
                except (ProcessLookupError, PermissionError):
                    pass

            self.tracker.update_agent_state(pid, AgentState.PAUSED)
            return True

    def resume_agent(self, pid: int) -> bool:
        """Resume paused agent execution thread via SIGCONT."""
        with self._lock:
            proc = self.tracker.get_process(pid)
            if not proc:
                return False

            if not self.tracker.demo_mode:
                try:
                    os.kill(pid, signal.SIGCONT)
                except (ProcessLookupError, PermissionError):
                    pass

            self.tracker.update_agent_state(pid, AgentState.THINKING)
            return True

    def terminate_agent(self, pid: int, force: bool = False) -> bool:
        """Terminate rogue agent loop via SIGTERM or SIGKILL."""
        with self._lock:
            proc = self.tracker.get_process(pid)
            if not proc:
                return False

            if not self.tracker.demo_mode:
                sig = signal.SIGKILL if force else signal.SIGTERM
                try:
                    os.kill(pid, sig)
                except (ProcessLookupError, PermissionError):
                    pass

            self.tracker.update_agent_state(pid, AgentState.TERMINATED)
            return True

    def toggle_pause(self, pid: int) -> Optional[AgentState]:
        """Toggles between PAUSED and THINKING for the selected agent."""
        with self._lock:
            proc = self.tracker.get_process(pid)
            if not proc:
                return None

            if proc.state == AgentState.PAUSED:
                self.resume_agent(pid)
                return AgentState.THINKING
            else:
                self.pause_agent(pid)
                return AgentState.PAUSED
