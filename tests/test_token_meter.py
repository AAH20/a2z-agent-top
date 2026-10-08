"""Unit tests for SwarmTokenMeter and TokenVelocity."""

import unittest
import time
from a2z_agent_top.monitors.token_meter import SwarmTokenMeter, TokenVelocity


class TestSwarmTokenMeter(unittest.TestCase):
    def setUp(self):
        self.meter = SwarmTokenMeter()

    def test_record_tokens_and_tick(self):
        self.meter.record_agent_tokens(41021, 500)
        self.meter.record_agent_tokens(41022, 1500)
        time.sleep(0.01)

        vel = self.meter.tick([41021, 41022], avg_ctx_pct=55.0)
        self.assertGreater(vel.tokens_per_second, 0.0)
        self.assertEqual(vel.total_tokens_consumed, 2000)
        self.assertGreater(vel.cost_per_hour_usd, 0.0)
        self.assertEqual(vel.avg_context_saturation_pct, 55.0)

    def test_simulate_tick(self):
        vel = self.meter.simulate_tick(num_agents=5)
        self.assertGreater(vel.tokens_per_second, 0.0)
        self.assertGreater(vel.total_tokens_consumed, 0)
        d = vel.to_dict()
        self.assertIn("cost_per_hour_usd", d)
        self.assertIn("peak_tokens_per_second", d)


if __name__ == "__main__":
    unittest.main()
