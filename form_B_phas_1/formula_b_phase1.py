"""
Formula B: Harmonic Sequence Growth — Phase 1
==================================================================
Implements and evaluates the growth formula from the research document:

    g(k) = min(g_max, max(g_min, 1 + c / k))
    C_new = floor(C_old * g(k))

Parameters tested:
    c  : 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0
    g_min  : 1.1
    g_max  : 2.0

Baselines:
    Fixed 2.0x growth
    Fixed 1.5x growth
    Formula A best baseline (a=3.5, b=10)

Workloads:
    10,000 / 100,000 / 1,000,000 insertions
"""

import sys
import os
import time
import csv
import math
from dataclasses import dataclass, field

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

@dataclass
class SimResult:
    strategy_name: str
    c_val: float
    workload: int
    final_capacity: int
    final_size: int
    resize_count: int
    total_copied: int
    memory_waste_pct: float
    exec_time_ms: float

class DynamicArraySimulator:
    def __init__(self, initial_capacity: int = 10):
        self.capacity = initial_capacity
        self.size = 0
        self.resize_count = 0
        self.total_copied = 0

    def run(self, n: int, growth_fn) -> SimResult:
        t0 = time.perf_counter()
        for _ in range(n):
            if self.size == self.capacity:
                k = self.resize_count + 1
                new_cap = growth_fn(self.capacity, k)
                new_cap = max(new_cap, self.capacity + 1)
                self.total_copied += self.size
                self.capacity = new_cap
                self.resize_count += 1
            self.size += 1
        t1 = time.perf_counter()
        waste_pct = ((self.capacity - self.size) / self.capacity) * 100.0
        return SimResult(
            strategy_name="", c_val=0.0, workload=n,
            final_capacity=self.capacity, final_size=self.size,
            resize_count=self.resize_count, total_copied=self.total_copied,
            memory_waste_pct=round(waste_pct, 4), exec_time_ms=round((t1 - t0)*1000, 4)
        )

G_MIN, G_MAX = 1.1, 2.0

def make_formula_b_growth(c: float):
    def growth_fn(capacity: int, k: int) -> int:
        g = 1.0 + c / k
        return int(math.floor(capacity * min(G_MAX, max(G_MIN, g))))
    return growth_fn

def formula_a_best(capacity: int, k: int) -> int:
    g = 1.0 + 3.5 / math.log(capacity + 10)
    return int(math.floor(capacity * min(G_MAX, max(G_MIN, g))))

def fixed_2x_growth(capacity: int, k: int) -> int: return capacity * 2
def fixed_1_5x_growth(capacity: int, k: int) -> int: return capacity + (capacity >> 1)

C_VALUES = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
WORKLOADS = [10_000, 100_000, 1_000_000]

def run_all_experiments():
    results = []
    total = len(WORKLOADS) * (3 + len(C_VALUES))
    run_num = 0

    for n in WORKLOADS:
        print("\n" + "="*80)
        print(f"  WORKLOAD: {n:>12,} insertions")
        print("="*80)
        
        strats = [
            ("Fixed 2.0x", fixed_2x_growth, 0.0),
            ("Fixed 1.5x", fixed_1_5x_growth, 0.0),
            ("Formula A (a=3.5,b=10)", formula_a_best, 0.0)
        ]
        strats += [(f"Formula B (c={c})", make_formula_b_growth(c), c) for c in C_VALUES]
            
        for strat_name, fn, c_val in strats:
            run_num += 1
            print(f"  [{run_num}/{total}] {strat_name} ...", end="", flush=True)
            sim = DynamicArraySimulator()
            res = sim.run(n, fn)
            res.strategy_name = strat_name
            res.c_val = c_val
            results.append(res)
            print(" done")
    return results

def export_csv(results):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "formula_b_results.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Strategy", "C_Value", "Workload", "Final_Capacity", "Final_Size", "Resize_Count", "Total_Copied", "Memory_Waste_Pct"])
        for r in results:
            writer.writerow([r.strategy_name, r.c_val, r.workload, r.final_capacity, r.final_size, r.resize_count, r.total_copied, r.memory_waste_pct])
    print(f"\n  CSV saved -> {path}")

def plot_comparisons(results):
    for n in WORKLOADS:
        subset = [r for r in results if r.workload == n]
        names = [r.strategy_name.replace("Formula B", "FB").replace("Formula A", "FA") for r in subset]
        wastes = [r.memory_waste_pct for r in subset]
        copies = [r.total_copied for r in subset]
        x = np.arange(len(names))
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.patch.set_facecolor("#11111B")
        fig.suptitle(f"Formula B (Harmonic) Phase 1 | N = {n:,}", color="#CDD6F4", fontsize=14, fontweight="bold", y=1.02)
        
        ax1 = axes[0]
        ax1.set_facecolor("#1E1E2E")
        ax1.set_title("Memory Waste (%)", color="#CDD6F4")
        bars1 = ax1.bar(x, wastes, color="#FF6B6B")
        ax1.set_xticks(x)
        ax1.set_xticklabels(names, rotation=45, ha="right", color="#CDD6F4", fontsize=9)
        ax1.tick_params(colors="#CDD6F4")
        for bar in bars1:
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{bar.get_height():.1f}%", ha="center", va="bottom", fontsize=8, color="#CDD6F4")
            
        ax2 = axes[1]
        ax2.set_facecolor("#1E1E2E")
        ax2.set_title("Total Elements Copied", color="#CDD6F4")
        bars2 = ax2.bar(x, copies, color="#4DABF7")
        ax2.set_xticks(x)
        ax2.set_xticklabels(names, rotation=45, ha="right", color="#CDD6F4", fontsize=9)
        ax2.tick_params(colors="#CDD6F4")
        ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v>=1e6 else f"{v/1e3:.0f}K"))
        
        plt.tight_layout()
        fname = f"formula_b_comparison_{n}.png"
        plt.savefig(fname, dpi=150, facecolor="#11111B", bbox_inches="tight")
        print(f"  Chart saved -> {fname}")
        plt.close()

def generate_report(results):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report.txt")
    with open(path, "w", encoding="utf-8") as f:
        for n in WORKLOADS:
            subset = [r for r in results if r.workload == n]
            f.write("\n" + "="*100 + "\n")
            f.write(f"  RESULTS TABLE  |  Workload = {n:,} insertions\n")
            f.write("="*100 + "\n")
            header = f"  {'Strategy':<28} {'Resizes':>8} {'Copied':>12} {'FinalCap':>12} {'Waste%':>8}\n"
            f.write(header)
            f.write("  " + "-"*96 + "\n")
            for r in subset:
                f.write(f"  {r.strategy_name:<28} {r.resize_count:>8,} {r.total_copied:>12,} {r.final_capacity:>12,} {r.memory_waste_pct:>7.2f}%\n")
            f.write("="*100 + "\n")
    print(f"  TXT Report saved -> {path}")

if __name__ == "__main__":
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    results = run_all_experiments()
    export_csv(results)
    generate_report(results)
    plot_comparisons(results)
