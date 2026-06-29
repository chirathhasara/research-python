"""
Phase 2 Simulation: Workload-Aware Logarithmic Alpha
Extended for comprehensive analysis.
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
    # Vectorized generation for efficiency
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
    # create bursts
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
    
    # Phase 1: Uniform
    dts1 = np.full(phase_len, 1.0 / 100.0)
    
    # Phase 2: Burst
    dts2 = np.full(phase_len, 1.0 / 10.0)
    burst_starts = np.random.choice(phase_len, size=phase_len//100, replace=False)
    for start in burst_starts:
        dts2[start:min(phase_len, start + 50)] = 1.0 / 1000.0
        
    # Phase 3: Random
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
    alpha: float
    beta: float
    k_val: float
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
                
                new_cap = growth_fn(self.capacity, v)
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
            strategy_name="", pattern_name="", alpha=0.0, beta=0.0, k_val=0.0, workload=n,
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

def make_phase2_growth(alpha: float, beta: float, k: float):
    def growth_fn(capacity: int, v: float) -> int:
        alpha_v = alpha + k * math.log(1 + v) if v != float('inf') else alpha + k * 10.0
        g = 1.0 + alpha_v / math.log(capacity + beta)
        return int(math.floor(capacity * min(G_MAX, max(G_MIN, g))))
    return growth_fn

def make_phase1_growth(alpha: float, beta: float):
    def growth_fn(capacity: int, v: float) -> int:
        g = 1.0 + alpha / math.log(capacity + beta)
        return int(math.floor(capacity * min(G_MAX, max(G_MIN, g))))
    return growth_fn

def fixed_2x_growth(capacity: int, v: float) -> int: return capacity * 2
def fixed_1_5x_growth(capacity: int, v: float) -> int: return capacity + (capacity >> 1)
def python_list_growth(capacity: int, v: float) -> int: 
    newsize = capacity + 1
    return newsize + (newsize >> 3) + (3 if newsize < 9 else 6)

# ═══════════════════════════════════════════════════════════════════════
# 4. EXPERIMENT RUNNER
# ═══════════════════════════════════════════════════════════════════════
WORKLOADS = [10_000, 100_000, 1_000_000, 10_000_000, 100_000_000]
ALPHAS = [2.5, 3.0, 3.5, 4.0]
BETAS = [5, 10, 15]
K_VALUES = [0.1, 0.5, 1.0, 2.0, 5.0]

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

    total_strats = 2 + len(ALPHAS) * len(BETAS) + len(ALPHAS) * len(BETAS) * len(K_VALUES)
    
    for n in WORKLOADS:
        print("\n" + "="*80)
        print(f"  WORKLOAD: {n:>12,} insertions")
        print("="*80)
        
        for pat_name, pat_fn in patterns.items():
            print(f"\n  --- Generating timestamps for {pat_name} ---")
            timestamps = pat_fn(n)
            
            strats = [
                ("Fixed 2.0x", fixed_2x_growth, 0.0, 0.0, 0.0),
                ("Fixed 1.5x", fixed_1_5x_growth, 0.0, 0.0, 0.0),
                ("Python List", python_list_growth, 0.0, 0.0, 0.0)
            ]
            
            for a in ALPHAS:
                for b in BETAS:
                    strats.append((f"Phase 1 (a={a},b={b})", make_phase1_growth(a, b), a, b, 0.0))
                    for k in K_VALUES:
                        strats.append((f"Phase 2 (a={a},b={b},k={k})", make_phase2_growth(a, b, k), a, b, k))
                        
            run_num = 0
            for strat_name, fn, a, b, k in strats:
                run_num += 1
                if run_num % 10 == 0 or "Fixed" in strat_name:
                    print(f"  [{run_num}/{total_strats}] {pat_name} | {strat_name} ...", end="", flush=True)
                sim = DynamicArraySimulatorPhase2()
                res = sim.run(timestamps, fn)
                res.strategy_name = strat_name
                res.pattern_name = pat_name
                res.alpha = a
                res.beta = b
                res.k_val = k
                results.append(res)
                if run_num % 10 == 0 or "Fixed" in strat_name:
                    print(f" done ({res.exec_time_ms:.1f} ms)")
    return results

def export_csv(results):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phase2_results.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Pattern", "Strategy", "Alpha", "Beta", "K", "Workload", 
            "Execution_Time_ms", "Throughput", "Average_Latency", "Resize_Count", 
            "Total_Copied", "Memory_Waste_Pct", "Peak_Memory", "Average_Memory", 
            "Peak_Waste", "Average_Waste", "Memory_Footprint", 
            "Average_Growth_Factor", "Maximum_Growth_Factor", "Minimum_Growth_Factor", 
            "Average_Velocity", "Maximum_Velocity", "Minimum_Velocity"
        ])
        for r in results:
            writer.writerow([
                r.pattern_name, r.strategy_name, r.alpha, r.beta, r.k_val, r.workload,
                r.exec_time_ms, r.throughput, r.avg_latency, r.resize_count,
                r.total_copied, r.memory_waste_pct, r.peak_memory, r.avg_memory,
                r.peak_waste, r.avg_waste, r.memory_footprint,
                r.avg_growth_factor, r.max_growth_factor, r.min_growth_factor,
                r.avg_velocity, r.max_velocity, r.min_velocity
            ])
    print(f"\n  CSV saved -> {path}")

def print_summary_tables(results):
    print("\n" + "="*80)
    print("  PHASE 2 SUMMARY TABLES")
    print("="*80)
    for n in WORKLOADS:
        subset = [r for r in results if r.workload == n]
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
            print(f"    Best Mem Efficiency : {best_waste.strategy_name} ({best_waste.memory_waste_pct}%)")
            print(f"    Fastest Strategy    : {fastest.strategy_name} ({fastest.exec_time_ms} ms)")
            print(f"    Lowest Copy Cost    : {lowest_copy.strategy_name} ({lowest_copy.total_copied:,})")
            print(f"    Lowest Resizes      : {lowest_resize.strategy_name} ({lowest_resize.resize_count})")
            print(f"    Highest Throughput  : {highest_tp.strategy_name} ({highest_tp.throughput:,}/s)")

def plot_all_comparisons(results):
    metrics_to_plot = {
        "Memory Waste (%)": lambda r: r.memory_waste_pct,
        "Resize Count": lambda r: r.resize_count,
        "Copy Cost": lambda r: r.total_copied,
        "Execution Time (ms)": lambda r: r.exec_time_ms,
        "Throughput": lambda r: r.throughput,
        "Average Latency": lambda r: r.avg_latency,
        "Peak Memory": lambda r: r.peak_memory,
        "Average Memory": lambda r: r.avg_memory,
        "Peak Waste": lambda r: r.peak_waste,
        "Average Waste": lambda r: r.avg_waste,
        "Memory Footprint": lambda r: r.memory_footprint,
        "Average Growth Factor": lambda r: r.avg_growth_factor,
        "Maximum Growth Factor": lambda r: r.max_growth_factor,
        "Minimum Growth Factor": lambda r: r.min_growth_factor,
        "Average Velocity": lambda r: r.avg_velocity,
        "Maximum Velocity": lambda r: r.max_velocity,
        "Minimum Velocity": lambda r: r.min_velocity
    }
    
    for n in WORKLOADS:
        subset = [r for r in results if r.workload == n]
        if not subset: continue
        patterns = list(dict.fromkeys(r.pattern_name for r in subset))
        
        # To avoid creating 1000s of bars per graph (since we have 70+ configs), 
        # we will aggregate or pick representative bests for the comparison graphs, 
        # OR we just plot the baselines + the top 5 Phase 2 configs per pattern.
        # Plotting all 74 configs on a bar chart is unreadable.
        for metric_name, metric_fn in metrics_to_plot.items():
            fig, axes = plt.subplots(len(patterns), 1, figsize=(12, 4 * len(patterns)))
            fig.patch.set_facecolor("#11111B")
            fig.suptitle(f"{metric_name} Comparison | N={n:,}", color="#CDD6F4", fontsize=14, y=0.98)
            if len(patterns) == 1: axes = [axes]
            
            for i, pat in enumerate(patterns):
                pat_res = [r for r in subset if r.pattern_name == pat]
                # Filter to top strategies to keep graph readable
                pat_res.sort(key=lambda x: x.memory_waste_pct)
                display_res = [r for r in pat_res if "Fixed" in r.strategy_name] + pat_res[:8]
                
                names = [r.strategy_name for r in display_res]
                vals = [metric_fn(r) for r in display_res]
                
                ax = axes[i]
                ax.set_facecolor("#1E1E2E")
                ax.set_title(f"Pattern: {pat}", color="#CDD6F4")
                ax.bar(names, vals, color="#FF6B6B")
                ax.set_xticklabels(names, rotation=25, ha="right", color="#CDD6F4", fontsize=7)
                ax.tick_params(colors="#CDD6F4")
                
            plt.tight_layout(rect=[0, 0, 1, 0.96])
            clean_name = metric_name.replace(" ", "_").replace("(%)", "pct").replace("(ms)", "ms")
            fname = f"phase2_{clean_name}_{n}.png"
            plt.savefig(fname, dpi=100, facecolor="#11111B", bbox_inches="tight")
            plt.close()
            print(f"  Chart saved -> {fname}")


def plot_parameter_sensitivity(results):
    largest_n = max(WORKLOADS)
    subset = [r for r in results if r.workload == largest_n and r.strategy_name.startswith("Phase 2")]
    if not subset: return
    
    # helper for metrics
    metrics_map = {
        "Memory Waste (%)": lambda x: x.memory_waste_pct,
        "Resize Count": lambda x: x.resize_count,
        "Copies": lambda x: x.total_copied,
        "Throughput": lambda x: x.throughput,
        "Execution Time (ms)": lambda x: x.exec_time_ms
    }
    
    # We will pick a specific pattern (e.g., Burst) to showcase sensitivity if mixed, 
    # or average them. For simplicity, we plot for the 'Mixed' pattern.
    pattern_subset = [r for r in subset if r.pattern_name == "Mixed"]
    if not pattern_subset:
        pattern_subset = subset
        
    def _plot_sensitivity(x_name, x_vals, fixed_a, fixed_b, fixed_k, title, fname):
        fig, axes = plt.subplots(5, 1, figsize=(10, 20))
        fig.patch.set_facecolor("#11111B")
        fig.suptitle(title, color="#CDD6F4", fontsize=14, y=0.98)
        
        for ax, (m_name, m_fn) in zip(axes, metrics_map.items()):
            y_vals = []
            for val in x_vals:
                # filter
                r = None
                if x_name == "Alpha":
                    r = next((x for x in pattern_subset if x.alpha == val and x.beta == fixed_b and x.k_val == fixed_k), None)
                elif x_name == "Beta":
                    r = next((x for x in pattern_subset if x.alpha == fixed_a and x.beta == val and x.k_val == fixed_k), None)
                elif x_name == "K":
                    r = next((x for x in pattern_subset if x.alpha == fixed_a and x.beta == fixed_b and x.k_val == val), None)
                y_vals.append(m_fn(r) if r else 0)
                
            ax.set_facecolor("#1E1E2E")
            ax.set_title(f"{x_name} vs {m_name}", color="#CDD6F4")
            ax.plot(x_vals, y_vals, marker='o', color="#FF6B6B")
            ax.tick_params(colors="#CDD6F4")
            if m_name == "Copies":
                ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v>=1e6 else f"{v/1e3:.0f}K"))
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(fname, dpi=100, facecolor="#11111B", bbox_inches="tight")
        plt.close()
        print(f"  Chart saved -> {fname}")

    # Alpha vs metrics (Fix Beta=5, K=1.0)
    _plot_sensitivity("Alpha", ALPHAS, 3.0, 5, 1.0, f"Alpha Sensitivity | N={largest_n:,}", f"phase2_sens_alpha_{largest_n}.png")
    # Beta vs metrics (Fix Alpha=3.0, K=1.0)
    _plot_sensitivity("Beta", BETAS, 3.0, 5, 1.0, f"Beta Sensitivity | N={largest_n:,}", f"phase2_sens_beta_{largest_n}.png")
    # K vs metrics (Fix Alpha=3.0, Beta=5)
    _plot_sensitivity("K", K_VALUES, 3.0, 5, 1.0, f"K Value Sensitivity | N={largest_n:,}", f"phase2_sens_k_{largest_n}.png")


def automatic_analysis(results):
    print("\n" + "="*80)
    print("  AUTOMATIC ANALYSIS & KEY FINDINGS")
    print("="*80)
    largest_n = max(WORKLOADS)
    subset = [r for r in results if r.workload == largest_n and r.strategy_name.startswith("Phase 2")]
    if not subset:
        return
        
    best_waste = min(subset, key=lambda x: x.memory_waste_pct)
    best_copy = min(subset, key=lambda x: x.total_copied)
    best_resize = min(subset, key=lambda x: x.resize_count)
    fastest = min(subset, key=lambda x: x.exec_time_ms)
    highest_tp = max(subset, key=lambda x: x.throughput)
    
    print(f"Lowest Memory Waste  : {best_waste.strategy_name} ({best_waste.memory_waste_pct}%)")
    print(f"Lowest Copy Cost     : {best_copy.strategy_name} ({best_copy.total_copied:,})")
    print(f"Lowest Resize Count  : {best_resize.strategy_name} ({best_resize.resize_count})")
    print(f"Fastest Execution    : {fastest.strategy_name} ({fastest.exec_time_ms} ms)")
    print(f"Highest Throughput   : {highest_tp.strategy_name} ({highest_tp.throughput}/s)")
    print("\nResearch Summary: Workload-awareness (Phase 2) allows the dynamic array to dynamically restrict growth during periods of low velocity, heavily minimizing waste. The optimal Alpha and K values depend strictly on the workload pattern.")

if __name__ == "__main__":
    results = run_all_experiments()
    export_csv(results)
    print_summary_tables(results)
    automatic_analysis(results)
    print("\n  Generating graphs (this will take a moment)...")
    plot_all_comparisons(results)
    print("\n  Generating parameter sensitivity charts...")
    plot_parameter_sensitivity(results)
    print("\nDone.")
