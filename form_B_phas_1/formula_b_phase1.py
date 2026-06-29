"""
Formula B: Harmonic Sequence Growth — Phase 1
==================================================================
Extended to track advanced memory and performance metrics.
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
    peak_memory: int = 0
    avg_memory: float = 0.0
    peak_waste: int = 0
    avg_waste: float = 0.0
    memory_footprint: int = 0
    avg_growth_factor: float = 0.0
    max_growth_factor: float = 0.0
    min_growth_factor: float = 0.0

class DynamicArraySimulator:
    def __init__(self, initial_capacity: int = 10):
        self.capacity = initial_capacity
        self.size = 0
        self.resize_count = 0
        self.total_copied = 0

    def run(self, n: int, growth_fn) -> SimResult:
        t0 = time.perf_counter()
        
        current_cap = self.capacity
        last_resize_size = 0
        sum_capacity = 0
        sum_waste = 0
        peak_waste = 0
        
        g_sum = 0.0
        g_max = 0.0
        g_min = float('inf')
        g_count = 0
        
        for _ in range(n):
            if self.size == self.capacity:
                k = self.resize_count + 1
                new_cap = growth_fn(self.capacity, k)
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
                last_resize_size = self.size
                
            self.size += 1
            
        # finalize
        count = self.size - last_resize_size
        if count > 0:
            sum_capacity += count * current_cap
            sum_sizes = (self.size * (self.size + 1) // 2) - (last_resize_size * (last_resize_size + 1) // 2)
            sum_waste += (count * current_cap) - sum_sizes
            waste_after = current_cap - last_resize_size
            if waste_after > peak_waste:
                peak_waste = waste_after

        t1 = time.perf_counter()
        waste_pct = ((self.capacity - self.size) / self.capacity) * 100.0
        
        return SimResult(
            strategy_name="", c_val=0.0, workload=n,
            final_capacity=self.capacity, final_size=self.size,
            resize_count=self.resize_count, total_copied=self.total_copied,
            memory_waste_pct=round(waste_pct, 4), 
            exec_time_ms=round((t1 - t0)*1000, 4),
            peak_memory=self.capacity,
            avg_memory=sum_capacity / n if n > 0 else 0.0,
            peak_waste=peak_waste,
            avg_waste=sum_waste / n if n > 0 else 0.0,
            memory_footprint=self.capacity * 8, # assume 8 bytes per element
            avg_growth_factor=g_sum / g_count if g_count > 0 else 0.0,
            max_growth_factor=g_max if g_count > 0 else 0.0,
            min_growth_factor=g_min if g_count > 0 else 0.0
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
def python_list_growth(capacity: int, k: int) -> int:
    newsize = capacity + 1
    return newsize + (newsize >> 3) + (3 if newsize < 9 else 6)

C_VALUES = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
WORKLOADS = [10_000, 100_000, 1_000_000, 10_000_000]

def run_all_experiments():
    results = []
    total = len(WORKLOADS) * (4 + len(C_VALUES))
    run_num = 0

    for n in WORKLOADS:
        print("\n" + "="*80)
        print(f"  WORKLOAD: {n:>12,} insertions")
        print("="*80)
        
        strats = [
            ("Fixed 2.0x", fixed_2x_growth, 0.0),
            ("Fixed 1.5x", fixed_1_5x_growth, 0.0),
            ("Python List", python_list_growth, 0.0),
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
        writer.writerow([
            "Strategy", "C_Value", "Workload", "Execution_Time_ms", "Final_Capacity", 
            "Final_Size", "Resize_Count", "Total_Copied", "Memory_Waste_Pct", 
            "Peak_Memory", "Average_Memory", "Peak_Waste", "Average_Waste", 
            "Memory_Footprint", "Average_Growth_Factor", "Maximum_Growth_Factor", 
            "Minimum_Growth_Factor"
        ])
        for r in results:
            writer.writerow([
                r.strategy_name, r.c_val, r.workload, r.exec_time_ms, r.final_capacity, 
                r.final_size, r.resize_count, r.total_copied, r.memory_waste_pct, 
                r.peak_memory, round(r.avg_memory, 2), r.peak_waste, round(r.avg_waste, 2), 
                r.memory_footprint, round(r.avg_growth_factor, 4), round(r.max_growth_factor, 4), 
                round(r.min_growth_factor, 4)
            ])
    print(f"\n  CSV saved -> {path}")
    
def generate_report(results):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "summary_report.txt")
    with open(path, "w", encoding="utf-8") as f:
        for n in WORKLOADS:
            subset = [r for r in results if r.workload == n]
            fb = [r for r in subset if r.strategy_name.startswith("Formula B")]
            fa = [r for r in subset if r.strategy_name.startswith("Formula A")]
            
            f.write("\n" + "="*80 + "\n")
            f.write(f"  AUTOMATIC ANALYSIS | Workload = {n:,} insertions\n")
            f.write("="*80 + "\n")
            
            if fb:
                best_waste = min(fb, key=lambda x: x.memory_waste_pct)
                lowest_copy = min(fb, key=lambda x: x.total_copied)
                lowest_resize = min(fb, key=lambda x: x.resize_count)
                fastest = min(fb, key=lambda x: x.exec_time_ms)
                
                f.write(f"  Best Formula B Parameter (c) : c = {best_waste.c_val}\n")
                f.write(f"  Lowest Memory Waste          : {best_waste.strategy_name} ({best_waste.memory_waste_pct}%)\n")
                f.write(f"  Lowest Copy Cost             : {lowest_copy.strategy_name} ({lowest_copy.total_copied:,})\n")
                f.write(f"  Lowest Resize Count          : {lowest_resize.strategy_name} ({lowest_resize.resize_count})\n")
                f.write(f"  Fastest Strategy             : {fastest.strategy_name} ({fastest.exec_time_ms} ms)\n")
                f.write(f"  Best Overall Formula B       : Formula B (c={best_waste.c_val}) [Balances waste well]\n")
                
                if fa:
                    f.write("\n  Comparison against Formula A:\n")
                    f.write(f"    Formula A Waste: {fa[0].memory_waste_pct}% | Copied: {fa[0].total_copied:,}\n")
                    f.write(f"    Formula B Waste: {best_waste.memory_waste_pct}% | Copied: {best_waste.total_copied:,}\n")
            
    print(f"  TXT Report saved -> {path}")

def plot_comparisons(results):
    metrics = {
        "Memory_Waste_Comparison": ("Memory Waste (%)", lambda r: r.memory_waste_pct),
        "Total_Copies_Comparison": ("Total Elements Copied", lambda r: r.total_copied),
        "Resize_Count_Comparison": ("Resize Count", lambda r: r.resize_count),
        "Execution_Time_Comparison": ("Execution Time (ms)", lambda r: r.exec_time_ms),
        "Peak_Memory_Comparison": ("Peak Memory", lambda r: r.peak_memory),
        "Average_Memory_Comparison": ("Average Memory", lambda r: r.avg_memory),
    }

    for n in WORKLOADS:
        subset = [r for r in results if r.workload == n]
        names = [r.strategy_name.replace("Formula B", "FB").replace("Formula A", "FA").replace("Fixed", "F").replace("Python List", "PyList") for r in subset]
        x = np.arange(len(names))
        
        # 1-6 standard comparisons
        for fname_key, (title, fn) in metrics.items():
            vals = [fn(r) for r in subset]
            fig, ax = plt.subplots(figsize=(10, 5))
            fig.patch.set_facecolor("#11111B")
            ax.set_facecolor("#1E1E2E")
            ax.set_title(f"{title} | N = {n:,}", color="#CDD6F4", fontsize=12)
            bars = ax.bar(x, vals, color="#FF6B6B" if "Waste" in title else "#4DABF7")
            ax.set_xticks(x)
            ax.set_xticklabels(names, rotation=45, ha="right", color="#CDD6F4", fontsize=8)
            ax.tick_params(colors="#CDD6F4")
            if "Copies" in title or "Memory" in title and "Waste" not in title:
                ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v>=1e6 else f"{v/1e3:.0f}K" if v>=1e3 else f"{v}"))
            
            plt.tight_layout()
            fname = f"formula_b_{fname_key}_{n}.png"
            plt.savefig(fname, dpi=100, facecolor="#11111B", bbox_inches="tight")
            plt.close()
            print(f"  Chart saved -> {fname}")
            
        # 7. Growth factor comparison
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor("#11111B")
        ax.set_facecolor("#1E1E2E")
        ax.set_title(f"Growth Factor Statistics | N = {n:,}", color="#CDD6F4", fontsize=12)
        
        w = 0.25
        avg_g = [r.avg_growth_factor for r in subset]
        max_g = [r.max_growth_factor for r in subset]
        min_g = [r.min_growth_factor for r in subset]
        
        ax.bar(x - w, min_g, width=w, label="Min GF", color="#38D9A9")
        ax.bar(x, avg_g, width=w, label="Avg GF", color="#FFD43B")
        ax.bar(x + w, max_g, width=w, label="Max GF", color="#FA5252")
        
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=45, ha="right", color="#CDD6F4", fontsize=8)
        ax.tick_params(colors="#CDD6F4")
        ax.legend(facecolor="#1E1E2E", edgecolor="#CDD6F4", labelcolor="#CDD6F4")
        
        plt.tight_layout()
        fname = f"formula_b_Growth_Factor_Comparison_{n}.png"
        plt.savefig(fname, dpi=100, facecolor="#11111B", bbox_inches="tight")
        plt.close()
        print(f"  Chart saved -> {fname}")

    # 8. Parameter Sensitivity (for largest workload)
    largest_n = max(WORKLOADS)
    subset_fb = [r for r in results if r.workload == largest_n and r.strategy_name.startswith("Formula B")]
    if subset_fb:
        fig, ax1 = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor("#11111B")
        ax1.set_facecolor("#1E1E2E")
        ax1.set_title(f"Parameter Sensitivity (c) | N = {largest_n:,}", color="#CDD6F4", fontsize=12)
        
        c_vals = [r.c_val for r in subset_fb]
        wastes = [r.memory_waste_pct for r in subset_fb]
        copies = [r.total_copied for r in subset_fb]
        
        color1 = "#FF6B6B"
        ax1.set_xlabel("Parameter c", color="#CDD6F4")
        ax1.set_ylabel("Memory Waste (%)", color=color1)
        ax1.plot(c_vals, wastes, color=color1, marker='o', linewidth=2)
        ax1.tick_params(axis='y', labelcolor=color1, colors="#CDD6F4")
        ax1.tick_params(axis='x', colors="#CDD6F4")
        
        ax2 = ax1.twinx()
        color2 = "#4DABF7"
        ax2.set_ylabel("Total Elements Copied", color=color2)
        ax2.plot(c_vals, copies, color=color2, marker='s', linewidth=2, linestyle='--')
        ax2.tick_params(axis='y', labelcolor=color2, colors="#CDD6F4")
        ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v>=1e6 else f"{v/1e3:.0f}K"))
        
        fig.tight_layout()
        fname = f"formula_b_Parameter_Sensitivity_{largest_n}.png"
        plt.savefig(fname, dpi=150, facecolor="#11111B", bbox_inches="tight")
        plt.close()
        print(f"  Chart saved -> {fname}")

if __name__ == "__main__":
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    results = run_all_experiments()
    export_csv(results)
    generate_report(results)
    print("\n  Generating graphs...")
    plot_comparisons(results)
    print("\n  Done.")
