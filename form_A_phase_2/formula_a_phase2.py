"""
Formula A: Logarithmic Adaptive Growth — Phase 2 (Workload-Aware Alpha)
========================================================================
Extends Phase 1 by making alpha adaptive based on insertion velocity.

    v = delta_N / delta_t                   (insertion velocity)
    v_smooth = ema_factor * v_prev + (1 - ema_factor) * v_current
    alpha(v) = alpha_base + k * v_smooth    (adaptive alpha)

    g(C,v) = min(g_max, max(g_min, 1 + alpha(v) / ln(C + beta)))
    C_new  = ceil(C_old * g(C,v))

Author : Research Project - Dynamic Growth Factor Study
Date   : 2026-06-15
"""

import sys
import os
import time
import csv
import math
from dataclasses import dataclass, field

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ═══════════════════════════════════════════════════════════════════════
# 1.  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════
@dataclass
class Phase2Config:
    """All tunable parameters for Phase 2 experiments."""
    alpha_base: float = 2.0
    beta: float = 2.0
    k: float = 0.001          # velocity sensitivity
    g_min: float = 1.1
    g_max: float = 2.0
    velocity_smoothing_factor: float = 0.9   # EMA factor
    initial_capacity: int = 10

    @property
    def label(self) -> str:
        return f"P2(ab={self.alpha_base},b={self.beta},k={self.k})"


# ═══════════════════════════════════════════════════════════════════════
# 2.  EXTENDED RESULT DATACLASS
# ═══════════════════════════════════════════════════════════════════════
@dataclass
class Phase2Result:
    """Stores outcome including velocity/alpha tracking."""
    strategy_name: str
    workload_name: str
    workload_size: int
    final_capacity: int
    final_size: int
    resize_count: int
    total_copied: int
    memory_waste_pct: float
    exec_time_ms: float
    # Phase 2 specific metrics
    avg_velocity: float = 0.0
    max_velocity: float = 0.0
    avg_alpha: float = 0.0
    max_alpha: float = 0.0
    avg_growth_factor: float = 0.0
    # Histories for graphing (sampled at resize events)
    velocity_history: list = field(default_factory=list)
    alpha_history: list = field(default_factory=list)
    growth_factor_history: list = field(default_factory=list)
    capacity_history: list = field(default_factory=list)
    resize_insertion_indices: list = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════
# 3.  PHASE 2 SIMULATOR (Velocity-Aware)
# ═══════════════════════════════════════════════════════════════════════
class Phase2Simulator:
    """
    Dynamic array simulator with insertion velocity tracking.
    Calls a growth function that receives (capacity, smoothed_velocity).
    """

    def __init__(self, cfg: Phase2Config):
        self.cfg = cfg
        self.capacity = cfg.initial_capacity
        self.size = 0
        self.resize_count = 0
        self.total_copied = 0

        # Velocity tracking
        self._last_resize_time: float = 0.0
        self._last_resize_size: int = 0
        self._v_smooth: float = 0.0

        # Histories
        self._vel_hist: list[float] = []
        self._alpha_hist: list[float] = []
        self._gf_hist: list[float] = []
        self._cap_hist: list[int] = []
        self._resize_idx: list[int] = []

    def run(self, n: int, delay_fn=None) -> Phase2Result:
        """
        Insert n elements.  delay_fn(i) is called per-insertion to
        simulate different workload patterns (returns seconds to sleep).
        """
        self._last_resize_time = time.perf_counter()
        self._last_resize_size = 0

        t0 = time.perf_counter()

        for i in range(n):
            if delay_fn is not None:
                d = delay_fn(i)
                if d > 0:
                    time.sleep(d)

            if self.size == self.capacity:
                self._do_resize(i)

            self.size += 1

        t1 = time.perf_counter()

        waste_pct = ((self.capacity - self.size) / self.capacity) * 100.0

        avg_v  = float(np.mean(self._vel_hist))  if self._vel_hist else 0.0
        max_v  = float(np.max(self._vel_hist))   if self._vel_hist else 0.0
        avg_a  = float(np.mean(self._alpha_hist)) if self._alpha_hist else 0.0
        max_a  = float(np.max(self._alpha_hist))  if self._alpha_hist else 0.0
        avg_gf = float(np.mean(self._gf_hist))   if self._gf_hist else 0.0

        return Phase2Result(
            strategy_name="",
            workload_name="",
            workload_size=n,
            final_capacity=self.capacity,
            final_size=self.size,
            resize_count=self.resize_count,
            total_copied=self.total_copied,
            memory_waste_pct=round(waste_pct, 4),
            exec_time_ms=round((t1 - t0) * 1000, 4),
            avg_velocity=round(avg_v, 4),
            max_velocity=round(max_v, 4),
            avg_alpha=round(avg_a, 4),
            max_alpha=round(max_a, 4),
            avg_growth_factor=round(avg_gf, 6),
            velocity_history=self._vel_hist,
            alpha_history=self._alpha_hist,
            growth_factor_history=self._gf_hist,
            capacity_history=self._cap_hist,
            resize_insertion_indices=self._resize_idx,
        )

    def _do_resize(self, insertion_idx: int):
        now = time.perf_counter()
        dt = now - self._last_resize_time
        dn = self.size - self._last_resize_size

        # Compute instantaneous velocity (insertions/second), safe div
        v_current = dn / dt if dt > 1e-12 else 0.0

        # EMA smoothing
        ema = self.cfg.velocity_smoothing_factor
        self._v_smooth = ema * self._v_smooth + (1.0 - ema) * v_current

        # Adaptive alpha
        alpha_v = self.cfg.alpha_base + self.cfg.k * self._v_smooth

        # Growth factor
        ln_val = math.log(self.capacity + self.cfg.beta)
        g = 1.0 + alpha_v / ln_val
        g = min(self.cfg.g_max, max(self.cfg.g_min, g))

        new_cap = int(math.ceil(self.capacity * g))
        new_cap = max(new_cap, self.capacity + 1)

        # Record
        self._vel_hist.append(self._v_smooth)
        self._alpha_hist.append(alpha_v)
        self._gf_hist.append(g)
        self._cap_hist.append(new_cap)
        self._resize_idx.append(insertion_idx)

        self.total_copied += self.size
        self.capacity = new_cap
        self.resize_count += 1

        self._last_resize_time = now
        self._last_resize_size = self.size


# ═══════════════════════════════════════════════════════════════════════
# 4.  PHASE 1 SIMULATOR (for comparison, simplified)
# ═══════════════════════════════════════════════════════════════════════
class Phase1Simulator:
    """Phase 1 constant-alpha simulator for side-by-side comparison."""

    def __init__(self, alpha: float, beta: float,
                 g_min: float = 1.1, g_max: float = 2.0,
                 initial_capacity: int = 10):
        self.alpha = alpha
        self.beta = beta
        self.g_min = g_min
        self.g_max = g_max
        self.capacity = initial_capacity
        self.size = 0
        self.resize_count = 0
        self.total_copied = 0
        self._gf_hist: list[float] = []
        self._cap_hist: list[int] = []
        self._resize_idx: list[int] = []

    def run(self, n: int, delay_fn=None) -> Phase2Result:
        t0 = time.perf_counter()
        for i in range(n):
            if delay_fn is not None:
                d = delay_fn(i)
                if d > 0:
                    time.sleep(d)
            if self.size == self.capacity:
                ln_val = math.log(self.capacity + self.beta)
                g = 1.0 + self.alpha / ln_val
                g = min(self.g_max, max(self.g_min, g))
                new_cap = int(math.floor(self.capacity * g))
                new_cap = max(new_cap, self.capacity + 1)
                self._gf_hist.append(g)
                self._cap_hist.append(new_cap)
                self._resize_idx.append(i)
                self.total_copied += self.size
                self.capacity = new_cap
                self.resize_count += 1
            self.size += 1
        t1 = time.perf_counter()
        waste_pct = ((self.capacity - self.size) / self.capacity) * 100.0
        avg_gf = float(np.mean(self._gf_hist)) if self._gf_hist else 0.0
        return Phase2Result(
            strategy_name="",
            workload_name="",
            workload_size=n,
            final_capacity=self.capacity,
            final_size=self.size,
            resize_count=self.resize_count,
            total_copied=self.total_copied,
            memory_waste_pct=round(waste_pct, 4),
            exec_time_ms=round((t1 - t0) * 1000, 4),
            avg_growth_factor=round(avg_gf, 6),
            velocity_history=[],
            alpha_history=[self.alpha] * len(self._gf_hist),
            growth_factor_history=self._gf_hist,
            capacity_history=self._cap_hist,
            resize_insertion_indices=self._resize_idx,
        )


# ═══════════════════════════════════════════════════════════════════════
# 5.  WORKLOAD DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════
WORKLOAD_SIZE = 50_000  # kept moderate so bursty delays don't take forever


def _no_delay(i: int) -> float:
    return 0.0


def _slow_delay(i: int) -> float:
    """~100 us pause per insertion -> low velocity."""
    return 0.0001


def _bursty_delay(i: int) -> float:
    """Alternate: 5000 fast, then 5000 slow."""
    if (i // 5000) % 2 == 0:
        return 0.0          # burst
    return 0.0002           # slow


def _mixed_delay(i: int) -> float:
    """Gradual acceleration then deceleration."""
    cycle = i % 10000
    if cycle < 5000:
        return 0.0          # fast ramp
    return 0.00015          # slow ramp


WORKLOADS = [
    ("Fast",   WORKLOAD_SIZE, _no_delay),
    ("Slow",   WORKLOAD_SIZE, _slow_delay),
    ("Bursty", WORKLOAD_SIZE, _bursty_delay),
    ("Mixed",  WORKLOAD_SIZE, _mixed_delay),
]


# ═══════════════════════════════════════════════════════════════════════
# 6.  EXPERIMENT RUNNER
# ═══════════════════════════════════════════════════════════════════════
DEFAULT_CFG = Phase2Config(alpha_base=2.0, beta=2, k=0.001)


def run_experiments() -> list[Phase2Result]:
    results: list[Phase2Result] = []
    total = len(WORKLOADS) * 2
    run_num = 0

    for wl_name, wl_size, delay_fn in WORKLOADS:
        print(f"\n{'='*65}")
        print(f"  WORKLOAD: {wl_name} ({wl_size:,} insertions)")
        print(f"{'='*65}")

        # Phase 1 (constant alpha)
        run_num += 1
        print(f"  [{run_num}/{total}] Phase1 (const alpha={DEFAULT_CFG.alpha_base}) ...",
              end="", flush=True)
        p1 = Phase1Simulator(
            alpha=DEFAULT_CFG.alpha_base, beta=DEFAULT_CFG.beta,
            g_min=DEFAULT_CFG.g_min, g_max=DEFAULT_CFG.g_max,
        )
        r1 = p1.run(wl_size, delay_fn)
        r1.strategy_name = f"Phase1(a={DEFAULT_CFG.alpha_base})"
        r1.workload_name = wl_name
        results.append(r1)
        print(f"  done ({r1.exec_time_ms:.1f} ms)")

        # Phase 2 (workload-aware)
        run_num += 1
        print(f"  [{run_num}/{total}] Phase2 (adaptive, k={DEFAULT_CFG.k}) ...",
              end="", flush=True)
        p2 = Phase2Simulator(DEFAULT_CFG)
        r2 = p2.run(wl_size, delay_fn)
        r2.strategy_name = f"Phase2(ab={DEFAULT_CFG.alpha_base},k={DEFAULT_CFG.k})"
        r2.workload_name = wl_name
        results.append(r2)
        print(f"  done ({r2.exec_time_ms:.1f} ms)")

    return results


# ═══════════════════════════════════════════════════════════════════════
# 7.  CSV EXPORT
# ═══════════════════════════════════════════════════════════════════════
def export_csv(results: list[Phase2Result]):
    path = os.path.join(SCRIPT_DIR, "phase2_results.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "Strategy", "Workload", "Size", "FinalCap", "Resizes",
            "TotalCopied", "Waste%", "Time_ms",
            "AvgVelocity", "MaxVelocity", "AvgAlpha", "MaxAlpha", "AvgGrowthFactor",
        ])
        for r in results:
            w.writerow([
                r.strategy_name, r.workload_name, r.workload_size,
                r.final_capacity, r.resize_count, r.total_copied,
                r.memory_waste_pct, r.exec_time_ms,
                r.avg_velocity, r.max_velocity, r.avg_alpha, r.max_alpha,
                r.avg_growth_factor,
            ])
    print(f"\n  CSV saved -> {path}")


# ═══════════════════════════════════════════════════════════════════════
# 8.  CONSOLE SUMMARY
# ═══════════════════════════════════════════════════════════════════════
def print_summary(results: list[Phase2Result]):
    print(f"\n{'='*110}")
    print("  PHASE 2 RESULTS — Phase 1 (Constant Alpha) vs Phase 2 (Workload-Aware Alpha)")
    print(f"{'='*110}")
    hdr = (f"  {'Workload':<8} {'Strategy':<35} {'Resizes':>7} {'Copied':>10} "
           f"{'Waste%':>7} {'Time':>9} {'AvgVel':>10} {'AvgAlpha':>9} {'AvgGF':>7}")
    print(hdr)
    print(f"  {'-'*106}")
    for r in results:
        v_str = f"{r.avg_velocity:.0f}" if r.avg_velocity > 0 else "-"
        a_str = f"{r.avg_alpha:.3f}" if r.avg_alpha > 0 else "-"
        print(
            f"  {r.workload_name:<8} {r.strategy_name:<35} "
            f"{r.resize_count:>7,} {r.total_copied:>10,} "
            f"{r.memory_waste_pct:>6.2f}% {r.exec_time_ms:>8.1f}ms "
            f"{v_str:>10} {a_str:>9} {r.avg_growth_factor:>7.4f}"
        )
    print(f"{'='*110}")


# ═══════════════════════════════════════════════════════════════════════
# 9.  GRAPHS
# ═══════════════════════════════════════════════════════════════════════
C_BG   = "#1E1E2E"
C_GRID = "#3B3B5C"
C_TEXT = "#CDD6F4"
C_P1   = "#6C5CE7"   # purple for Phase 1
C_P2   = "#00CEC9"   # teal for Phase 2


def _style_ax(ax, title, xlabel, ylabel):
    ax.set_facecolor(C_BG)
    ax.set_title(title, color=C_TEXT, fontsize=11, fontweight="bold", pad=10)
    ax.set_xlabel(xlabel, color=C_TEXT, fontsize=9)
    ax.set_ylabel(ylabel, color=C_TEXT, fontsize=9)
    ax.tick_params(colors=C_TEXT, labelsize=7)
    ax.grid(True, color=C_GRID, linewidth=0.3, alpha=0.5)
    for spine in ax.spines.values():
        spine.set_color(C_GRID)


def plot_phase2_analysis(results: list[Phase2Result]):
    """Generate per-workload Phase 2 diagnostic graphs."""
    workload_names = list(dict.fromkeys(r.workload_name for r in results))

    for wl_name in workload_names:
        p1 = next((r for r in results
                    if r.workload_name == wl_name and "Phase1" in r.strategy_name), None)
        p2 = next((r for r in results
                    if r.workload_name == wl_name and "Phase2" in r.strategy_name), None)
        if not p2:
            continue

        fig, axes = plt.subplots(2, 3, figsize=(20, 10))
        fig.patch.set_facecolor("#11111B")
        fig.suptitle(
            f"Phase 2 Analysis — {wl_name} Workload ({p2.workload_size:,} insertions)",
            color=C_TEXT, fontsize=14, fontweight="bold", y=0.98,
        )

        idx = np.arange(len(p2.velocity_history))

        # 1. Velocity vs Resize Event
        ax = axes[0, 0]
        _style_ax(ax, "Smoothed Velocity vs Resize Event", "Resize #", "Velocity (ins/sec)")
        if p2.velocity_history:
            ax.plot(idx, p2.velocity_history, color="#FFA94D", linewidth=1.2)
            ax.fill_between(idx, 0, p2.velocity_history, color="#FFA94D", alpha=0.15)

        # 2. Alpha vs Resize Event
        ax = axes[0, 1]
        _style_ax(ax, "Adaptive Alpha vs Resize Event", "Resize #", "Alpha")
        if p2.alpha_history:
            ax.plot(idx, p2.alpha_history, color=C_P2, linewidth=1.5, label="Phase 2 (adaptive)")
        if p1 and p1.alpha_history:
            ax.axhline(y=p1.alpha_history[0], color=C_P1, linewidth=1.5,
                       linestyle="--", label="Phase 1 (constant)")
        ax.legend(fontsize=7, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)

        # 3. Growth Factor vs Resize Event
        ax = axes[0, 2]
        _style_ax(ax, "Growth Factor vs Resize Event", "Resize #", "g(C,v)")
        if p2.growth_factor_history:
            ax.plot(idx, p2.growth_factor_history, color=C_P2, linewidth=1.2,
                    label="Phase 2")
        if p1 and p1.growth_factor_history:
            idx1 = np.arange(len(p1.growth_factor_history))
            ax.plot(idx1, p1.growth_factor_history, color=C_P1, linewidth=1.2,
                    linestyle="--", label="Phase 1")
        ax.legend(fontsize=7, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)

        # 4. Velocity vs Alpha (scatter)
        ax = axes[1, 0]
        _style_ax(ax, "Velocity vs Alpha (Correlation)", "Velocity", "Alpha")
        if p2.velocity_history and p2.alpha_history:
            ax.scatter(p2.velocity_history, p2.alpha_history,
                       c="#FD79A8", s=12, alpha=0.7, edgecolors="none")

        # 5. Capacity Growth Over Time
        ax = axes[1, 1]
        _style_ax(ax, "Capacity Growth Over Insertions", "Resize #", "Capacity")
        if p2.capacity_history:
            ax.plot(idx, p2.capacity_history, color=C_P2, linewidth=1.5, label="Phase 2")
        if p1 and p1.capacity_history:
            idx1 = np.arange(len(p1.capacity_history))
            ax.plot(idx1, p1.capacity_history, color=C_P1, linewidth=1.5,
                    linestyle="--", label="Phase 1")
        ax.legend(fontsize=7, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)

        # 6. Summary comparison bar
        ax = axes[1, 2]
        _style_ax(ax, "Phase 1 vs Phase 2 Summary", "", "")
        metrics = ["Resizes", "Waste %", "Copies (K)"]
        p1_vals = [p1.resize_count, p1.memory_waste_pct,
                   p1.total_copied / 1000] if p1 else [0, 0, 0]
        p2_vals = [p2.resize_count, p2.memory_waste_pct, p2.total_copied / 1000]
        x_pos = np.arange(len(metrics))
        w = 0.35
        ax.bar(x_pos - w/2, p1_vals, w, color=C_P1, label="Phase 1", alpha=0.85)
        ax.bar(x_pos + w/2, p2_vals, w, color=C_P2, label="Phase 2", alpha=0.85)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(metrics, color=C_TEXT, fontsize=9)
        ax.legend(fontsize=8, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        fname = os.path.join(SCRIPT_DIR, f"phase2_{wl_name.lower()}.png")
        plt.savefig(fname, dpi=150, facecolor="#11111B", bbox_inches="tight")
        print(f"  Chart saved -> {fname}")
        plt.show()


# ═══════════════════════════════════════════════════════════════════════
# 10.  RESEARCH VALIDATION
# ═══════════════════════════════════════════════════════════════════════
def print_validation(results: list[Phase2Result]):
    print("\n" + "=" * 75)
    print("  RESEARCH VALIDATION")
    print("=" * 75)

    p2_results = [r for r in results if "Phase2" in r.strategy_name]

    fast  = next((r for r in p2_results if r.workload_name == "Fast"), None)
    slow  = next((r for r in p2_results if r.workload_name == "Slow"), None)
    burst = next((r for r in p2_results if r.workload_name == "Bursty"), None)

    checks = []
    if fast and slow:
        c1 = fast.avg_velocity > slow.avg_velocity
        checks.append(("Fast velocity > Slow velocity", c1,
                        f"{fast.avg_velocity:.0f} vs {slow.avg_velocity:.0f}"))
        c2 = fast.avg_alpha > slow.avg_alpha
        checks.append(("Fast avg_alpha > Slow avg_alpha", c2,
                        f"{fast.avg_alpha:.3f} vs {slow.avg_alpha:.3f}"))
        c3 = fast.avg_growth_factor > slow.avg_growth_factor
        checks.append(("Fast avg_gf > Slow avg_gf", c3,
                        f"{fast.avg_growth_factor:.4f} vs {slow.avg_growth_factor:.4f}"))
    if burst and slow:
        c4 = burst.max_alpha > slow.max_alpha
        checks.append(("Bursty max_alpha > Slow max_alpha", c4,
                        f"{burst.max_alpha:.3f} vs {slow.max_alpha:.3f}"))

    for desc, passed, detail in checks:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {desc}  ({detail})")

    print("=" * 75)


# ═══════════════════════════════════════════════════════════════════════
# 11.  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("  Formula A — Phase 2: Workload-Aware Alpha")
    print(f"  Config: alpha_base={DEFAULT_CFG.alpha_base}, beta={DEFAULT_CFG.beta}, "
          f"k={DEFAULT_CFG.k}, EMA={DEFAULT_CFG.velocity_smoothing_factor}")
    print("=" * 65)

    all_results = run_experiments()
    export_csv(all_results)
    print_summary(all_results)
    print_validation(all_results)

    print("\n  Generating Phase 2 graphs ...")
    plot_phase2_analysis(all_results)

    print("\n  All Phase 2 outputs generated. Done.\n")
