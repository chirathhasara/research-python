import os
import math
import csv
import time
import random
from dataclasses import dataclass
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from skopt import gp_minimize
from skopt.space import Real

# =======================================================================
# 1. WORKLOAD GENERATORS
# =======================================================================
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

# =======================================================================
# 2. SIMULATOR
# =======================================================================
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
    objective_score: float = 0.0

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

# =======================================================================
# 3. GROWTH STRATEGIES & BASELINES
# =======================================================================
G_MIN, G_MAX = 1.1, 2.0
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

# =======================================================================
# 4. OPTIMIZATION & EXPERIMENT RUNNER
# =======================================================================
WORKLOADS = [10_000, 100_000, 1_000_000, 10_000_000]

def calculate_j_score(res: SimResult, base_waste: float, base_copy: float, base_time: float) -> float:
    norm_waste = res.memory_waste_pct / max(base_waste, 1.0)
    norm_copy = res.total_copied / max(base_copy, 1.0)
    norm_time = res.exec_time_ms / max(base_time, 1.0)
    
    j = 0.4 * norm_waste + 0.4 * norm_copy + 0.2 * norm_time
    return round(j, 4)

def run_all_experiments():
    results = []
    opt_logs = []
    patterns = {
        "Uniform": generate_uniform_pattern,
        "Increasing": generate_increasing_pattern,
        "Decreasing": generate_decreasing_pattern,
        "Burst": generate_burst_pattern,
        "Random": generate_random_pattern,
        "Periodic": generate_periodic_pattern,
        "Mixed": generate_mixed_pattern
    }
    
    for n in WORKLOADS:
        print("\n" + "="*80)
        print(f"  WORKLOAD: {n:>12,} insertions")
        print("="*80)
        
        for pat_name, pat_fn in patterns.items():
            print(f"\n  --- {pat_name} Workload ---")
            timestamps = pat_fn(n)
            
            sim = DynamicArraySimulatorPhase2()
            res_2x = sim.run(timestamps, fixed_2x_growth)
            res_list = sim.run(timestamps, python_list_growth)
            
            base_waste = max(res_2x.memory_waste_pct, 1.0)
            base_copy = max(res_list.total_copied, 1.0)
            base_time = max(res_list.exec_time_ms, res_2x.exec_time_ms, 1.0)
            
            baselines = [
                ("Fixed 2.0x", fixed_2x_growth),
                ("Fixed 1.5x", fixed_1_5x_growth),
                ("Python List", python_list_growth),
                ("Formula A Phase 1", formula_a_phase1),
                ("Formula A Phase 2", formula_a_phase2),
                ("Formula B Phase 1", make_formula_b_phase1(2.0)),
                ("Formula B Phase 2", make_formula_b_phase2(2.0, 1.0)),
                ("Formula C (best manual configuration)", make_formula_c(0.5, 1.0))
            ]
            
            for strat_name, fn in baselines:
                sim = DynamicArraySimulatorPhase2()
                r = sim.run(timestamps, fn)
                r.strategy_name = strat_name
                r.pattern_name = pat_name
                if strat_name == "Formula C (best manual configuration)":
                    r.weight_a = 0.5
                    r.weight_b = 0.5
                    r.lambda_val = 1.0
                r.objective_score = calculate_j_score(r, base_waste, base_copy, base_time)
                results.append(r)
                
            print("  Optimizing Formula D (35 evaluations)...", end="", flush=True)
            
            opt_history_j = []
            
            def objective(params):
                wa, lam = params
                sim = DynamicArraySimulatorPhase2()
                r = sim.run(timestamps, make_formula_c(wa, lam))
                j = calculate_j_score(r, base_waste, base_copy, base_time)
                opt_history_j.append(j)
                return j
            
            space = [Real(0.0, 1.0, name='weight_a'), Real(0.1, 5.0, name='lambda')]
            
            res_opt = gp_minimize(
                objective, 
                space, 
                n_calls=35, 
                n_initial_points=10, 
                random_state=42
            )
            
            best_wa, best_lam = res_opt.x
            best_j = res_opt.fun
            print(f" done -> Best J: {best_j:.4f} (WA={best_wa:.2f}, Lam={best_lam:.2f})")
            
            sim = DynamicArraySimulatorPhase2()
            r_opt = sim.run(timestamps, make_formula_c(best_wa, best_lam))
            r_opt.strategy_name = "Formula D (optimized)"
            r_opt.pattern_name = pat_name
            r_opt.weight_a = round(best_wa, 4)
            r_opt.weight_b = round(1.0 - best_wa, 4)
            r_opt.lambda_val = round(best_lam, 4)
            r_opt.objective_score = round(best_j, 4)
            results.append(r_opt)
            
            opt_logs.append({
                'workload': n,
                'pattern': pat_name,
                'history': opt_history_j,
                'best_wa': best_wa,
                'best_lam': best_lam,
                'best_j': best_j
            })
            
    return results, opt_logs

def export_data(results, opt_logs):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    csv_path = os.path.join(base_dir, "formula_d_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Pattern", "Workload", "Strategy", "WeightA", "WeightB", "Lambda", 
            "Objective Score", "Memory Waste", "Copy Cost", "Execution Time", 
            "Throughput", "Resize Count", "Peak Memory", "Average Memory", 
            "Memory Footprint", "Peak Waste", "Average Waste", 
            "Average Growth Factor", "Maximum Growth Factor", "Minimum Growth Factor", 
            "Average Velocity", "Maximum Velocity", "Minimum Velocity"
        ])
        for r in results:
            writer.writerow([
                r.pattern_name, r.workload, r.strategy_name, r.weight_a, r.weight_b, r.lambda_val,
                r.objective_score, r.memory_waste_pct, r.total_copied, r.exec_time_ms,
                r.throughput, r.resize_count, r.peak_memory, r.avg_memory, r.memory_footprint,
                r.peak_waste, r.avg_waste, r.avg_growth_factor, r.max_growth_factor, r.min_growth_factor,
                r.avg_velocity, r.max_velocity, r.min_velocity
            ])
            
    opt_path = os.path.join(base_dir, "formula_d_optimization_log.csv")
    with open(opt_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Workload", "Pattern", "Best WeightA", "Best Lambda", "Best Score", "History"])
        for lg in opt_logs:
            writer.writerow([
                lg['workload'], lg['pattern'], round(lg['best_wa'],4), round(lg['best_lam'],4), round(lg['best_j'],4),
                "|".join([f"{v:.4f}" for v in lg['history']])
            ])
            
    rep_path = os.path.join(base_dir, "formula_d_report.txt")
    with open(rep_path, "w", encoding="utf-8") as f:
        f.write("==================================================\n")
        f.write("Formula D Optimization Summary Report\n")
        f.write("==================================================\n\n")
        
        largest_n = max(WORKLOADS)
        f.write(f"Results for N = {largest_n:,}\n\n")
        
        subset = [r for r in results if r.workload == largest_n]
        patterns = list(dict.fromkeys(r.pattern_name for r in subset))
        
        for pat in patterns:
            f.write(f"Pattern: {pat}\n")
            r_c = next((r for r in subset if r.pattern_name == pat and r.strategy_name == "Formula C (best manual configuration)"), None)
            r_d = next((r for r in subset if r.pattern_name == pat and r.strategy_name == "Formula D (optimized)"), None)
            
            f.write(f"  Formula D (Optimized):\n")
            f.write(f"    Best WeightA : {r_d.weight_a:.4f}\n")
            f.write(f"    Best WeightB : {r_d.weight_b:.4f}\n")
            f.write(f"    Best Lambda  : {r_d.lambda_val:.4f}\n")
            f.write(f"    Objective J  : {r_d.objective_score:.4f}\n")
            
            if r_c:
                f.write(f"  Formula C (Manual):\n")
                f.write(f"    Objective J  : {r_c.objective_score:.4f}\n")
                if r_c.objective_score > 0:
                    imp = ((r_c.objective_score - r_d.objective_score) / r_c.objective_score) * 100
                    f.write(f"  -> {imp:.1f}% improvement in combined score\n")
            f.write("-" * 50 + "\n")

def plot_results(results, opt_logs):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    largest_n = max(WORKLOADS)
    subset = [r for r in results if r.workload == largest_n]
    if not subset: return
    
    mixed_log = next((lg for lg in opt_logs if lg['workload'] == largest_n and lg['pattern'] == 'Mixed'), None)
    if mixed_log:
        hist = mixed_log['history']
        best_so_far = np.minimum.accumulate(hist)
        plt.figure(figsize=(8,5), facecolor="#11111B")
        ax = plt.gca()
        ax.set_facecolor("#1E1E2E")
        plt.plot(range(1, len(hist)+1), best_so_far, color="#38D9A9", marker='o', label="Best J Score")
        plt.title(f"Optimization Convergence (Mixed, N={largest_n:,})", color="#CDD6F4")
        plt.xlabel("Iteration", color="#CDD6F4")
        plt.ylabel("Objective Score J", color="#CDD6F4")
        ax.tick_params(colors="#CDD6F4")
        plt.grid(color="#45475A", linestyle="--", alpha=0.5)
        plt.savefig(os.path.join(base_dir, f"fd_Optimization_Convergence_{largest_n}.png"), dpi=100, facecolor="#11111B", bbox_inches="tight")
        plt.close()

    metrics = {
        "Memory Waste": lambda x: x.memory_waste_pct,
        "Copy Cost": lambda x: x.total_copied,
        "Execution Time": lambda x: x.exec_time_ms,
        "Objective Score": lambda x: x.objective_score
    }
    
    pat_res = [r for r in subset if r.pattern_name == "Mixed"]
    
    include = ["Fixed 2.0x", "Fixed 1.5x", "Python List", "Formula C (best manual configuration)", "Formula D (optimized)"]
    display_res = [r for r in pat_res if r.strategy_name in include]
    display_res.sort(key=lambda x: include.index(x.strategy_name))
    names = [r.strategy_name.replace(" (best manual configuration)", "").replace(" (optimized)", "").replace("Fixed", "Fx").replace("Python List", "PyList") for r in display_res]

    for m_name, m_fn in metrics.items():
        fig, ax = plt.subplots(figsize=(8, 5))
        fig.patch.set_facecolor("#11111B")
        ax.set_facecolor("#1E1E2E")
        plt.title(f"{m_name} Comparison (Mixed, N={largest_n:,})", color="#CDD6F4")
        
        vals = [m_fn(r) for r in display_res]
        colors = ["#4DABF7" if "Formula" not in n else ("#FFD43B" if "C" in n else "#38D9A9") for n in names]
        
        ax.bar(names, vals, color=colors)
        ax.tick_params(colors="#CDD6F4")
        if "Copied" in m_name or "Copy Cost" in m_name:
            ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v>=1e6 else f"{v/1e3:.0f}K"))
        
        clean_name = m_name.replace(" ", "_")
        plt.savefig(os.path.join(base_dir, f"fd_{clean_name}_Comparison_{largest_n}.png"), dpi=100, facecolor="#11111B", bbox_inches="tight")
        plt.close()

if __name__ == "__main__":
    results, opt_logs = run_all_experiments()
    export_data(results, opt_logs)
    plot_results(results, opt_logs)
    print("\nFormula D Optimization Completed Successfully.")
