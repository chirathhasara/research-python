import sys
import os
import time
import csv
import math
from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt
from skopt import gp_minimize
from skopt.space import Real

@dataclass
class SimResult:
    strategy_name: str
    alpha: float
    beta: float
    k_val: float
    workload: int
    final_capacity: int
    final_size: int
    resize_count: int
    total_copied: int
    memory_waste_pct: float
    exec_time_ms: float
    throughput: float = 0.0
    avg_latency: float = 0.0
    peak_memory: int = 0
    avg_memory: float = 0.0
    peak_waste: int = 0
    avg_waste: float = 0.0

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
        
        for i, t in enumerate(timestamps):
            if self.size == self.capacity:
                delta_n = self.size - last_resize_size
                delta_t = t - self.last_resize_time
                v = delta_n / delta_t if delta_t > 0 else float('inf')
                if v < 0: v = 0.0
                
                new_cap = growth_fn(self.capacity, v)
                new_cap = max(new_cap, self.capacity + 1)
                
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
            strategy_name="", alpha=0.0, beta=0.0, k_val=0.0, workload=n,
            final_capacity=self.capacity, final_size=self.size,
            resize_count=self.resize_count, total_copied=self.total_copied,
            memory_waste_pct=round(waste_pct, 4),
            exec_time_ms=round(exec_time, 4),
            throughput=round(throughput, 2),
            avg_latency=round(avg_latency, 2),
            peak_memory=self.capacity,
            avg_memory=round(sum_capacity / n if n > 0 else 0, 2),
            peak_waste=peak_waste,
            avg_waste=round(sum_waste / n if n > 0 else 0, 2)
        )

# WORKLOAD GENERATOR
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

G_MIN, G_MAX = 1.1, 2.0

def make_phase2_growth(alpha: float, beta: float, k: float):
    def growth_fn(capacity: int, v: float) -> int:
        alpha_v = alpha + k * math.log(1 + v) if v != float('inf') else alpha + k * 10.0
        g = 1.0 + alpha_v / math.log(capacity + beta)
        return int(math.floor(capacity * min(G_MAX, max(G_MIN, g))))
    return growth_fn

def fixed_2x_growth(capacity: int, v: float) -> int: return capacity * 2
def python_list_growth(capacity: int, v: float) -> int: 
    newsize = capacity + 1
    return newsize + (newsize >> 3) + (3 if newsize < 9 else 6)

def calculate_j_score(res: SimResult, base_waste: float, base_copy: float, base_time: float) -> float:
    norm_waste = res.memory_waste_pct / max(base_waste, 1.0)
    norm_copy = res.total_copied / max(base_copy, 1.0)
    norm_time = res.exec_time_ms / max(base_time, 1.0)
    j = 0.4 * norm_waste + 0.4 * norm_copy + 0.2 * norm_time
    return round(j, 4)

def run_optimization():
    n = 10_000_000
    print(f"Generating Mixed Workload for N={n}...")
    timestamps = generate_mixed_pattern(n)
    
    print("Running Baselines...")
    sim = DynamicArraySimulatorPhase2()
    res_2x = sim.run(timestamps, fixed_2x_growth)
    
    sim = DynamicArraySimulatorPhase2()
    res_list = sim.run(timestamps, python_list_growth)
    
    base_waste = max(res_2x.memory_waste_pct, 1.0)
    base_copy = max(res_list.total_copied, 1.0)
    base_time = max(res_list.exec_time_ms, res_2x.exec_time_ms, 1.0)
    
    history_records = []
    opt_history_j = []
    
    def objective(params):
        alpha, beta, k = params
        sim = DynamicArraySimulatorPhase2()
        r = sim.run(timestamps, make_phase2_growth(alpha, beta, k))
        j = calculate_j_score(r, base_waste, base_copy, base_time)
        opt_history_j.append(j)
        
        history_records.append({
            "Iteration": len(history_records) + 1,
            "Alpha": alpha,
            "Beta": beta,
            "K_Lambda": k,
            "Memory_Waste_%": r.memory_waste_pct,
            "Total_Copied": r.total_copied,
            "Exec_Time_ms": r.exec_time_ms,
            "J_Score": j
        })
        return j
        
    space = [
        Real(0.1, 10.0, name='alpha'), 
        Real(1.0, 100.0, name='beta'),
        Real(0.1, 10.0, name='k')
    ]
    
    print("Starting Bayesian Optimization Phase 2 (35 calls)...")
    res_opt = gp_minimize(
        objective, 
        space, 
        n_calls=35, 
        n_initial_points=10, 
        random_state=42
    )
    
    best_alpha, best_beta, best_k = res_opt.x
    best_j = res_opt.fun
    print(f"Optimization complete! Best J: {best_j:.4f} (Alpha={best_alpha:.4f}, Beta={best_beta:.4f}, K={best_k:.4f})")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(base_dir, "phase2_bo_log.csv")
    
    with open(log_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Iteration", "Alpha", "Beta", "K_Lambda", "Memory_Waste_%", "Total_Copied", "Exec_Time_ms", "J_Score"])
        writer.writeheader()
        for record in history_records:
            writer.writerow(record)
            
    print(f"Detailed log saved to {log_path}")

    # --- PLOTTING ---
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # 1. Convergence Plot
    iters = list(range(1, 36))
    best_j_so_far = np.minimum.accumulate(opt_history_j)
    
    plt.figure(figsize=(10, 6))
    plt.plot(iters, opt_history_j, 'bo-', alpha=0.5, label="J-Score Evaluation")
    plt.plot(iters, best_j_so_far, 'r*-', linewidth=2, markersize=10, label="Minimum J-Score")
    plt.title("Bayesian Optimization Convergence for Formula A (Phase 2)")
    plt.xlabel("Iteration")
    plt.ylabel("J-Score (Cost)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(base_dir, "bo_convergence.png"), dpi=300)
    plt.close()
    
    # 2. Parameter Scatter Plot (3D mapping)
    alphas = [r["Alpha"] for r in history_records]
    betas = [r["Beta"] for r in history_records]
    ks = [r["K_Lambda"] for r in history_records]
    js = [r["J_Score"] for r in history_records]
    
    # Scale dot size by k (minimum size 20, max size 200)
    k_min, k_max = min(ks), max(ks)
    if k_max > k_min:
        sizes = [20 + 180 * ((k - k_min) / (k_max - k_min)) for k in ks]
    else:
        sizes = [100] * len(ks)
    
    plt.figure(figsize=(10, 6))
    sc = plt.scatter(alphas, betas, c=js, cmap='viridis_r', s=sizes, edgecolor='k', alpha=0.8)
    plt.colorbar(sc, label='J-Score (lower is better)')
    
    # Highlight best
    plt.scatter(best_alpha, best_beta, c='red', marker='*', s=300, edgecolor='k', label='Best Configuration')
    
    plt.title("Explored Parameter Space (Size denotes K/Lambda)")
    plt.xlabel("Alpha (α)")
    plt.ylabel("Beta (β)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(base_dir, "bo_parameter_scatter.png"), dpi=300)
    plt.close()
    print("Figures saved successfully.")

if __name__ == "__main__":
    run_optimization()
