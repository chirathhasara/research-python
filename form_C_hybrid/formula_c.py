"""
Phase 3 Simulation: Formula C (Weighted Capacity-History Hybrid)
"""

import sys
import os
import math
import csv
import time
from dataclasses import dataclass, field
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# ═══════════════════════════════════════════════════════════════════════
# 1. WORKLOAD GENERATORS
# ═══════════════════════════════════════════════════════════════════════
def generate_constant_pattern(n: int, v: float) -> list[float]:
    return [i / v for i in range(n)]

def generate_accelerating_pattern(n: int, v_start: float, v_end: float) -> list[float]:
    dt_start = 1.0 / v_start
    dt_end = 1.0 / v_end
    t = 0.0
    timestamps = []
    for i in range(n):
        timestamps.append(t)
        progress = i / max(1, n - 1)
        dt = dt_start + progress * (dt_end - dt_start)
        t += dt
    return timestamps

def generate_spiky_pattern(n: int, v_base: float, v_spike: float, spike_freq: int, spike_len: int) -> list[float]:
    t = 0.0
    timestamps = []
    for i in range(n):
        timestamps.append(t)
        in_spike = (i % spike_freq) < spike_len
        dt = 1.0 / v_spike if in_spike else 1.0 / v_base
        t += dt
    return timestamps

# ═══════════════════════════════════════════════════════════════════════
# 2. SIMULATOR
# ═══════════════════════════════════════════════════════════════════════
@dataclass
class SimResult:
    strategy_name: str
    pattern_name: str
    workload: int
    final_capacity: int
    final_size: int
    resize_count: int
    total_copied: int
    memory_waste_pct: float

class DynamicArraySimulatorHybrid:
    def __init__(self, initial_capacity: int = 10):
        self.capacity = initial_capacity
        self.size = 0
        self.resize_count = 0
        self.total_copied = 0
        self.last_resize_size = 0
        self.last_resize_time = 0.0

    def run(self, timestamps: list[float], growth_fn) -> SimResult:
        n = len(timestamps)
        
        for i, t in enumerate(timestamps):
            if self.size == self.capacity:
                delta_n = self.size - self.last_resize_size
                delta_t = t - self.last_resize_time
                v = delta_n / delta_t if delta_t > 0 else float('inf')
                if v < 0: v = 0.0
                
                k = self.resize_count + 1
                new_cap = growth_fn(self.capacity, k, v)
                new_cap = max(new_cap, self.capacity + 1)
                
                self.total_copied += self.size
                self.capacity = new_cap
                self.resize_count += 1
                self.last_resize_size = self.size
                self.last_resize_time = t
                
            self.size += 1

        waste_pct = ((self.capacity - self.size) / self.capacity) * 100.0

        return SimResult(
            strategy_name="", pattern_name="", workload=n,
            final_capacity=self.capacity, final_size=self.size,
            resize_count=self.resize_count, total_copied=self.total_copied,
            memory_waste_pct=round(waste_pct, 4)
        )

# ═══════════════════════════════════════════════════════════════════════
# 3. GROWTH STRATEGIES
# ═══════════════════════════════════════════════════════════════════════
G_MIN, G_MAX = 1.1, 2.0

def make_formula_c_growth(w_A: float, w_B: float):
    alpha = 3.0
    beta = 5.0
    lam = 2.0
    mu = 1.0

    def growth_fn(capacity: int, k: int, v: float) -> int:
        if v == float('inf'):
            v_val = 10.0 # fallback
        else:
            v_val = v
            
        part_A = (alpha + lam * math.log(1 + v_val)) / math.log(capacity + beta)
        part_B = mu / k
        
        g = 1.0 + w_A * part_A + w_B * part_B
        return int(math.floor(capacity * min(G_MAX, max(G_MIN, g))))
    return growth_fn

def formula_a_phase2_best(capacity: int, k: int, v: float) -> int:
    lam = 1.0 # k parameter from Phase 2
    if v == float('inf'): v = 10.0
    g = 1.0 + (3.0 + lam * math.log(1 + v)) / math.log(capacity + 5)
    return int(math.floor(capacity * min(G_MAX, max(G_MIN, g))))

def formula_b_phase2_best(capacity: int, k: int, v: float) -> int:
    lam = 5.0 # lambda parameter from Phase 2 B
    if v == float('inf'): v = 10.0
    g = 1.0 + (1.0 + lam * math.log(1 + v)) / k
    return int(math.floor(capacity * min(G_MAX, max(G_MIN, g))))

def fixed_2x_growth(capacity: int, k: int, v: float) -> int: return capacity * 2
def fixed_1_5x_growth(capacity: int, k: int, v: float) -> int: return capacity + (capacity >> 1)

# ═══════════════════════════════════════════════════════════════════════
# 4. EXPERIMENT RUNNER
# ═══════════════════════════════════════════════════════════════════════
WORKLOADS = [100_000, 1_000_000]

def run_all_experiments():
    results = []
    patterns = {
        "Constant (v=10)": lambda n: generate_constant_pattern(n, 10.0),
        "High Vel (v=1000)": lambda n: generate_constant_pattern(n, 1000.0),
        "Accel (1->1000)": lambda n: generate_accelerating_pattern(n, 1.0, 1000.0),
        "Spiky": lambda n: generate_spiky_pattern(n, 10.0, 1000.0, n//10, n//50),
    }

    strats = [
        ("Fixed 2.0x", fixed_2x_growth),
        ("Fixed 1.5x", fixed_1_5x_growth),
        ("FA P2 (k=1.0)", formula_a_phase2_best),
        ("FB P2 (l=5.0)", formula_b_phase2_best),
        ("FC (0.8/0.2)", make_formula_c_growth(0.8, 0.2)),
        ("FC (0.7/0.3)", make_formula_c_growth(0.7, 0.3)),
        ("FC (0.6/0.4)", make_formula_c_growth(0.6, 0.4)),
    ]

    total = len(WORKLOADS) * len(patterns) * len(strats)
    run_num = 0

    for n in WORKLOADS:
        print("\n" + "="*80)
        print(f"  WORKLOAD: {n:>12,} insertions")
        print("="*80)
        
        for pat_name, pat_fn in patterns.items():
            timestamps = pat_fn(n)
                
            for strat_name, fn in strats:
                run_num += 1
                print(f"  [{run_num}/{total}] {pat_name} | {strat_name} ...", end="", flush=True)
                sim = DynamicArraySimulatorHybrid()
                res = sim.run(timestamps, fn)
                res.strategy_name = strat_name
                res.pattern_name = pat_name
                results.append(res)
                print(" done")
    return results

def export_csv(results):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "formula_c_results.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Pattern", "Strategy", "Workload", "Final_Capacity", "Final_Size", "Resize_Count", "Total_Copied", "Memory_Waste_Pct"])
        for r in results:
            writer.writerow([r.pattern_name, r.strategy_name, r.workload, r.final_capacity, r.final_size, r.resize_count, r.total_copied, r.memory_waste_pct])
    print(f"\n  CSV saved -> {path}")

def generate_report(results):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report.txt")
    with open(path, "w", encoding="utf-8") as f:
        for n in WORKLOADS:
            subset = [r for r in results if r.workload == n]
            f.write("\n" + "="*100 + "\n")
            f.write(f"  RESULTS TABLE  |  Workload = {n:,} insertions\n")
            f.write("="*100 + "\n")
            patterns = list(dict.fromkeys(r.pattern_name for r in subset))
            for pat in patterns:
                pat_rows = [r for r in subset if r.pattern_name == pat]
                f.write(f"\n  Pattern: {pat}\n")
                header = f"  {'Strategy':<28} {'Resizes':>8} {'Copied':>12} {'FinalCap':>12} {'Waste%':>8}\n"
                f.write(header)
                f.write("  " + "-"*96 + "\n")
                for r in pat_rows:
                    f.write(f"  {r.strategy_name:<28} {r.resize_count:>8,} {r.total_copied:>12,} {r.final_capacity:>12,} {r.memory_waste_pct:>7.2f}%\n")
            f.write("="*100 + "\n")
    print(f"  TXT Report saved -> {path}")

def plot_comparisons(results):
    for n in WORKLOADS:
        subset = [r for r in results if r.workload == n]
        patterns = list(dict.fromkeys(r.pattern_name for r in subset))
        
        fig, axes = plt.subplots(len(patterns), 2, figsize=(14, 4 * len(patterns)))
        fig.patch.set_facecolor("#11111B")
        fig.suptitle(f"Formula C (Weighted Hybrid) | N = {n:,}", color="#CDD6F4", fontsize=14, fontweight="bold", y=0.98)
                     
        if len(patterns) == 1: axes = [axes]
            
        for i, pat in enumerate(patterns):
            pat_res = [r for r in subset if r.pattern_name == pat]
            short_names = [r.strategy_name for r in pat_res]
            x = np.arange(len(short_names))
            
            for j, (metric, title, color) in enumerate([
                ([r.memory_waste_pct for r in pat_res], f"[{pat}] Waste (%)", "#FF6B6B"),
                ([r.total_copied for r in pat_res], f"[{pat}] Copies", "#4DABF7")
            ]):
                ax = axes[i][j]
                ax.set_facecolor("#1E1E2E")
                ax.set_title(title, color="#CDD6F4", fontsize=11)
                bars = ax.bar(x, metric, color=color)
                ax.set_xticks(x)
                ax.set_xticklabels(short_names, rotation=35, ha="right", color="#CDD6F4", fontsize=8)
                ax.tick_params(colors="#CDD6F4", labelsize=8)
                if j == 1: ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v>=1e6 else f"{v/1e3:.0f}K"))
                
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        fname = f"formula_c_comparison_{n}.png"
        plt.savefig(fname, dpi=150, facecolor="#11111B", bbox_inches="tight")
        print(f"  Chart saved -> {fname}")
        plt.close()

if __name__ == "__main__":
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    results = run_all_experiments()
    export_csv(results)
    generate_report(results)
    plot_comparisons(results)
