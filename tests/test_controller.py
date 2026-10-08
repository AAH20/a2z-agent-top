"""Unit tests for ProcessController and RollbackBridge."""

import unittest
from a2z_agent_top.monitors.process_tracker import AgentProcessTracker, AgentState
from a2z_agent_top.controller.process_control import ProcessController
from a2z_agent_top.controller.rollback_bridge import RollbackBridge


class TestControllerAndRollback(unittest.TestCase):
    def setUp(self):
        self.tracker = AgentProcessTracker(demo_mode=True)
        self.controller = ProcessController(self.tracker)
        self.rollback_bridge = RollbackBridge(self.tracker)

    def test_pause_and_resume(self):
        pid = 41021
        self.controller.pause_agent(pid)
        proc = self.tracker.get_process(pid)
        self.assertEqual(proc.state, AgentState.PAUSED)

        self.controller.resume_agent(pid)
        proc = self.tracker.get_process(pid)
        self.assertEqual(proc.state, AgentState.THINKING)

    def test_toggle_pause(self):
        pid = 41022
        st1 = self.controller.toggle_pause(pid)
        self.assertEqual(st1, AgentState.PAUSED)
        st2 = self.controller.toggle_pause(pid)
        self.assertEqual(st2, AgentState.THINKING)

    def test_terminate_agent(self):
        pid = 41023
        ok = self.controller.terminate_agent(pid, force=True)
        self.assertTrue(ok)
        proc = self.tracker.get_process(pid)
        self.assertEqual(proc.state, AgentState.TERMINATED)

    def test_rollback_bridge(self):
        pid = 41025
        result = self.rollback_bridge.trigger_rollback(pid)
        self.assertTrue(result.success)
        self.assertEqual(result.pid, pid)
        self.assertGreater(result.actions_reverted, 0)
        self.assertGreater(result.rollback_latency_us, 0.0)
        self.assertTrue(result.receipt_hash.startswith("sha256:"))
        self.assertIn("Zero leaked state", result.message)

        # Agent should now be marked terminated
        proc = self.tracker.get_process(pid)
        self.assertEqual(proc.state, AgentState.TERMINATED)

    def test_rollback_nonexistent_pid(self):
        result = self.rollback_bridge.trigger_rollback(12345678)
        self.assertFalse(result.success)


if __name__ == "__main__":
    unittest.main()
