"""Unit tests for TUI app, view renderers, and CLI entry point."""

import unittest
import json
from a2z_agent_top.tui.app import AgentTopApp, ActiveView
from a2z_agent_top.tui.hotkeys import HotkeyController
from a2z_agent_top.cli import main, build_parser


class TestTuiAndCli(unittest.TestCase):
    def setUp(self):
        self.app = AgentTopApp(demo_mode=True)

    def test_app_snapshot(self):
        snap = self.app.get_snapshot()
        self.assertIn("version", snap)
        self.assertEqual(snap["version"], "1.0.0")
        self.assertIn("swarm_status", snap)
        self.assertIn("token_economics", snap)
        self.assertIn("processes", snap)
        self.assertIn("apex_mcp", snap)
        self.assertIn("paperclip_employees", snap)
        self.assertIn("codex_diff_hunks", snap)
        self.assertIn("hermes_sessions", snap)
        self.assertGreaterEqual(len(snap["processes"]), 5)

    def test_render_all_views(self):
        views = [
            ActiveView.DASHBOARD,
            ActiveView.MCP,
            ActiveView.PAPERCLIP,
            ActiveView.CODEX,
            ActiveView.HERMES,
            ActiveView.GPU,
        ]
        for v in views:
            self.app._set_view(v)
            frame = self.app.render_text_frame(width=100)
            self.assertIn("a2z-agent-top", frame)
            self.assertIn("STATUS:", frame)
            self.assertIn("HOTKEYS:", frame)

    def test_hotkey_dispatch(self):
        hotkeys = HotkeyController()
        called = {"status": False}

        def dummy_action():
            called["status"] = True

        hotkeys.register("x", dummy_action)
        handled = hotkeys.handle_key(ord("x"))
        self.assertTrue(handled)
        self.assertTrue(called["status"])

        # Test space bar
        space_called = {"status": False}
        hotkeys.register(" ", lambda: space_called.update({"status": True}))
        handled_space = hotkeys.handle_key(32)
        self.assertTrue(handled_space)
        self.assertTrue(space_called["status"])

    def test_cli_parser(self):
        parser = build_parser()
        args = parser.parse_args(["--headless", "--format", "json", "-n", "1"])
        self.assertTrue(args.headless)
        self.assertEqual(args.format, "json")
        self.assertEqual(args.iterations, 1)

    def test_cli_snapshot_command(self):
        ret = main(["snapshot"])
        self.assertEqual(ret, 0)

    def test_cli_pause_and_resume_commands(self):
        ret_pause = main(["pause", "41021"])
        self.assertEqual(ret_pause, 0)
        ret_resume = main(["resume", "41021"])
        self.assertEqual(ret_resume, 0)

    def test_cli_rollback_command(self):
        ret_rb = main(["rollback", "41025"])
        self.assertEqual(ret_rb, 0)

    def test_cli_headless_text(self):
        ret = main(["--headless", "--format", "text", "-n", "1"])
        self.assertEqual(ret, 0)


if __name__ == "__main__":
    unittest.main()
