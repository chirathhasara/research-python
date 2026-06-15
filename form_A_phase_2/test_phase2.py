"""
Unit tests for Formula A Phase 2 — Workload-Aware Alpha
"""

import math
import time
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from formula_a_phase2 import Phase2Config, Phase2Simulator, Phase1Simulator


class TestVelocityTracking(unittest.TestCase):
    """Verify that insertion velocity is computed and recorded."""

    def test_velocity_history_populated(self):
        cfg = Phase2Config()
        sim = Phase2Simulator(cfg)
        res = sim.run(1000)
        self.assertGreater(len(res.velocity_history), 0,
                           "Velocity history should be non-empty after resizes")

    def test_velocity_positive_for_fast_inserts(self):
        cfg = Phase2Config()
        sim = Phase2Simulator(cfg)
        res = sim.run(1000)
        for v in res.velocity_history:
            self.assertGreaterEqual(v, 0, "Velocity must be non-negative")

    def test_slow_vs_fast_velocity(self):
        cfg = Phase2Config(k=0.001)
        # Fast
        sim_fast = Phase2Simulator(cfg)
        res_fast = sim_fast.run(5000)
        # Slow
        sim_slow = Phase2Simulator(cfg)
        res_slow = sim_slow.run(5000, delay_fn=lambda i: 0.0001)

        self.assertGreater(res_fast.avg_velocity, res_slow.avg_velocity,
                           "Fast workload should have higher avg velocity")


class TestAdaptiveAlpha(unittest.TestCase):
    """Verify alpha(v) = alpha_base + k * v_smooth."""

    def test_alpha_above_base(self):
        cfg = Phase2Config(alpha_base=2.0, k=0.01)
        sim = Phase2Simulator(cfg)
        res = sim.run(5000)
        for a in res.alpha_history:
            self.assertGreaterEqual(a, cfg.alpha_base - 1e-9,
                                    "Alpha must be >= alpha_base")

    def test_alpha_increases_with_velocity(self):
        cfg = Phase2Config(alpha_base=2.0, k=0.01)
        sim = Phase2Simulator(cfg)
        res = sim.run(5000)
        # With k > 0 and non-zero velocity, alpha should exceed base
        self.assertGreater(res.max_alpha, cfg.alpha_base,
                           "Max alpha should exceed alpha_base for k > 0")

    def test_k_zero_gives_constant_alpha(self):
        cfg = Phase2Config(alpha_base=2.0, k=0.0)
        sim = Phase2Simulator(cfg)
        res = sim.run(2000)
        for a in res.alpha_history:
            self.assertAlmostEqual(a, cfg.alpha_base, places=6,
                                   msg="k=0 should give constant alpha")


class TestGrowthFactorClamping(unittest.TestCase):
    """Verify g_min <= g(C,v) <= g_max."""

    def test_growth_factor_bounds(self):
        cfg = Phase2Config(g_min=1.1, g_max=2.0, k=0.1)
        sim = Phase2Simulator(cfg)
        res = sim.run(5000)
        for g in res.growth_factor_history:
            self.assertGreaterEqual(g, cfg.g_min - 1e-9)
            self.assertLessEqual(g, cfg.g_max + 1e-9)


class TestEMASmoothing(unittest.TestCase):
    """Verify EMA smoothing is applied."""

    def test_ema_dampens_spikes(self):
        cfg = Phase2Config(velocity_smoothing_factor=0.9)
        sim = Phase2Simulator(cfg)
        res = sim.run(5000)
        if len(res.velocity_history) > 2:
            diffs = [abs(res.velocity_history[i] - res.velocity_history[i-1])
                     for i in range(1, len(res.velocity_history))]
            # With 0.9 EMA, consecutive values should be somewhat close
            avg_diff = sum(diffs) / len(diffs)
            max_vel = max(res.velocity_history) if res.velocity_history else 1
            self.assertLess(avg_diff / (max_vel + 1e-9), 1.0,
                            "EMA should smooth velocity changes")


class TestPhase1VsPhase2(unittest.TestCase):
    """Verify Phase 2 produces different behavior than Phase 1."""

    def test_different_resize_counts(self):
        """With k > 0, Phase 2 should differ from Phase 1 in at least some metric."""
        cfg = Phase2Config(alpha_base=2.0, k=0.01)
        p1 = Phase1Simulator(alpha=2.0, beta=cfg.beta)
        p2 = Phase2Simulator(cfg)
        r1 = p1.run(10000)
        r2 = p2.run(10000)
        # They won't be identical because velocity modifies alpha
        differs = (r1.resize_count != r2.resize_count or
                   r1.total_copied != r2.total_copied or
                   r1.final_capacity != r2.final_capacity)
        self.assertTrue(differs,
                        "Phase 2 should produce different results than Phase 1")


class TestSimulatorCorrectness(unittest.TestCase):
    """Basic correctness checks."""

    def test_final_size_equals_workload(self):
        cfg = Phase2Config()
        sim = Phase2Simulator(cfg)
        res = sim.run(500)
        self.assertEqual(res.final_size, 500)

    def test_capacity_gte_size(self):
        cfg = Phase2Config()
        sim = Phase2Simulator(cfg)
        res = sim.run(500)
        self.assertGreaterEqual(res.final_capacity, res.final_size)

    def test_resize_count_matches_history(self):
        cfg = Phase2Config()
        sim = Phase2Simulator(cfg)
        res = sim.run(2000)
        self.assertEqual(res.resize_count, len(res.velocity_history))
        self.assertEqual(res.resize_count, len(res.alpha_history))
        self.assertEqual(res.resize_count, len(res.growth_factor_history))


if __name__ == "__main__":
    unittest.main(verbosity=2)
