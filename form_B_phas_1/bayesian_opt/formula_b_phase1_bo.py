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
        
        for _ in range(n):
            if self.size == self.capacity:
                k = self.resize_count + 1
                new_cap = growth_fn(self.capacity, k)
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
                last_resize_size = self.size
                
            self.size += 1
            
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
            avg_memory=round(sum_capacity / n if n > 0 else 0.0, 2),
            peak_waste=peak_waste,
            avg_waste=round(sum_waste / n if n > 0 else 0.0, 2)
        )

G_MIN, G_MAX = 1.1, 2.0

def make_formula_b_growth(c: float):
    def growth_fn(capacity: int, k: int) -> int:
        g = 1.0 + c / k
        return int(math.floor(capacity * min(G_MAX, max(G_MIN, g))))
    return growth_fn

def fixed_2x_growth(capacity: int, k: int) -> int: return capacity * 2
def python_list_growth(capacity: int, k: int) -> int:
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
    print(f"Running Baselines for N={n}...")
    
    sim = DynamicArraySimulator()
    res_2x = sim.run(n, fixed_2x_growth)
    
    sim = DynamicArraySimulator()
    res_list = sim.run(n, python_list_growth)
    
    base_waste = max(res_2x.memory_waste_pct, 1.0)
    base_copy = max(res_list.total_copied, 1.0)
    base_time = max(res_list.exec_time_ms, res_2x.exec_time_ms, 1.0)
    
    history_records = []
    opt_history_j = []
    
    def objective(params):
        c_val = params[0]
        sim = DynamicArraySimulator()
        r = sim.run(n, make_formula_b_growth(c_val))
        j = calculate_j_score(r, base_waste, base_copy, base_time)
        opt_history_j.append(j)
        
        history_records.append({
            "Iteration": len(history_records) + 1,
            "C_Val": c_val,
            "Memory_Waste_%": r.memory_waste_pct,
            "Total_Copied": r.total_copied,
            "Exec_Time_ms": r.exec_time_ms,
            "J_Score": j
        })
        return j
        
    space = [Real(0.1, 10.0, name='c_val')]
    
    print("Starting Bayesian Optimization Formula B Phase 1 (35 calls)...")
    res_opt = gp_minimize(
        objective, 
        space, 
        n_calls=35, 
        n_initial_points=10, 
        random_state=42
    )
    
    best_c = res_opt.x[0]
    best_j = res_opt.fun
    print(f"Optimization complete! Best J: {best_j:.4f} (C_Val={best_c:.4f})")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(base_dir, "formula_b_bo_log.csv")
    
    with open(log_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Iteration", "C_Val", "Memory_Waste_%", "Total_Copied", "Exec_Time_ms", "J_Score"])
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
    plt.title("Bayesian Optimization Convergence for Formula B (Phase 1)")
    plt.xlabel("Iteration")
    plt.ylabel("J-Score (Cost)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(base_dir, "bo_convergence.png"), dpi=300)
    plt.close()
    
    # 2. Parameter Scatter Plot (1D mapping)
    cs = [r["C_Val"] for r in history_records]
    js = [r["J_Score"] for r in history_records]
    
    plt.figure(figsize=(10, 6))
    plt.scatter(cs, js, c='blue', s=100, edgecolor='k', alpha=0.7, label='Evaluated C')
    plt.scatter([best_c], [best_j], c='red', marker='*', s=300, edgecolor='k', label='Best Configuration')
    
    plt.title("Explored Parameter Space (C_Val vs J-Score)")
    plt.xlabel("C_Val (c)")
    plt.ylabel("J-Score (lower is better)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(base_dir, "bo_parameter_scatter.png"), dpi=300)
    plt.close()
    print("Figures saved successfully.")

if __name__ == "__main__":
    run_optimization()
