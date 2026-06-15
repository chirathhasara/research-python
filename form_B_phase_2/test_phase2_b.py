"""
Unit tests for Formula B Phase 2 — Workload-Aware Harmonic Growth
"""

import math
import time
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from formula_b_phase2 import Phase2BConfig, Phase2BSimulator, Phase1BSimulator

class TestVelocityTrackingB(unittest.TestCase):
    def test_velocity_history_populated(self):
        cfg = Phase2BConfig()
        sim = Phase2BSimulator(cfg)
        res = sim.run(1000)
        self.assertGreater(len(res.velocity_history), 0)

    def test_velocity_positive_for_fast_inserts(self):
        cfg = Phase2BConfig()
        sim = Phase2BSimulator(cfg)
        res = sim.run(1000)
        for v in res.velocity_history:
            self.assertGreaterEqual(v, 0)

    def test_slow_vs_fast_velocity(self):
        cfg = Phase2BConfig(lambda_param=0.1)
        # Fast
        sim_fast = Phase2BSimulator(cfg)
        res_fast = sim_fast.run(2000)
        # Slow
        sim_slow = Phase2BSimulator(cfg)
        res_slow = sim_slow.run(2000, delay_fn=lambda i: 0.0001)

        self.assertGreater(res_fast.avg_velocity, res_slow.avg_velocity)


class TestAdaptiveNumerator(unittest.TestCase):
    def test_numerator_increases_with_velocity(self):
        cfg = Phase2BConfig(lambda_param=1.0)
        sim = Phase2BSimulator(cfg)
        res = sim.run(2000)
        # With lambda > 0 and non-zero velocity, numerator should exceed 1.0
        self.assertGreater(res.max_numerator, 1.0)

    def test_lambda_zero_gives_constant_numerator(self):
        cfg = Phase2BConfig(lambda_param=0.0)
        sim = Phase2BSimulator(cfg)
        res = sim.run(1000)
        for n in res.numerator_history:
            self.assertAlmostEqual(n, 1.0, places=6)


class TestPhase1VsPhase2B(unittest.TestCase):
    def test_different_resize_counts(self):
        cfg = Phase2BConfig(lambda_param=0.5, g_min=1.1)
        p1 = Phase1BSimulator(g_min=cfg.g_min)
        p2 = Phase2BSimulator(cfg)
        r1 = p1.run(5000)
        r2 = p2.run(5000)
        # They should differ
        differs = (r1.resize_count != r2.resize_count or r1.total_copied != r2.total_copied)
        self.assertTrue(differs, "Phase 2 B should produce different results than Phase 1 B")


class TestSimulatorCorrectnessB(unittest.TestCase):
    def test_final_size_equals_workload(self):
        cfg = Phase2BConfig()
        sim = Phase2BSimulator(cfg)
        res = sim.run(500)
        self.assertEqual(res.final_size, 500)

    def test_resize_count_matches_history(self):
        cfg = Phase2BConfig()
        sim = Phase2BSimulator(cfg)
        res = sim.run(2000)
        self.assertEqual(res.resize_count, len(res.velocity_history))
        self.assertEqual(res.resize_count, len(res.numerator_history))
        self.assertEqual(res.resize_count, len(res.growth_factor_history))


if __name__ == "__main__":
    unittest.main(verbosity=2)
