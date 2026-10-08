"""Unit tests for AgentProcessTracker."""

import unittest
from a2z_agent_top.monitors.process_tracker import AgentProcessTracker, ProcessInfo, AgentState


class TestAgentProcessTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = AgentProcessTracker(demo_mode=True)

    def test_seed_demo_swarm(self):
        procs = self.tracker.get_all_processes()
        self.assertGreaterEqual(len(procs), 5)
        pids = [p.pid for p in procs]
        self.assertIn(41021, pids)
        self.assertIn(41022, pids)
        self.assertIn(41023, pids)

    def test_register_and_query_agent(self):
        new_proc = ProcessInfo(
            pid=99999,
            name="test-worker",
            state=AgentState.THINKING,
            framework="LangGraph",
        )
        self.tracker.register_agent(new_proc)
        fetched = self.tracker.get_process(99999)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "test-worker")
        self.assertEqual(fetched.state, AgentState.THINKING)

    def test_update_agent_state(self):
        ok = self.tracker.update_agent_state(41021, AgentState.PAUSED, last_tool="freeze_io")
        self.assertTrue(ok)
        proc = self.tracker.get_process(41021)
        self.assertEqual(proc.state, AgentState.PAUSED)
        self.assertEqual(proc.last_tool, "freeze_io")

    def test_remove_process(self):
        removed = self.tracker.remove_process(41021)
        self.assertIsNotNone(removed)
        self.assertIsNone(self.tracker.get_process(41021))

    def test_to_dict_serialization(self):
        proc = self.tracker.get_process(41022)
        d = proc.to_dict()
        self.assertEqual(d["pid"], 41022)
        self.assertIn("cpu_pct", d)
        self.assertIn("blast_radius", d)


if __name__ == "__main__":
    unittest.main()
