"""Unit tests for ecosystem adapters: Paperclip, Hermes, Codex, and Apex MCP."""

import unittest
from a2z_agent_top.adapters.paperclip import PaperclipAdapter
from a2z_agent_top.adapters.hermes import HermesAdapter
from a2z_agent_top.adapters.codex import CodexDiffAdapter
from a2z_agent_top.adapters.apex_mcp import ApexMcpKernelAdapter


class TestEcosystemAdapters(unittest.TestCase):
    def test_paperclip_adapter(self):
        pc = PaperclipAdapter(demo_mode=True)
        employees = pc.get_employees()
        self.assertGreaterEqual(len(employees), 4)

        emp0 = employees[0]
        self.assertEqual(emp0.id, "emp-001")
        self.assertGreater(emp0.budget_usd, 0.0)
        self.assertGreater(emp0.spent_usd, 0.0)
        self.assertLessEqual(emp0.budget_util_pct, 100.0)

        spend = pc.get_department_spend_summary()
        self.assertIn("Engineering", spend)
        self.assertIn("Security & GRC", spend)
        self.assertGreater(spend["Engineering"]["spent"], 0.0)

    def test_hermes_adapter(self):
        hermes = HermesAdapter(demo_mode=True)
        sessions = hermes.get_sessions()
        self.assertGreaterEqual(len(sessions), 2)

        s1 = sessions[0]
        self.assertTrue(s1.session_id.startswith("hermes-sess-"))
        self.assertIn("sovereign_memory", s1.active_skills)
        self.assertTrue(s1.action_ledger_hash.startswith("sha256:"))
        self.assertGreater(s1.receipts_verified_count, 0)

    def test_codex_adapter(self):
        codex = CodexDiffAdapter(demo_mode=True)
        hunks = codex.get_hunks()
        self.assertGreaterEqual(len(hunks), 3)

        h0 = hunks[0]
        self.assertTrue(h0.file_path.endswith(".py"))
        self.assertGreater(h0.additions, 0)
        self.assertTrue(h0.ast_valid)
        self.assertEqual(h0.test_status, "PASSING")

    def test_apex_mcp_adapter(self):
        mcp = ApexMcpKernelAdapter(demo_mode=True)
        telemetry = mcp.get_telemetry()
        self.assertEqual(telemetry.original_schema_tokens, 102400)
        self.assertEqual(telemetry.pruned_schema_tokens, 4250)
        self.assertGreater(telemetry.knapsack_reduction_pct, 90.0)
        self.assertGreater(telemetry.radix_lcp_hit_pct, 80.0)
        self.assertGreaterEqual(telemetry.lct_deadlocks_defused, 1)

        # Update telemetry
        mcp.update_telemetry(deadlocks=2, blocked=1)
        updated = mcp.get_telemetry()
        self.assertEqual(updated.lct_deadlocks_defused, 4)
        self.assertEqual(updated.blocked_tool_calls, 2)


if __name__ == "__main__":
    unittest.main()
