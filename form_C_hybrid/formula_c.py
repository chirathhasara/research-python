"""
Formula C: Workload-Aware Hybrid Growth Strategy
"""

import sys
import os
import math
import csv
import time
import random
from dataclasses import dataclass, field
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# ═══════════════════════════════════════════════════════════════════════
# 1. WORKLOAD GENERATORS
# ═══════════════════════════════════════════════════════════════════════
def generate_uniform_pattern(n: int) -> list[float]:
    v = 100.0
    return [i / v for i in range(n)]

def generate_increasing_pattern(n: int) -> list[float]:
    v_start, v_end = 10.0, 1000.0
    dt_start, dt_end = 1.0 / v_start, 1.0 / v_end
    progress = np.linspace(0, 1, n)
    dts = dt_start + progress * (dt_end - dt_start)
    return np.cumsum(dts).tolist()

def generate_decreasing_pattern(n: int) -> list[float]:
    v_start, v_end = 1000.0, 10.0
    dt_start, dt_end = 1.0 / v_start, 1.0 / v_end
    progress = np.linspace(0, 1, n)
    dts = dt_start + progress * (dt_end - dt_start)
    return np.cumsum(dts).tolist()

def generate_burst_pattern(n: int) -> list[float]:
    v_base, v_burst = 10.0, 1000.0
    dts = np.full(n, 1.0 / v_base)
    burst_starts = np.random.choice(n, size=n//100, replace=False)
    for start in burst_starts:
        dts[start:min(n, start + 50)] = 1.0 / v_burst
    return np.cumsum(dts).tolist()

def generate_random_pattern(n: int) -> list[float]:
    v_min, v_max = 10.0, 1000.0
    vs = np.random.uniform(v_min, v_max, n)
    dts = 1.0 / vs
    return np.cumsum(dts).tolist()

def generate_periodic_pattern(n: int) -> list[float]:
    v_low, v_high, period_len = 10.0, 1000.0, max(1, n//20)
    dts = np.empty(n)
    for i in range(0, n, period_len * 2):
        dts[i:i+period_len] = 1.0 / v_high
        dts[i+period_len:i+period_len*2] = 1.0 / v_low
    return np.cumsum(dts).tolist()

def generate_mixed_pattern(n: int) -> list[float]:
    phase_len = max(1, n // 3)
    dts1 = np.full(phase_len, 1.0 / 100.0)
    dts2 = np.full(phase_len, 1.0 / 10.0)
    burst_starts = np.random.choice(phase_len, size=phase_len//100, replace=False)
    for start in burst_starts:
        dts2[start:min(phase_len, start + 50)] = 1.0 / 1000.0
    rem = n - 2 * phase_len
    dts3 = 1.0 / np.random.uniform(10.0, 500.0, rem)
    dts = np.concatenate([dts1, dts2, dts3])
    return np.cumsum(dts).tolist()

# ═══════════════════════════════════════════════════════════════════════
# 2. SIMULATOR
# ═══════════════════════════════════════════════════════════════════════
@dataclass
class SimResult:
    strategy_name: str
    pattern_name: str
    weight_a: float
    weight_b: float
    lambda_val: float
    workload: int
    final_capacity: int
    final_size: int
    resize_count: int
    total_copied: int
    memory_waste_pct: float
    exec_time_ms: float = 0.0
    throughput: float = 0.0
    avg_latency: float = 0.0
    peak_memory: int = 0
    avg_memory: float = 0.0
    peak_waste: int = 0
    avg_waste: float = 0.0
    memory_footprint: int = 0
    avg_growth_factor: float = 0.0
    max_growth_factor: float = 0.0
    min_growth_factor: float = 0.0
    avg_velocity: float = 0.0
    max_velocity: float = 0.0
    min_velocity: float = 0.0

class DynamicArraySimulatorPhase2:
    def __init__(self, initial_capacity: int = 10):
        self.capacity = initial_capacity
        self.size = 0
        self.resize_count = 0
        self.total_copied = 0
        self.last_resize_size = 0
        self.last_resize_time = 0.0

    def run(self, timestamps: list[float], growth_fn) -> SimResult:
        n = len(timestamps)
        t_start = time.perf_counter()
        
        current_cap = self.capacity
        last_resize_size = 0
        sum_capacity = 0
        sum_waste = 0
        peak_waste = 0
        
        g_sum = 0.0; g_max = 0.0; g_min = float('inf'); g_count = 0
        v_sum = 0.0; v_max = 0.0; v_min = float('inf'); v_count = 0

        for i, t in enumerate(timestamps):
            if self.size == self.capacity:
                delta_n = self.size - last_resize_size
                delta_t = t - self.last_resize_time
                v = delta_n / delta_t if delta_t > 0 else float('inf')
                if v < 0: v = 0.0
                
                v_sum += v
                if v > v_max: v_max = v
                if v < v_min: v_min = v
                v_count += 1
                
                new_cap = growth_fn(self.capacity, self.resize_count + 1, v)
                new_cap = max(new_cap, self.capacity + 1)
                
                g = new_cap / self.capacity
                g_sum += g
                if g > g_max: g_max = g
                if g < g_min: g_min = g
                g_count += 1
                
                count = self.size - last_resize_size
                sum_capacity += count * current_cap
                sum_sizes = (self.size * (self.size + 1) // 2) - (last_resize_size * (last_resize_size + 1) // 2)
                sum_waste += (count * current_cap) - sum_sizes
                
                waste_after_resize = new_cap - self.size
                if waste_after_resize > peak_waste:
                    peak_waste = waste_after_resize
                
                self.total_copied += self.size
                self.capacity = new_cap
                current_cap = new_cap
                self.resize_count += 1
                self.last_resize_size = self.size
                self.last_resize_time = t
                
            self.size += 1

        count = self.size - self.last_resize_size
        if count > 0:
            sum_capacity += count * current_cap
            sum_sizes = (self.size * (self.size + 1) // 2) - (self.last_resize_size * (self.last_resize_size + 1) // 2)
            sum_waste += (count * current_cap) - sum_sizes
            waste_after = current_cap - self.last_resize_size
            if waste_after > peak_waste:
                peak_waste = waste_after

        t_end = time.perf_counter()
        
        exec_time = (t_end - t_start) * 1000
        throughput = n / (exec_time / 1000) if exec_time > 0 else 0
        avg_latency = (exec_time / n) * 1e6 if n > 0 else 0
        waste_pct = ((self.capacity - self.size) / self.capacity) * 100.0
        
        return SimResult(
            strategy_name="", pattern_name="", weight_a=0.0, weight_b=0.0, lambda_val=0.0, workload=n,
            final_capacity=self.capacity, final_size=self.size,
            resize_count=self.resize_count, total_copied=self.total_copied,
            memory_waste_pct=round(waste_pct, 4),
            exec_time_ms=round(exec_time, 4),
            throughput=round(throughput, 2),
            avg_latency=round(avg_latency, 2),
            peak_memory=self.capacity,
            avg_memory=round(sum_capacity / n if n > 0 else 0, 2),
            peak_waste=peak_waste,
            avg_waste=round(sum_waste / n if n > 0 else 0, 2),
            memory_footprint=self.capacity * 8,
            avg_growth_factor=round(g_sum / g_count if g_count > 0 else 0, 4),
            max_growth_factor=round(g_max if g_count > 0 else 0, 4),
            min_growth_factor=round(g_min if g_count > 0 else 0, 4),
            avg_velocity=round(v_sum / v_count if v_count > 0 else 0, 2),
            max_velocity=round(v_max if v_count > 0 else 0, 2),
            min_velocity=round(v_min if v_count > 0 else 0, 2)
        )

# ═══════════════════════════════════════════════════════════════════════
# 3. GROWTH STRATEGIES
# ═══════════════════════════════════════════════════════════════════════
G_MIN, G_MAX = 1.1, 2.0

# Fixed Best Values
ALPHA0 = 2.5
BETA = 15.0
C0 = 2.0

def make_formula_c(wa: float, lam: float):
    wb = 1.0 - wa
    def growth_fn(capacity: int, k: int, v: float) -> int:
        if v == float('inf'): v = 1000.0
        term_a = (ALPHA0 + lam * math.log(1 + v)) / math.log(capacity + BETA)
        term_b = (C0 + lam * math.log(1 + v)) / k
        g = 1.0 + wa * term_a + wb * term_b
        return int(math.floor(capacity * min(G_MAX, max(G_MIN, g))))
    return growth_fn

def make_formula_b_phase2(c0: float, lam: float):
    def growth_fn(capacity: int, k: int, v: float) -> int:
        if v == float('inf'): v = 1000.0
        c_v = c0 + lam * math.log(1 + v)
        g = 1.0 + c_v / k
        return int(math.floor(capacity * min(G_MAX, max(G_MIN, g))))
    return growth_fn

def make_formula_b_phase1(c0: float):
    def growth_fn(capacity: int, k: int, v: float) -> int:
        g = 1.0 + c0 / k
        return int(math.floor(capacity * min(G_MAX, max(G_MIN, g))))
    return growth_fn

def formula_a_phase1(capacity: int, k: int, v: float) -> int:
    g = 1.0 + 3.5 / math.log(capacity + 10)
    return int(math.floor(capacity * min(G_MAX, max(G_MIN, g))))

def formula_a_phase2(capacity: int, k: int, v: float) -> int:
    if v == float('inf'): v = 1000.0
    alpha_v = 2.5 + 0.5 * math.log(1 + v)
    g = 1.0 + alpha_v / math.log(capacity + 15)
    return int(math.floor(capacity * min(G_MAX, max(G_MIN, g))))

def fixed_2x_growth(capacity: int, k: int, v: float) -> int: return capacity * 2
def fixed_1_5x_growth(capacity: int, k: int, v: float) -> int: return capacity + (capacity >> 1)
def python_list_growth(capacity: int, k: int, v: float) -> int: 
    newsize = capacity + 1
    return newsize + (newsize >> 3) + (3 if newsize < 9 else 6)

# ═══════════════════════════════════════════════════════════════════════
# 4. EXPERIMENT RUNNER
# ═══════════════════════════════════════════════════════════════════════
WORKLOADS = [10_000, 100_000, 1_000_000, 10_000_000]
WEIGHT_A_VALUES = [1.0, 0.8, 0.6, 0.5, 0.4, 0.2, 0.0]
LAMBDA_VALUES = [0.1, 0.5, 1.0, 2.0, 5.0]

def run_all_experiments():
    results = []
    patterns = {
        "Uniform": generate_uniform_pattern,
        "Increasing": generate_increasing_pattern,
        "Decreasing": generate_decreasing_pattern,
        "Burst": generate_burst_pattern,
        "Random": generate_random_pattern,
        "Periodic": generate_periodic_pattern,
        "Mixed": generate_mixed_pattern
    }

    total_strats = 7 + len(WEIGHT_A_VALUES) * len(LAMBDA_VALUES)
    
    for n in WORKLOADS:
        print("\n" + "="*80)
        print(f"  WORKLOAD: {n:>12,} insertions")
        print("="*80)
        
        for pat_name, pat_fn in patterns.items():
            print(f"\n  --- Generating timestamps for {pat_name} ---")
            timestamps = pat_fn(n)
            
            strats = [
                ("Fixed 2.0x", fixed_2x_growth, 0.0, 0.0),
                ("Fixed 1.5x", fixed_1_5x_growth, 0.0, 0.0),
                ("Python List", python_list_growth, 0.0, 0.0),
                ("Formula A Phase 1", formula_a_phase1, 0.0, 0.0),
                ("Formula A Phase 2", formula_a_phase2, 0.0, 0.0),
                ("Formula B Phase 1", make_formula_b_phase1(C0), 0.0, 0.0),
                ("Formula B Phase 2", make_formula_b_phase2(C0, 1.0), 0.0, 0.0)
            ]
            
            for wa in WEIGHT_A_VALUES:
                for lam in LAMBDA_VALUES:
                    strats.append((f"Formula C (wa={wa},lam={lam})", make_formula_c(wa, lam), wa, lam))
                        
            run_num = 0
            for strat_name, fn, wa, lam in strats:
                run_num += 1
                if run_num % 10 == 0 or "Fixed" in strat_name:
                    print(f"  [{run_num}/{total_strats}] {pat_name} | {strat_name} ...", end="", flush=True)
                sim = DynamicArraySimulatorPhase2()
                res = sim.run(timestamps, fn)
                res.strategy_name = strat_name
                res.pattern_name = pat_name
                res.weight_a = wa
                res.weight_b = 1.0 - wa
                res.lambda_val = lam
                results.append(res)
                if run_num % 10 == 0 or "Fixed" in strat_name:
                    print(f" done ({res.exec_time_ms:.1f} ms)")
    return results

def export_csv(results):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "formula_c_results.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Pattern", "Strategy", "Weight_A", "Weight_B", "Lambda", "Workload", 
            "Execution Time", "Throughput", "Average Latency", "Resize Count", 
            "Total Copied", "Memory Waste", "Peak Memory", "Average Memory", 
            "Peak Waste", "Average Waste", "Memory Footprint", 
            "Average Growth Factor", "Maximum Growth Factor", "Minimum Growth Factor", 
            "Average Velocity", "Maximum Velocity", "Minimum Velocity"
        ])
        for r in results:
            writer.writerow([
                r.pattern_name, r.strategy_name, r.weight_a, r.weight_b, r.lambda_val, r.workload,
                r.exec_time_ms, r.throughput, r.avg_latency, r.resize_count,
                r.total_copied, r.memory_waste_pct, r.peak_memory, r.avg_memory,
                r.peak_waste, r.avg_waste, r.memory_footprint,
                r.avg_growth_factor, r.max_growth_factor, r.min_growth_factor,
                r.avg_velocity, r.max_velocity, r.min_velocity
            ])
    print(f"\n  CSV saved -> {path}")

def print_summary_tables(results):
    print("\n" + "="*80)
    print("  AUTOMATIC ANALYSIS & KEY FINDINGS")
    print("="*80)
    for n in WORKLOADS:
        subset = [r for r in results if r.workload == n and r.strategy_name.startswith("Formula C")]
        if not subset: continue
        patterns = list(dict.fromkeys(r.pattern_name for r in subset))
        print(f"\nWorkload: {n:,}")
        for pat in patterns:
            pat_res = [r for r in subset if r.pattern_name == pat]
            best_waste = min(pat_res, key=lambda x: x.memory_waste_pct)
            fastest = min(pat_res, key=lambda x: x.exec_time_ms)
            lowest_copy = min(pat_res, key=lambda x: x.total_copied)
            lowest_resize = min(pat_res, key=lambda x: x.resize_count)
            highest_tp = max(pat_res, key=lambda x: x.throughput)
            print(f"  Pattern: {pat}")
            print(f"    Best Weight A       : {best_waste.weight_a} (WB={best_waste.weight_b})")
            print(f"    Best Lambda         : {best_waste.lambda_val}")
            print(f"    Lowest Memory Waste : {best_waste.strategy_name} ({best_waste.memory_waste_pct}%)")
            print(f"    Fastest Strategy    : {fastest.strategy_name} ({fastest.exec_time_ms} ms)")
            print(f"    Lowest Copy Cost    : {lowest_copy.strategy_name} ({lowest_copy.total_copied:,})")
            print(f"    Lowest Resize Count : {lowest_resize.strategy_name} ({lowest_resize.resize_count})")
            print(f"    Highest Throughput  : {highest_tp.strategy_name} ({highest_tp.throughput:,}/s)")
            print(f"    Best Overall FC     : Formula C (wa={best_waste.weight_a}, lam={best_waste.lambda_val})")

def plot_all_comparisons(results):
    metrics_to_plot = {
        "Memory Waste": lambda r: r.memory_waste_pct,
        "Total Copied": lambda r: r.total_copied,
        "Resize Count": lambda r: r.resize_count,
        "Execution Time": lambda r: r.exec_time_ms,
        "Throughput": lambda r: r.throughput,
        "Peak Memory": lambda r: r.peak_memory,
        "Average Memory": lambda r: r.avg_memory
    }
    
    largest_n = max(WORKLOADS)
    subset = [r for r in results if r.workload == largest_n]
    if not subset: return
    
    # We will plot Overall Comparison specifically on the Mixed workload 
    # to avoid plotting hundreds of charts.
    pat = "Mixed"
    pat_res = [r for r in subset if r.pattern_name == pat]
    if not pat_res: pat_res = subset
    
    pat_res.sort(key=lambda x: x.memory_waste_pct)
    display_res = [r for r in pat_res if not r.strategy_name.startswith("Formula C")]
    fc_res = [r for r in pat_res if r.strategy_name.startswith("Formula C")]
    display_res += fc_res[:5] # Top 5 FC
    
    for metric_name, metric_fn in metrics_to_plot.items():
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor("#11111B")
        fig.suptitle(f"{metric_name} Comparison | N={largest_n:,} ({pat})", color="#CDD6F4", fontsize=14, y=0.98)
        
        names = [r.strategy_name.replace("Formula C", "FC").replace("Formula B Phase 2", "FB P2").replace("Formula A Phase 2", "FA P2").replace("Formula A Phase 1", "FA P1").replace("Formula B Phase 1", "FB P1") for r in display_res]
        vals = [metric_fn(r) for r in display_res]
        
        ax.set_facecolor("#1E1E2E")
        ax.bar(names, vals, color="#FF6B6B" if "Waste" in metric_name else "#4DABF7")
        ax.set_xticklabels(names, rotation=25, ha="right", color="#CDD6F4", fontsize=8)
        ax.tick_params(colors="#CDD6F4")
        if "Copied" in metric_name or "Memory" in metric_name and "Waste" not in metric_name:
            ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v>=1e6 else f"{v/1e3:.0f}K" if v>=1e3 else f"{v}"))
            
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        clean_name = metric_name.replace(" ", "_")
        fname = f"fc_{clean_name}_{largest_n}.png"
        plt.savefig(fname, dpi=100, facecolor="#11111B", bbox_inches="tight")
        plt.close()
        print(f"  Chart saved -> {fname}")

def plot_parameter_sensitivity(results):
    largest_n = max(WORKLOADS)
    subset = [r for r in results if r.workload == largest_n and r.strategy_name.startswith("Formula C")]
    if not subset: return
    
    metrics_map = {
        "Memory Waste": lambda x: x.memory_waste_pct,
        "Total Copied": lambda x: x.total_copied,
        "Throughput": lambda x: x.throughput,
        "Execution Time": lambda x: x.exec_time_ms
    }
    
    pattern_subset = [r for r in subset if r.pattern_name == "Mixed"]
    if not pattern_subset: pattern_subset = subset
        
    def _plot_sensitivity(x_name, x_vals, fixed_wa, fixed_lam, title, fname):
        fig, axes = plt.subplots(4, 1, figsize=(10, 16))
        fig.patch.set_facecolor("#11111B")
        fig.suptitle(title, color="#CDD6F4", fontsize=14, y=0.98)
        
        for ax, (m_name, m_fn) in zip(axes, metrics_map.items()):
            y_vals = []
            for val in x_vals:
                r = None
                if x_name == "Weight A":
                    r = next((x for x in pattern_subset if x.weight_a == val and x.lambda_val == fixed_lam), None)
                elif x_name == "Lambda":
                    r = next((x for x in pattern_subset if x.weight_a == fixed_wa and x.lambda_val == val), None)
                y_vals.append(m_fn(r) if r else 0)
                
            ax.set_facecolor("#1E1E2E")
            ax.set_title(f"{x_name} vs {m_name}", color="#CDD6F4")
            ax.plot(x_vals, y_vals, marker='o', color="#FF6B6B" if "Waste" in m_name else "#4DABF7")
            ax.tick_params(colors="#CDD6F4")
            if "Copied" in m_name:
                ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v>=1e6 else f"{v/1e3:.0f}K"))
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(fname, dpi=100, facecolor="#11111B", bbox_inches="tight")
        plt.close()
        print(f"  Chart saved -> {fname}")

    # Weight A Sensitivity (Fix Lambda=1.0)
    _plot_sensitivity("Weight A", WEIGHT_A_VALUES, 0.5, 1.0, f"Weight A Sensitivity (Mixed) | N={largest_n:,}", f"fc_WeightA_Sensitivity_{largest_n}.png")
    # Lambda Sensitivity (Fix WA=0.5)
    _plot_sensitivity("Lambda", LAMBDA_VALUES, 0.5, 1.0, f"Lambda Sensitivity (Mixed) | N={largest_n:,}", f"fc_Lambda_Sensitivity_{largest_n}.png")

if __name__ == "__main__":
    results = run_all_experiments()
    export_csv(results)
    print_summary_tables(results)
    print("\n  Generating graphs (this will take a moment)...")
    plot_all_comparisons(results)
    print("\n  Generating parameter sensitivity charts...")
    plot_parameter_sensitivity(results)
    print("\nDone.")
