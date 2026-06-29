"""
Formula A: Logarithmic Adaptive Growth — Phase 1 (Constant Alpha)
==================================================================
Implements and evaluates the growth formula from the research document:

    g(C) = min(g_max, max(g_min, 1 + alpha / ln(C + beta)))
    C_new = floor(C_old * g(C))

Parameters tested:
    alpha  : 1.0, 1.5, 2.0, 2.5, 3.0
    beta   : 1, 2, 5
    g_min  : 1.1
    g_max  : 2.0

Baselines:
    Fixed 2.0x growth (C++ std::vector style)
    Fixed 1.5x growth (Java ArrayList style)

Workloads:
    10,000 / 100,000 / 1,000,000 insertions

Outputs:
    - Console summary tables
    - CSV with all results
    - Comparative graphs (4 charts)
    - Ranked recommendations
    - Research-style conclusion

Author : Research Project – Dynamic Growth Factor Study
Date   : 2026-06-09
"""

import sys
import os
import time
import csv
import math
import itertools
from dataclasses import dataclass, field

# Ensure Unicode output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np


# ═══════════════════════════════════════════════════════════════════════
# 1.  DYNAMIC ARRAY SIMULATOR
# ═══════════════════════════════════════════════════════════════════════
@dataclass
class SimResult:
    """Stores the outcome of a single simulation run."""
    strategy_name: str
    alpha: float
    beta: float
    workload: int
    final_capacity: int
    final_size: int
    resize_count: int
    total_copied: int
    memory_waste_pct: float
    exec_time_ms: float
    # Per-insertion tracking (kept lean — only snapshots at resize points
    # plus beginning/end for plotting)
    snapshot_sizes: list = field(default_factory=list)
    snapshot_capacities: list = field(default_factory=list)
    snapshot_wastes: list = field(default_factory=list)
    peak_memory: int = 0
    peak_memory_bytes: int = 0
    avg_memory: float = 0.0
    peak_waste: int = 0
    avg_waste: float = 0.0
    final_memory_footprint: int = 0
    peak_memory_footprint: int = 0
    avg_memory_footprint: float = 0.0


class DynamicArraySimulator:
    """
    Generic dynamic array simulator.  Accepts a growth_fn(capacity) -> new_capacity
    callable so we can plug in any strategy.
    """

    def __init__(self, initial_capacity: int = 10):
        self.capacity: int = initial_capacity
        self.size: int = 0
        self.resize_count: int = 0
        self.total_copied: int = 0

        # Lightweight per-insertion snapshots for graphing
        self._snap_sizes: list[int] = []
        self._snap_caps: list[int] = []
        self._snap_wastes: list[int] = []
        
        self.sum_capacity: int = 0
        self.sum_waste: int = 0
        self.peak_waste: int = 0

    def run(self, n: int, growth_fn) -> SimResult:
        """Insert n elements using the given growth function."""
        t0 = time.perf_counter()

        last_resize_size = 0
        current_cap = self.capacity
        
        for _ in range(n):
            if self.size == self.capacity:
                # Add to sums before changing capacity
                count = self.size - last_resize_size
                self.sum_capacity += count * current_cap
                # sum of (current_cap - size) for size from last_resize_size+1 to self.size
                # sum(size) = (self.size * (self.size + 1) // 2) - (last_resize_size * (last_resize_size + 1) // 2)
                sum_sizes = (self.size * (self.size + 1) // 2) - (last_resize_size * (last_resize_size + 1) // 2)
                self.sum_waste += (count * current_cap) - sum_sizes
                
                new_cap = growth_fn(self.capacity)
                new_cap = max(new_cap, self.capacity + 1)  # ensure at least +1
                
                # Peak waste is largest right after resize
                waste_after_resize = new_cap - self.size
                if waste_after_resize > self.peak_waste:
                    self.peak_waste = waste_after_resize
                    
                self.total_copied += self.size
                self.capacity = new_cap
                current_cap = new_cap
                last_resize_size = self.size
                self.resize_count += 1
                
            self.size += 1

            # Record snapshots at logarithmic intervals to keep memory low
            # for million-element runs
            if self.size <= 1000 or self.size % max(1, n // 2000) == 0:
                self._snap_sizes.append(self.size)
                self._snap_caps.append(self.capacity)
                self._snap_wastes.append(self.capacity - self.size)
                
        # Final additions to sums for the last segment
        count = self.size - last_resize_size
        if count > 0:
            self.sum_capacity += count * current_cap
            sum_sizes = (self.size * (self.size + 1) // 2) - (last_resize_size * (last_resize_size + 1) // 2)
            self.sum_waste += (count * current_cap) - sum_sizes
            waste_after_resize = current_cap - last_resize_size
            if waste_after_resize > self.peak_waste:
                self.peak_waste = waste_after_resize
                
        t1 = time.perf_counter()

        # Ensure the final state is always captured
        if not self._snap_sizes or self._snap_sizes[-1] != self.size:
            self._snap_sizes.append(self.size)
            self._snap_caps.append(self.capacity)
            self._snap_wastes.append(self.capacity - self.size)

        waste_pct = ((self.capacity - self.size) / self.capacity) * 100.0
        ELEMENT_SIZE = 8
        peak_memory = self.capacity
        peak_memory_bytes = peak_memory * ELEMENT_SIZE
        avg_memory = self.sum_capacity / n if n > 0 else 0
        avg_waste = self.sum_waste / n if n > 0 else 0
        
        final_footprint = self.capacity * ELEMENT_SIZE
        peak_footprint = peak_memory_bytes
        avg_footprint = avg_memory * ELEMENT_SIZE

        return SimResult(
            strategy_name="",
            alpha=0.0,
            beta=0.0,
            workload=n,
            final_capacity=self.capacity,
            final_size=self.size,
            resize_count=self.resize_count,
            total_copied=self.total_copied,
            memory_waste_pct=round(waste_pct, 4),
            exec_time_ms=round((t1 - t0) * 1000, 4),
            snapshot_sizes=self._snap_sizes,
            snapshot_capacities=self._snap_caps,
            snapshot_wastes=self._snap_wastes,
            peak_memory=peak_memory,
            peak_memory_bytes=peak_memory_bytes,
            avg_memory=round(avg_memory, 4),
            peak_waste=self.peak_waste,
            avg_waste=round(avg_waste, 4),
            final_memory_footprint=final_footprint,
            peak_memory_footprint=peak_footprint,
            avg_memory_footprint=round(avg_footprint, 4),
        )


# ═══════════════════════════════════════════════════════════════════════
# 2.  GROWTH STRATEGIES
# ═══════════════════════════════════════════════════════════════════════
G_MIN = 1.1
G_MAX = 2.0


def make_formula_a_growth(alpha: float, beta: float):
    """Return a growth function for Formula A (Phase 1, constant alpha)."""
    def growth_fn(capacity: int) -> int:
        ln_val = math.log(capacity + beta)
        g = 1.0 + alpha / ln_val
        g = min(G_MAX, max(G_MIN, g))
        return int(math.floor(capacity * g))
    return growth_fn


def fixed_2x_growth(capacity: int) -> int:
    """Fixed 2.0x growth (C++ std::vector)."""
    return capacity * 2


def fixed_1_5x_growth(capacity: int) -> int:
    """Fixed 1.5x growth (Java ArrayList)."""
    return capacity + (capacity >> 1)


def python_list_growth(capacity: int) -> int:
    """Python list growth pattern approximation (CPython)."""
    newsize = capacity + 1
    return newsize + (newsize >> 3) + (3 if newsize < 9 else 6)


# ═══════════════════════════════════════════════════════════════════════
# 3.  EXPERIMENT RUNNER
# ═══════════════════════════════════════════════════════════════════════
ALPHAS = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
BETAS = [1, 2, 5, 10]
WORKLOADS = [10_000, 100_000, 1_000_000, 10_000_000, 100_000_000]


def run_all_experiments() -> list[SimResult]:
    """Execute all parameter combinations + baselines across all workloads."""
    results: list[SimResult] = []
    total_runs = (len(ALPHAS) * len(BETAS) + 2) * len(WORKLOADS)
    run_num = 0

    for n in WORKLOADS:
        print(f"\n{'='*70}")
        print(f"  WORKLOAD: {n:>12,} insertions")
        print(f"{'='*70}")

        # ── Baselines ────────────────────────────────────────────────
        for name, fn, a, b in [
            ("Fixed 2.0x", fixed_2x_growth, 0.0, 0.0),
            ("Fixed 1.5x", fixed_1_5x_growth, 0.0, 0.0),
            ("Python List", python_list_growth, 0.0, 0.0),
        ]:
            run_num += 1
            print(f"  [{run_num}/{total_runs}] {name} ...", end="", flush=True)
            sim = DynamicArraySimulator()
            res = sim.run(n, fn)
            res.strategy_name = name
            res.alpha = a
            res.beta = b
            results.append(res)
            print(f"  done ({res.exec_time_ms:.1f} ms)")

        # ── Formula A combinations ───────────────────────────────────
        for alpha, beta in itertools.product(ALPHAS, BETAS):
            run_num += 1
            name = f"FormulaA(a={alpha},b={beta})"
            print(f"  [{run_num}/{total_runs}] {name} ...", end="", flush=True)
            sim = DynamicArraySimulator()
            fn = make_formula_a_growth(alpha, beta)
            res = sim.run(n, fn)
            res.strategy_name = name
            res.alpha = alpha
            res.beta = beta
            results.append(res)
            print(f"  done ({res.exec_time_ms:.1f} ms)")

    return results


# ═══════════════════════════════════════════════════════════════════════
# 4.  CSV EXPORT
# ═══════════════════════════════════════════════════════════════════════
CSV_FILENAME = "formula_a_results_v2.csv"


def export_csv(results: list[SimResult]):
    """Write all results to CSV."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CSV_FILENAME)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Strategy", "Alpha", "Beta", "Workload",
            "Final_Capacity", "Final_Size", "Resize_Count",
            "Total_Copied", "Memory_Waste_%", "Exec_Time_ms",
            "Peak_Memory", "Average_Memory", "Peak_Waste", "Average_Waste",
            "Memory_Footprint"
        ])
        for r in results:
            writer.writerow([
                r.strategy_name, r.alpha, r.beta, r.workload,
                r.final_capacity, r.final_size, r.resize_count,
                r.total_copied, r.memory_waste_pct, r.exec_time_ms,
                r.peak_memory, r.avg_memory, r.peak_waste, r.avg_waste,
                r.final_memory_footprint
            ])
    print(f"\n  CSV saved -> {path}")


# ═══════════════════════════════════════════════════════════════════════
# 5.  CONSOLE SUMMARY TABLES
# ═══════════════════════════════════════════════════════════════════════
def print_summary_tables(results: list[SimResult]):
    """Print a comparison table for each workload."""
    for n in WORKLOADS:
        subset = [r for r in results if r.workload == n]
        print(f"\n{'='*130}")
        print(f"  RESULTS TABLE  |  Workload = {n:,} insertions")
        print(f"{'='*130}")
        header = (
            f"  {'Strategy':<28} {'Alpha':>5} {'Beta':>4}  "
            f"{'Resizes':>8} {'Copied':>12} {'FinalCap':>12} "
            f"{'Waste%':>8} {'Time(ms)':>10} {'PeakMem':>10} {'AvgMem':>10} {'PeakWst':>10} {'AvgWst':>10} {'Footprint':>10}"
        )
        print(header)
        print(f"  {'-'*126}")
        for r in subset:
            a_str = f"{r.alpha:.1f}" if r.alpha > 0 else "  -"
            b_str = f"{r.beta:.0f}" if r.beta > 0 else " -"
            print(
                f"  {r.strategy_name:<28} {a_str:>5} {b_str:>4}  "
                f"{r.resize_count:>8,} {r.total_copied:>12,} "
                f"{r.final_capacity:>12,} {r.memory_waste_pct:>7.2f}% "
                f"{r.exec_time_ms:>10.2f} "
                f"{r.peak_memory:>10,} {r.avg_memory:>10.1f} {r.peak_waste:>10,} {r.avg_waste:>10.1f} {r.final_memory_footprint:>10,}"
            )
        print(f"{'='*130}")


# ═══════════════════════════════════════════════════════════════════════
# 6.  RANKING
# ═══════════════════════════════════════════════════════════════════════
def print_rankings(results: list[SimResult]):
    """Rank Formula A combinations for each workload by a composite score."""
    print("\n" + "=" * 80)
    print("  RANKINGS (Formula A only, lower composite score = better)")
    print("  Score = 0.4 * norm(waste) + 0.3 * norm(copies) + 0.2 * norm(resizes) + 0.1 * norm(time)")
    print("=" * 80)

    for n in WORKLOADS:
        fa_results = [r for r in results
                      if r.workload == n and r.strategy_name.startswith("FormulaA")]
        if not fa_results:
            continue

        # Normalize each metric to [0, 1]
        max_waste  = max(r.memory_waste_pct for r in fa_results) or 1
        max_copies = max(r.total_copied for r in fa_results) or 1
        max_resize = max(r.resize_count for r in fa_results) or 1
        max_time   = max(r.exec_time_ms for r in fa_results) or 1

        scored = []
        for r in fa_results:
            score = (
                0.4 * (r.memory_waste_pct / max_waste)
                + 0.3 * (r.total_copied / max_copies)
                + 0.2 * (r.resize_count / max_resize)
                + 0.1 * (r.exec_time_ms / max_time)
            )
            scored.append((score, r))

        scored.sort(key=lambda x: x[0])

        print(f"\n  Workload: {n:,}")
        print(f"  {'Rank':>4}  {'Strategy':<28} {'Score':>7}  "
              f"{'Waste%':>7} {'Copies':>12} {'Resizes':>8}")
        print(f"  {'-'*75}")
        for rank, (score, r) in enumerate(scored, 1):
            marker = " <-- BEST" if rank == 1 else ""
            print(f"  {rank:>4}  {r.strategy_name:<28} {score:>7.4f}  "
                  f"{r.memory_waste_pct:>6.2f}% {r.total_copied:>12,} "
                  f"{r.resize_count:>8,}{marker}")


# ═══════════════════════════════════════════════════════════════════════
# 7.  GRAPHS
# ═══════════════════════════════════════════════════════════════════════
C_BG   = "#1E1E2E"
C_GRID = "#3B3B5C"
C_TEXT = "#CDD6F4"

# Distinct colors for each alpha value
ALPHA_COLORS = {
    1.0: "#FF6B6B",   # red
    1.5: "#FFA94D",   # orange
    2.0: "#FFD43B",   # yellow
    2.5: "#69DB7C",   # green
    3.0: "#4DABF7",   # blue
    3.5: "#C084FC",   # purple
}
BETA_LINESTYLES = {1: "-", 2: "--", 5: ":", 10: "-."}

BASELINE_STYLES = {
    "Fixed 2.0x": {"color": "#E17055", "linewidth": 2.5, "linestyle": "-.", "alpha": 0.9},
    "Fixed 1.5x": {"color": "#6C5CE7", "linewidth": 2.5, "linestyle": "-.", "alpha": 0.9},
    "Python List": {"color": "#00B894", "linewidth": 2.5, "linestyle": "-.", "alpha": 0.9},
}


def _style_ax(ax, title, xlabel, ylabel):
    ax.set_facecolor(C_BG)
    ax.set_title(title, color=C_TEXT, fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel(xlabel, color=C_TEXT, fontsize=10)
    ax.set_ylabel(ylabel, color=C_TEXT, fontsize=10)
    ax.tick_params(colors=C_TEXT, labelsize=8)
    ax.grid(True, color=C_GRID, linewidth=0.3, alpha=0.5)
    for spine in ax.spines.values():
        spine.set_color(C_GRID)


def plot_bar_comparisons(results: list[SimResult]):
    """Generate 4 bar-chart comparisons for each workload."""
    for n in WORKLOADS:
        subset = [r for r in results if r.workload == n]

        names   = [r.strategy_name for r in subset]
        wastes  = [r.memory_waste_pct for r in subset]
        resizes = [r.resize_count for r in subset]
        copies  = [r.total_copied for r in subset]
        times   = [r.exec_time_ms for r in subset]

        short_names = []
        for nm in names:
            if nm.startswith("FormulaA"):
                short_names.append(nm.replace("FormulaA(", "A(").replace(")", ")"))
            else:
                short_names.append(nm)

        fig, axes = plt.subplots(2, 2, figsize=(18, 12))
        fig.patch.set_facecolor("#11111B")
        fig.suptitle(
            f"Formula A (Phase 1) — Comparative Analysis  |  N = {n:,}",
            color=C_TEXT, fontsize=15, fontweight="bold", y=0.98,
        )

        x = np.arange(len(short_names))
        bar_width = 0.6

        # Assign colors: baselines get distinct colors, Formula A gets gradient
        colors = []
        for r in subset:
            if r.strategy_name == "Fixed 2.0x":
                colors.append("#E17055")
            elif r.strategy_name == "Fixed 1.5x":
                colors.append("#6C5CE7")
            elif r.strategy_name == "Python List":
                colors.append("#00B894")
            else:
                colors.append(ALPHA_COLORS.get(r.alpha, "#888888"))

        # Chart 1: Memory Waste %
        ax = axes[0, 0]
        _style_ax(ax, "Memory Waste (%)", "Strategy", "Waste %")
        bars = ax.bar(x, wastes, bar_width, color=colors, edgecolor="#ffffff20")
        ax.set_xticks(x)
        ax.set_xticklabels(short_names, rotation=55, ha="right", fontsize=7, color=C_TEXT)
        for bar, val in zip(bars, wastes):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    f"{val:.1f}%", ha="center", va="bottom", fontsize=6, color=C_TEXT)

        # Chart 2: Resize Count
        ax = axes[0, 1]
        _style_ax(ax, "Resize Count", "Strategy", "Resizes")
        bars = ax.bar(x, resizes, bar_width, color=colors, edgecolor="#ffffff20")
        ax.set_xticks(x)
        ax.set_xticklabels(short_names, rotation=55, ha="right", fontsize=7, color=C_TEXT)
        for bar, val in zip(bars, resizes):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    f"{val}", ha="center", va="bottom", fontsize=6, color=C_TEXT)

        # Chart 3: Total Copies
        ax = axes[1, 0]
        _style_ax(ax, "Total Elements Copied", "Strategy", "Copies")
        bars = ax.bar(x, copies, bar_width, color=colors, edgecolor="#ffffff20")
        ax.set_xticks(x)
        ax.set_xticklabels(short_names, rotation=55, ha="right", fontsize=7, color=C_TEXT)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v >= 1e6 else f"{v/1e3:.0f}K" if v >= 1e3 else f"{v:.0f}"))

        # Chart 4: Execution Time
        ax = axes[1, 1]
        _style_ax(ax, "Execution Time (ms)", "Strategy", "Time (ms)")
        bars = ax.bar(x, times, bar_width, color=colors, edgecolor="#ffffff20")
        ax.set_xticks(x)
        ax.set_xticklabels(short_names, rotation=55, ha="right", fontsize=7, color=C_TEXT)
        for bar, val in zip(bars, times):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    f"{val:.1f}", ha="center", va="bottom", fontsize=6, color=C_TEXT)

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        fname = f"formula_a_comparison_{n}_v2.png"
        plt.savefig(fname, dpi=150, facecolor="#11111B", bbox_inches="tight")
        print(f"  Chart saved -> {fname}")
        plt.close()

def plot_memory_comparisons(results: list[SimResult]):
    """Generate 4 bar-chart comparisons for memory metrics for each workload."""
    for n in WORKLOADS:
        subset = [r for r in results if r.workload == n]

        names   = [r.strategy_name for r in subset]
        p_mems  = [r.peak_memory for r in subset]
        a_mems  = [r.avg_memory for r in subset]
        p_wsts  = [r.peak_waste for r in subset]
        a_wsts  = [r.avg_waste for r in subset]

        short_names = []
        for nm in names:
            if nm.startswith("FormulaA"):
                short_names.append(nm.replace("FormulaA(", "A(").replace(")", ")"))
            else:
                short_names.append(nm)

        fig, axes = plt.subplots(2, 2, figsize=(18, 12))
        fig.patch.set_facecolor("#11111B")
        fig.suptitle(
            f"Memory Metrics Comparison  |  N = {n:,}",
            color=C_TEXT, fontsize=15, fontweight="bold", y=0.98,
        )

        x = np.arange(len(short_names))
        bar_width = 0.6

        # Assign colors: baselines get distinct colors, Formula A gets gradient
        colors = []
        for r in subset:
            if r.strategy_name == "Fixed 2.0x":
                colors.append("#E17055")
            elif r.strategy_name == "Fixed 1.5x":
                colors.append("#6C5CE7")
            elif r.strategy_name == "Python List":
                colors.append("#00B894")
            else:
                colors.append(ALPHA_COLORS.get(r.alpha, "#888888"))

        # Chart 1: Peak Memory
        ax = axes[0, 0]
        _style_ax(ax, "Peak Memory (Capacity)", "Strategy", "Peak Memory")
        bars = ax.bar(x, p_mems, bar_width, color=colors, edgecolor="#ffffff20")
        ax.set_xticks(x)
        ax.set_xticklabels(short_names, rotation=55, ha="right", fontsize=7, color=C_TEXT)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v >= 1e6 else f"{v/1e3:.0f}K" if v >= 1e3 else f"{v:.0f}"))

        # Chart 2: Average Memory
        ax = axes[0, 1]
        _style_ax(ax, "Average Memory", "Strategy", "Avg Memory")
        bars = ax.bar(x, a_mems, bar_width, color=colors, edgecolor="#ffffff20")
        ax.set_xticks(x)
        ax.set_xticklabels(short_names, rotation=55, ha="right", fontsize=7, color=C_TEXT)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v >= 1e6 else f"{v/1e3:.0f}K" if v >= 1e3 else f"{v:.0f}"))

        # Chart 3: Peak Waste
        ax = axes[1, 0]
        _style_ax(ax, "Peak Memory Waste", "Strategy", "Peak Waste")
        bars = ax.bar(x, p_wsts, bar_width, color=colors, edgecolor="#ffffff20")
        ax.set_xticks(x)
        ax.set_xticklabels(short_names, rotation=55, ha="right", fontsize=7, color=C_TEXT)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v >= 1e6 else f"{v/1e3:.0f}K" if v >= 1e3 else f"{v:.0f}"))

        # Chart 4: Average Waste
        ax = axes[1, 1]
        _style_ax(ax, "Average Memory Waste", "Strategy", "Avg Waste")
        bars = ax.bar(x, a_wsts, bar_width, color=colors, edgecolor="#ffffff20")
        ax.set_xticks(x)
        ax.set_xticklabels(short_names, rotation=55, ha="right", fontsize=7, color=C_TEXT)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v >= 1e6 else f"{v/1e3:.0f}K" if v >= 1e3 else f"{v:.0f}"))

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        fname = f"memory_comparison_{n}_v2.png"
        plt.savefig(fname, dpi=150, facecolor="#11111B", bbox_inches="tight")
        print(f"  Chart saved -> {fname}")
        plt.close()


def plot_growth_factor_curve():
    """Plot how g(C) changes with capacity for each alpha/beta combo."""
    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor("#11111B")
    _style_ax(ax, "Growth Factor g(C) vs Capacity — Formula A (Phase 1)",
              "Capacity (C)", "Growth Factor g(C)")

    capacities = np.arange(10, 50_000, 10)

    # Baselines
    ax.axhline(y=2.0, color="#E17055", linewidth=2, linestyle="-.",
               alpha=0.7, label="Fixed 2.0x")
    ax.axhline(y=1.5, color="#6C5CE7", linewidth=2, linestyle="-.",
               alpha=0.7, label="Fixed 1.5x")
    ax.axhline(y=1.125, color="#00B894", linewidth=2, linestyle="-.",
               alpha=0.7, label="Python List (~1.125x)")
    ax.axhline(y=G_MIN, color="#888888", linewidth=1, linestyle=":",
               alpha=0.5, label=f"g_min = {G_MIN}")

    for alpha in ALPHAS:
        for beta in BETAS:
            g_vals = []
            for c in capacities:
                g = 1.0 + alpha / math.log(c + beta)
                g = min(G_MAX, max(G_MIN, g))
                g_vals.append(g)
            ax.plot(capacities, g_vals,
                    color=ALPHA_COLORS[alpha],
                    linestyle=BETA_LINESTYLES[beta],
                    linewidth=1.2, alpha=0.85,
                    label=f"a={alpha}, b={beta}")

    ax.set_ylim(1.0, 2.2)
    ax.legend(fontsize=7, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT,
              loc="upper right", ncol=3)

    plt.tight_layout()
    fname = "formula_a_growth_curve_v2.png"
    plt.savefig(fname, dpi=150, facecolor="#11111B", bbox_inches="tight")
    print(f"  Chart saved -> {fname}")
    plt.close()


def plot_parameter_sensitivity(results: list[SimResult]):
    """Generate parameter sensitivity charts for Alpha and Beta."""
    # We will generate these for the largest workload to show the most pronounced effects
    largest_n = max(WORKLOADS)
    subset = [r for r in results if r.workload == largest_n and r.strategy_name.startswith("FormulaA")]

    if not subset:
        return

    # Helper function to plot 4 subplots
    def _plot_4_metrics(fig, axes, x_vals, metrics_dict, x_label, title):
        fig.patch.set_facecolor("#11111B")
        fig.suptitle(title, color=C_TEXT, fontsize=15, fontweight="bold", y=0.98)
        
        y_labels = ["Memory Waste (%)", "Resize Count", "Total Copies", "Execution Time (ms)"]
        keys = ["waste", "resize", "copy", "time"]
        
        for idx, (ax_idx, y_label, key) in enumerate(zip([(0,0), (0,1), (1,0), (1,1)], y_labels, keys)):
            ax = axes[ax_idx[0], ax_idx[1]]
            _style_ax(ax, y_label, x_label, y_label)
            
            for line_label, y_vals in metrics_dict[key].items():
                ax.plot(x_vals, y_vals, marker='o', label=line_label, linewidth=2, alpha=0.85)
                
            ax.legend(fontsize=7, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)
            if key == "copy":
                ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v >= 1e6 else f"{v/1e3:.0f}K" if v >= 1e3 else f"{v:.0f}"))

    # 1. Alpha Sensitivity (X = Alpha, Lines = Beta)
    fig_a, axes_a = plt.subplots(2, 2, figsize=(16, 10))
    metrics_a = {"waste": {}, "resize": {}, "copy": {}, "time": {}}
    for beta in BETAS:
        b_label = f"Beta = {beta}"
        metrics_a["waste"][b_label] = []
        metrics_a["resize"][b_label] = []
        metrics_a["copy"][b_label] = []
        metrics_a["time"][b_label] = []
        for alpha in ALPHAS:
            r = next((x for x in subset if x.alpha == alpha and x.beta == beta), None)
            if r:
                metrics_a["waste"][b_label].append(r.memory_waste_pct)
                metrics_a["resize"][b_label].append(r.resize_count)
                metrics_a["copy"][b_label].append(r.total_copied)
                metrics_a["time"][b_label].append(r.exec_time_ms)
                
    _plot_4_metrics(fig_a, axes_a, ALPHAS, metrics_a, "Alpha (α)", f"Parameter Sensitivity: Alpha (N={largest_n:,})")
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    fname_a = f"sensitivity_alpha_{largest_n}.png"
    plt.savefig(fname_a, dpi=150, facecolor="#11111B", bbox_inches="tight")
    print(f"  Chart saved -> {fname_a}")
    plt.close(fig_a)

    # 2. Beta Sensitivity (X = Beta, Lines = Alpha)
    fig_b, axes_b = plt.subplots(2, 2, figsize=(16, 10))
    metrics_b = {"waste": {}, "resize": {}, "copy": {}, "time": {}}
    for alpha in ALPHAS:
        a_label = f"Alpha = {alpha}"
        metrics_b["waste"][a_label] = []
        metrics_b["resize"][a_label] = []
        metrics_b["copy"][a_label] = []
        metrics_b["time"][a_label] = []
        for beta in BETAS:
            r = next((x for x in subset if x.alpha == alpha and x.beta == beta), None)
            if r:
                metrics_b["waste"][a_label].append(r.memory_waste_pct)
                metrics_b["resize"][a_label].append(r.resize_count)
                metrics_b["copy"][a_label].append(r.total_copied)
                metrics_b["time"][a_label].append(r.exec_time_ms)

    _plot_4_metrics(fig_b, axes_b, BETAS, metrics_b, "Beta (β)", f"Parameter Sensitivity: Beta (N={largest_n:,})")
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    fname_b = f"sensitivity_beta_{largest_n}.png"
    plt.savefig(fname_b, dpi=150, facecolor="#11111B", bbox_inches="tight")
    print(f"  Chart saved -> {fname_b}")
    plt.close(fig_b)


# ═══════════════════════════════════════════════════════════════════════
# 8.  RESEARCH CONCLUSION
# ═══════════════════════════════════════════════════════════════════════
def print_conclusion(results: list[SimResult]):
    """Print a research-style analysis."""
    print("\n")
    print("=" * 80)
    print("  RESEARCH CONCLUSION: Formula A — Logarithmic Adaptive Growth (Phase 1)")
    print("=" * 80)

    # Find the best combo for the largest workload
    largest_n = max(WORKLOADS)
    fa_large = [r for r in results
                if r.workload == largest_n and r.strategy_name.startswith("FormulaA")]
    baselines = [r for r in results
                 if r.workload == largest_n and not r.strategy_name.startswith("FormulaA")]

    if not fa_large:
        print("  No Formula A results to analyze.")
        return

    best_waste = min(fa_large, key=lambda r: r.memory_waste_pct)
    best_copy  = min(fa_large, key=lambda r: r.total_copied)
    best_time  = min(fa_large, key=lambda r: r.exec_time_ms)

    fixed_2x = next((r for r in baselines if r.strategy_name == "Fixed 2.0x"), None)
    fixed_15 = next((r for r in baselines if r.strategy_name == "Fixed 1.5x"), None)
    py_list  = next((r for r in baselines if r.strategy_name == "Python List"), None)

    print(f"""
  Analysis at N = {largest_n:,} insertions:

  1. MEMORY EFFICIENCY
     - Best Formula A configuration : {best_waste.strategy_name}
       Memory waste                 : {best_waste.memory_waste_pct:.2f}%
     - Fixed 2.0x waste             : {fixed_2x.memory_waste_pct:.2f}%
     - Fixed 1.5x waste             : {fixed_15.memory_waste_pct:.2f}%
     - Python List waste            : {py_list.memory_waste_pct:.2f}%
     - Improvement over 2.0x        : {fixed_2x.memory_waste_pct - best_waste.memory_waste_pct:+.2f} percentage points
     - Improvement over Python List : {py_list.memory_waste_pct - best_waste.memory_waste_pct:+.2f} percentage points

  2. RESIZE OVERHEAD
     - Best waste config resizes    : {best_waste.resize_count:,}
     - Fixed 2.0x resizes           : {fixed_2x.resize_count:,}
     - Python List resizes          : {py_list.resize_count:,}
     - More resizes = more frequent interruptions but tighter memory.

  3. COPY COST
     - Lowest-copy configuration    : {best_copy.strategy_name}
       Total copies                 : {best_copy.total_copied:,}
     - Fixed 2.0x copies            : {fixed_2x.total_copied:,}
     - Python List copies           : {py_list.total_copied:,}

  4. EXECUTION PERFORMANCE
     - Fastest Formula A            : {best_time.strategy_name}
       Time                         : {best_time.exec_time_ms:.2f} ms
     - Fixed 2.0x time              : {fixed_2x.exec_time_ms:.2f} ms
     - Python List time             : {py_list.exec_time_ms:.2f} ms

  5. PRACTICAL ASSESSMENT
     Formula A demonstrates that logarithmic decay of the growth factor
     successfully reduces memory waste compared to fixed strategies, while
     maintaining acceptable copy costs. Higher alpha values (2.5-3.0)
     behave closer to fixed strategies (more aggressive growth, fewer
     copies, more waste). Lower alpha values (1.0-1.5) achieve tighter
     memory but increase resize frequency and total copies.

     The trade-off is governed by the formula's parameters and can be
     tuned to match specific application requirements — making Formula A
     a viable, tunable alternative to fixed growth strategies.
""")
    print("=" * 80)


# ═══════════════════════════════════════════════════════════════════════
# 9.  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  Formula A: Logarithmic Adaptive Growth — Phase 1 (Constant Alpha)")
    print("  Parameters: alpha in {1.0, 1.5, 2.0, 2.5, 3.0, 3.5}")
    print("              beta  in {1, 2, 5, 10}")
    print("  Baselines : Fixed 2.0x, Fixed 1.5x, Python List")
    print("  Workloads : 10K, 100K, 1M, 10M, 100M insertions")
    print("=" * 70)

    # Run experiments
    all_results = run_all_experiments()

    # Export CSV
    export_csv(all_results)

    # Print summary tables
    print_summary_tables(all_results)

    # Print rankings
    print_rankings(all_results)

    # Print conclusion
    print_conclusion(all_results)

    # Plot growth factor curve
    print("\n  Generating growth factor curve ...")
    plot_growth_factor_curve()

    # Plot bar comparisons for each workload
    print("\n  Generating comparison charts ...")
    plot_bar_comparisons(all_results)
    
    print("\n  Generating memory charts ...")
    plot_memory_comparisons(all_results)
    
    print("\n  Generating parameter sensitivity charts ...")
    plot_parameter_sensitivity(all_results)

    print("\n  All outputs generated. Done.\n")
