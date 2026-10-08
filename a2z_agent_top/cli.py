"""
Command Line Interface for a2z-agent-top (agent-top / atop).
Provides interactive TUI, headless JSON streaming, and process control commands.
"""

from __future__ import annotations

import argparse
import sys
import json

from a2z_agent_top import __version__
from a2z_agent_top.tui.app import AgentTopApp
from a2z_agent_top.monitors.process_tracker import AgentProcessTracker
from a2z_agent_top.controller.process_control import ProcessController
from a2z_agent_top.controller.rollback_bridge import RollbackBridge


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="atop",
        description="a2z-agent-top (`atop` / `agent-top`): Real-Time Agent Swarm Observability & Interception Hypervisor.",
        epilog="Apex Growth Systems LLC | a2zsoc.com | NVIDIA Inception Program Partner",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless non-interactive mode (for CI/CD pipelines, tmux logs, and JSON streaming).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format when running in --headless mode (default: text).",
    )
    parser.add_argument(
        "-n", "--iterations",
        type=int,
        default=1,
        help="Number of iterations for headless mode (default: 1, 0 for infinite stream).",
    )
    parser.add_argument(
        "-i", "--interval",
        type=float,
        default=1.0,
        help="Refresh interval in seconds (default: 1.0).",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        default=True,
        help="Run in high-fidelity demo swarm mode across Paperclip, Hermes, Codex, and Apex MCP (default: True).",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Force live host process scanning via /proc and ps instead of demo simulation.",
    )

    # Subcommands for programmatic control
    subparsers = parser.add_subparsers(dest="command", help="Operational subcommands")

    pause_p = subparsers.add_parser("pause", help="Pause an agent process (SIGSTOP)")
    pause_p.add_argument("pid", type=int, help="Target process PID")

    resume_p = subparsers.add_parser("resume", help="Resume a paused agent process (SIGCONT)")
    resume_p.add_argument("pid", type=int, help="Target process PID")

    kill_p = subparsers.add_parser("kill", help="Terminate an agent process (SIGKILL)")
    kill_p.add_argument("pid", type=int, help="Target process PID")
    kill_p.add_argument("-f", "--force", action="store_true", help="Force immediate SIGKILL")

    rb_p = subparsers.add_parser("rollback", help="Trigger LIFO Compensatory Rollback via a2z-ghost-kernel")
    rb_p.add_argument("pid", type=int, help="Target process PID")

    snap_p = subparsers.add_parser("snapshot", help="Print immediate JSON telemetry snapshot and exit")

    return parser


def main(args: list[str] | None = None) -> int:
    parser = build_parser()
    parsed = parser.parse_args(args)

    demo_mode = False if parsed.live else parsed.demo

    # Handle subcommands if specified
    if parsed.command == "pause":
        tracker = AgentProcessTracker(demo_mode=demo_mode)
        ctrl = ProcessController(tracker)
        ok = ctrl.pause_agent(parsed.pid)
        print(f"[{'OK' if ok else 'FAIL'}] Paused PID {parsed.pid}")
        return 0 if ok else 1

    elif parsed.command == "resume":
        tracker = AgentProcessTracker(demo_mode=demo_mode)
        ctrl = ProcessController(tracker)
        ok = ctrl.resume_agent(parsed.pid)
        print(f"[{'OK' if ok else 'FAIL'}] Resumed PID {parsed.pid}")
        return 0 if ok else 1

    elif parsed.command == "kill":
        tracker = AgentProcessTracker(demo_mode=demo_mode)
        ctrl = ProcessController(tracker)
        ok = ctrl.terminate_agent(parsed.pid, force=parsed.force)
        print(f"[{'OK' if ok else 'FAIL'}] Terminated PID {parsed.pid}")
        return 0 if ok else 1

    elif parsed.command == "rollback":
        tracker = AgentProcessTracker(demo_mode=demo_mode)
        rb = RollbackBridge(tracker)
        res = rb.trigger_rollback(parsed.pid)
        print(json.dumps(res.to_dict(), indent=2))
        return 0 if res.success else 1

    elif parsed.command == "snapshot":
        app = AgentTopApp(demo_mode=demo_mode)
        snap = app.get_snapshot()
        print(json.dumps(snap, indent=2))
        return 0

    # Main TUI or Headless Runner
    app = AgentTopApp(demo_mode=demo_mode, refresh_rate_hz=1.0 / parsed.interval)
    if parsed.headless:
        app.run_headless(
            output_format=parsed.format,
            iterations=parsed.iterations,
            interval_sec=parsed.interval,
        )
    else:
        try:
            app.run_curses()
        except KeyboardInterrupt:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
