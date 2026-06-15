"""
Formula B: Harmonic Growth — Phase 2 (Workload-Aware Harmonic Growth)
======================================================================
Extends Phase 1 by integrating insertion velocity into Formula B.

    v = delta_N / delta_t                   (insertion velocity)
    v_smooth = ema_factor * v_prev + (1 - ema_factor) * v_current

    g(k,v) = min(g_max, max(g_min, 1 + (1 + lambda_param * ln(1 + v_smooth)) / k))
    C_new  = ceil(C_old * g(k,v))

Where `k` is the resize count (1-indexed).

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
class Phase2BConfig:
    """Tunable parameters for Formula B Phase 2."""
    lambda_param: float = 0.5          # workload sensitivity
    g_min: float = 1.1
    g_max: float = 2.0
    velocity_smoothing_factor: float = 0.9   # EMA factor
    initial_capacity: int = 10

    @property
    def label(self) -> str:
        return f"P2B(lambda={self.lambda_param},g_min={self.g_min})"


# ═══════════════════════════════════════════════════════════════════════
# 2.  RESULT DATACLASS
# ═══════════════════════════════════════════════════════════════════════
@dataclass
class Phase2BResult:
    strategy_name: str
    workload_name: str
    workload_size: int
    final_capacity: int
    final_size: int
    resize_count: int
    total_copied: int
    memory_waste_pct: float
    exec_time_ms: float
    avg_velocity: float = 0.0
    max_velocity: float = 0.0
    avg_numerator: float = 0.0
    max_numerator: float = 0.0
    avg_growth_factor: float = 0.0
    velocity_history: list = field(default_factory=list)
    numerator_history: list = field(default_factory=list)
    growth_factor_history: list = field(default_factory=list)
    capacity_history: list = field(default_factory=list)
    resize_insertion_indices: list = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════
# 3.  PHASE 2 SIMULATOR (Velocity-Aware)
# ═══════════════════════════════════════════════════════════════════════
class Phase2BSimulator:
    def __init__(self, cfg: Phase2BConfig):
        self.cfg = cfg
        self.capacity = cfg.initial_capacity
        self.size = 0
        self.resize_count = 0
        self.total_copied = 0

        self._last_resize_time: float = 0.0
        self._last_resize_size: int = 0
        self._v_smooth: float = 0.0

        self._vel_hist: list[float] = []
        self._num_hist: list[float] = []
        self._gf_hist: list[float] = []
        self._cap_hist: list[int] = []
        self._resize_idx: list[int] = []

    def run(self, n: int, delay_fn=None) -> Phase2BResult:
        self._last_resize_time = time.perf_counter()
        self._last_resize_size = 0

        t0 = time.perf_counter()

        for i in range(n):
            if delay_fn is not None:
                d = delay_fn(i)
                if d > 0:
                    time.sleep(d)

            if self.size == self.capacity:
                self.resize_count += 1
                self._do_resize(i)

            self.size += 1

        t1 = time.perf_counter()

        waste_pct = ((self.capacity - self.size) / self.capacity) * 100.0

        avg_v  = float(np.mean(self._vel_hist))  if self._vel_hist else 0.0
        max_v  = float(np.max(self._vel_hist))   if self._vel_hist else 0.0
        avg_n  = float(np.mean(self._num_hist))  if self._num_hist else 0.0
        max_n  = float(np.max(self._num_hist))   if self._num_hist else 0.0
        avg_gf = float(np.mean(self._gf_hist))   if self._gf_hist else 0.0

        return Phase2BResult(
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
            avg_numerator=round(avg_n, 4),
            max_numerator=round(max_n, 4),
            avg_growth_factor=round(avg_gf, 6),
            velocity_history=self._vel_hist,
            numerator_history=self._num_hist,
            growth_factor_history=self._gf_hist,
            capacity_history=self._cap_hist,
            resize_insertion_indices=self._resize_idx,
        )

    def _do_resize(self, insertion_idx: int):
        now = time.perf_counter()
        dt = now - self._last_resize_time
        dn = self.size - self._last_resize_size

        v_current = dn / dt if dt > 1e-12 else 0.0

        ema = self.cfg.velocity_smoothing_factor
        self._v_smooth = ema * self._v_smooth + (1.0 - ema) * v_current

        numerator = 1.0 + self.cfg.lambda_param * math.log(1.0 + self._v_smooth)
        
        g = 1.0 + numerator / self.resize_count
        g = min(self.cfg.g_max, max(self.cfg.g_min, g))

        new_cap = int(math.ceil(self.capacity * g))
        new_cap = max(new_cap, self.capacity + 1)

        self._vel_hist.append(self._v_smooth)
        self._num_hist.append(numerator)
        self._gf_hist.append(g)
        self._cap_hist.append(new_cap)
        self._resize_idx.append(insertion_idx)

        self.total_copied += self.size
        self.capacity = new_cap

        self._last_resize_time = now
        self._last_resize_size = self.size


# ═══════════════════════════════════════════════════════════════════════
# 4.  PHASE 1 SIMULATOR (Standard Harmonic for comparison)
# ═══════════════════════════════════════════════════════════════════════
class Phase1BSimulator:
    """Phase 1 Formula B (c=1.0) for side-by-side comparison."""
    def __init__(self, g_min: float = 1.1, g_max: float = 2.0, initial_capacity: int = 10):
        self.g_min = g_min
        self.g_max = g_max
        self.capacity = initial_capacity
        self.size = 0
        self.resize_count = 0
        self.total_copied = 0
        self._gf_hist: list[float] = []
        self._cap_hist: list[int] = []
        self._resize_idx: list[int] = []

    def run(self, n: int, delay_fn=None) -> Phase2BResult:
        t0 = time.perf_counter()
        for i in range(n):
            if delay_fn is not None:
                d = delay_fn(i)
                if d > 0:
                    time.sleep(d)
            if self.size == self.capacity:
                self.resize_count += 1
                g = 1.0 + 1.0 / self.resize_count
                g = min(self.g_max, max(self.g_min, g))
                new_cap = int(math.floor(self.capacity * g))
                new_cap = max(new_cap, self.capacity + 1)
                self._gf_hist.append(g)
                self._cap_hist.append(new_cap)
                self._resize_idx.append(i)
                self.total_copied += self.size
                self.capacity = new_cap
            self.size += 1
        t1 = time.perf_counter()
        waste_pct = ((self.capacity - self.size) / self.capacity) * 100.0
        avg_gf = float(np.mean(self._gf_hist)) if self._gf_hist else 0.0
        return Phase2BResult(
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
            numerator_history=[1.0] * len(self._gf_hist),
            growth_factor_history=self._gf_hist,
            capacity_history=self._cap_hist,
            resize_insertion_indices=self._resize_idx,
        )


# ═══════════════════════════════════════════════════════════════════════
# 5.  WORKLOAD DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════
WORKLOAD_SIZE = 50_000

def _no_delay(i: int) -> float: return 0.0
def _slow_delay(i: int) -> float: return 0.0001
def _bursty_delay(i: int) -> float: return 0.0 if (i // 5000) % 2 == 0 else 0.0002
def _mixed_delay(i: int) -> float: return 0.0 if (i % 10000) < 5000 else 0.00015

WORKLOADS = [
    ("Fast",   WORKLOAD_SIZE, _no_delay),
    ("Slow",   WORKLOAD_SIZE, _slow_delay),
    ("Bursty", WORKLOAD_SIZE, _bursty_delay),
    ("Mixed",  WORKLOAD_SIZE, _mixed_delay),
]


# ═══════════════════════════════════════════════════════════════════════
# 6.  EXPERIMENT RUNNER
# ═══════════════════════════════════════════════════════════════════════
DEFAULT_CFG = Phase2BConfig(lambda_param=0.5, g_min=1.2)

def run_experiments() -> list[Phase2BResult]:
    results: list[Phase2BResult] = []
    total = len(WORKLOADS) * 2
    run_num = 0

    for wl_name, wl_size, delay_fn in WORKLOADS:
        print(f"\n{'='*65}")
        print(f"  WORKLOAD: {wl_name} ({wl_size:,} insertions)")
        print(f"{'='*65}")

        # Phase 1
        run_num += 1
        print(f"  [{run_num}/{total}] Phase1 (c=1.0) ...", end="", flush=True)
        p1 = Phase1BSimulator(g_min=DEFAULT_CFG.g_min)
        r1 = p1.run(wl_size, delay_fn)
        r1.strategy_name = f"Phase1B(c=1.0,g_min={DEFAULT_CFG.g_min})"
        r1.workload_name = wl_name
        results.append(r1)
        print(f"  done ({r1.exec_time_ms:.1f} ms)")

        # Phase 2
        run_num += 1
        print(f"  [{run_num}/{total}] Phase2 (lambda={DEFAULT_CFG.lambda_param}) ...", end="", flush=True)
        p2 = Phase2BSimulator(DEFAULT_CFG)
        r2 = p2.run(wl_size, delay_fn)
        r2.strategy_name = f"Phase2B(L={DEFAULT_CFG.lambda_param},g_min={DEFAULT_CFG.g_min})"
        r2.workload_name = wl_name
        results.append(r2)
        print(f"  done ({r2.exec_time_ms:.1f} ms)")

    return results


# ═══════════════════════════════════════════════════════════════════════
# 7.  CSV EXPORT
# ═══════════════════════════════════════════════════════════════════════
def export_csv(results: list[Phase2BResult]):
    path = os.path.join(SCRIPT_DIR, "phase2b_results.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "Strategy", "Workload", "Size", "FinalCap", "Resizes",
            "TotalCopied", "Waste%", "Time_ms",
            "AvgVelocity", "MaxVelocity", "AvgNumerator", "MaxNumerator", "AvgGrowthFactor",
        ])
        for r in results:
            w.writerow([
                r.strategy_name, r.workload_name, r.workload_size,
                r.final_capacity, r.resize_count, r.total_copied,
                r.memory_waste_pct, r.exec_time_ms,
                r.avg_velocity, r.max_velocity, r.avg_numerator, r.max_numerator,
                r.avg_growth_factor,
            ])
    print(f"\n  CSV saved -> {path}")


# ═══════════════════════════════════════════════════════════════════════
# 8.  CONSOLE SUMMARY
# ═══════════════════════════════════════════════════════════════════════
def print_summary(results: list[Phase2BResult]):
    print(f"\n{'='*110}")
    print("  PHASE 2 RESULTS — Formula B: Standard vs Workload-Aware Harmonic Growth")
    print(f"{'='*110}")
    hdr = (f"  {'Workload':<8} {'Strategy':<30} {'Resizes':>7} {'Copied':>10} "
           f"{'Waste%':>7} {'Time':>9} {'AvgVel':>10} {'AvgNum':>8} {'AvgGF':>7}")
    print(hdr)
    print(f"  {'-'*106}")
    for r in results:
        v_str = f"{r.avg_velocity:.0f}" if r.avg_velocity > 0 else "-"
        n_str = f"{r.avg_numerator:.2f}" if r.avg_numerator > 0 else "-"
        print(
            f"  {r.workload_name:<8} {r.strategy_name:<30} "
            f"{r.resize_count:>7,} {r.total_copied:>10,} "
            f"{r.memory_waste_pct:>6.2f}% {r.exec_time_ms:>8.1f}ms "
            f"{v_str:>10} {n_str:>8} {r.avg_growth_factor:>7.4f}"
        )
    print(f"{'='*110}")


# ═══════════════════════════════════════════════════════════════════════
# 9.  GRAPHS
# ═══════════════════════════════════════════════════════════════════════
C_BG   = "#1E1E2E"
C_GRID = "#3B3B5C"
C_TEXT = "#CDD6F4"
C_P1   = "#6C5CE7"   # purple
C_P2   = "#00CEC9"   # teal

def _style_ax(ax, title, xlabel, ylabel):
    ax.set_facecolor(C_BG)
    ax.set_title(title, color=C_TEXT, fontsize=11, fontweight="bold", pad=10)
    ax.set_xlabel(xlabel, color=C_TEXT, fontsize=9)
    ax.set_ylabel(ylabel, color=C_TEXT, fontsize=9)
    ax.tick_params(colors=C_TEXT, labelsize=7)
    ax.grid(True, color=C_GRID, linewidth=0.3, alpha=0.5)
    for spine in ax.spines.values():
        spine.set_color(C_GRID)

def plot_phase2_analysis(results: list[Phase2BResult]):
    workload_names = list(dict.fromkeys(r.workload_name for r in results))

    for wl_name in workload_names:
        p1 = next((r for r in results if r.workload_name == wl_name and "Phase1" in r.strategy_name), None)
        p2 = next((r for r in results if r.workload_name == wl_name and "Phase2" in r.strategy_name), None)
        if not p2: continue

        fig, axes = plt.subplots(2, 3, figsize=(20, 10))
        fig.patch.set_facecolor("#11111B")
        fig.suptitle(
            f"Formula B (Phase 2) — {wl_name} Workload ({p2.workload_size:,} insertions)",
            color=C_TEXT, fontsize=14, fontweight="bold", y=0.98,
        )

        idx = np.arange(1, len(p2.velocity_history) + 1)

        # 1. Velocity
        ax = axes[0, 0]
        _style_ax(ax, "Smoothed Velocity vs Resize Event", "Resize Count (k)", "Velocity (ins/sec)")
        if p2.velocity_history:
            ax.plot(idx, p2.velocity_history, color="#FFA94D", linewidth=1.2)
            ax.fill_between(idx, 0, p2.velocity_history, color="#FFA94D", alpha=0.15)

        # 2. Numerator vs k
        ax = axes[0, 1]
        _style_ax(ax, "Numerator [1 + λ*ln(1+v)] vs Resize Event", "Resize Count (k)", "Numerator")
        if p2.numerator_history:
            ax.plot(idx, p2.numerator_history, color=C_P2, linewidth=1.5, label="Phase 2 (adaptive)")
        if p1 and p1.numerator_history:
            idx1 = np.arange(1, len(p1.numerator_history) + 1)
            ax.axhline(y=1.0, color=C_P1, linewidth=1.5, linestyle="--", label="Phase 1 (constant c=1)")
        ax.legend(fontsize=7, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)

        # 3. Growth Factor vs k
        ax = axes[0, 2]
        _style_ax(ax, "Growth Factor vs Resize Event", "Resize Count (k)", "g(k,v)")
        if p2.growth_factor_history:
            ax.plot(idx, p2.growth_factor_history, color=C_P2, linewidth=1.2, label="Phase 2")
        if p1 and p1.growth_factor_history:
            idx1 = np.arange(1, len(p1.growth_factor_history) + 1)
            ax.plot(idx1, p1.growth_factor_history, color=C_P1, linewidth=1.2, linestyle="--", label="Phase 1")
        ax.legend(fontsize=7, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)

        # 4. Velocity vs Numerator
        ax = axes[1, 0]
        _style_ax(ax, "Velocity vs Numerator (Correlation)", "Velocity", "Numerator")
        if p2.velocity_history and p2.numerator_history:
            ax.scatter(p2.velocity_history, p2.numerator_history, c="#FD79A8", s=12, alpha=0.7)

        # 5. Capacity Growth
        ax = axes[1, 1]
        _style_ax(ax, "Capacity Growth Over Insertions", "Resize Count (k)", "Capacity")
        if p2.capacity_history:
            ax.plot(idx, p2.capacity_history, color=C_P2, linewidth=1.5, label="Phase 2")
        if p1 and p1.capacity_history:
            idx1 = np.arange(1, len(p1.capacity_history) + 1)
            ax.plot(idx1, p1.capacity_history, color=C_P1, linewidth=1.5, linestyle="--", label="Phase 1")
        ax.legend(fontsize=7, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)

        # 6. Bar summary
        ax = axes[1, 2]
        _style_ax(ax, "Phase 1 vs Phase 2 Summary", "", "")
        metrics = ["Resizes", "Waste %", "Copies (K)"]
        p1_vals = [p1.resize_count, p1.memory_waste_pct, p1.total_copied / 1000] if p1 else [0, 0, 0]
        p2_vals = [p2.resize_count, p2.memory_waste_pct, p2.total_copied / 1000]
        x_pos = np.arange(len(metrics))
        w = 0.35
        ax.bar(x_pos - w/2, p1_vals, w, color=C_P1, label="Phase 1", alpha=0.85)
        ax.bar(x_pos + w/2, p2_vals, w, color=C_P2, label="Phase 2", alpha=0.85)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(metrics, color=C_TEXT, fontsize=9)
        ax.legend(fontsize=8, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        fname = os.path.join(SCRIPT_DIR, f"phase2b_{wl_name.lower()}.png")
        plt.savefig(fname, dpi=150, facecolor="#11111B", bbox_inches="tight")
        print(f"  Chart saved -> {fname}")
        plt.close()


if __name__ == "__main__":
    all_results = run_experiments()
    export_csv(all_results)
    print_summary(all_results)
    print("\n  Generating Phase 2 graphs ...")
    plot_phase2_analysis(all_results)
    print("\n  All Phase 2 outputs generated. Done.\n")
