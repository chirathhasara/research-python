import sys
import os
import time
import csv
import math
from dataclasses import dataclass, field
import numpy as np
import matplotlib.pyplot as plt
from skopt import gp_minimize
from skopt.space import Real

@dataclass
class SimResult:
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
    peak_memory: int = 0
    avg_memory: float = 0.0
    peak_waste: int = 0
    avg_waste: float = 0.0
    objective_score: float = 0.0

class DynamicArraySimulator:
    def __init__(self, initial_capacity: int = 10):
        self.capacity: int = initial_capacity
        self.size: int = 0
        self.resize_count: int = 0
        self.total_copied: int = 0
        self.sum_capacity: int = 0
        self.sum_waste: int = 0
        self.peak_waste: int = 0

    def run(self, n: int, growth_fn) -> SimResult:
        t0 = time.perf_counter()

        last_resize_size = 0
        current_cap = self.capacity
        
        for _ in range(n):
            if self.size == self.capacity:
                count = self.size - last_resize_size
                self.sum_capacity += count * current_cap
                sum_sizes = (self.size * (self.size + 1) // 2) - (last_resize_size * (last_resize_size + 1) // 2)
                self.sum_waste += (count * current_cap) - sum_sizes
                
                new_cap = growth_fn(self.capacity)
                new_cap = max(new_cap, self.capacity + 1)
                
                waste_after_resize = new_cap - self.size
                if waste_after_resize > self.peak_waste:
                    self.peak_waste = waste_after_resize
                    
                self.total_copied += self.size
                self.capacity = new_cap
                current_cap = new_cap
                last_resize_size = self.size
                self.resize_count += 1
                
            self.size += 1

        count = self.size - last_resize_size
        if count > 0:
            self.sum_capacity += count * current_cap
            sum_sizes = (self.size * (self.size + 1) // 2) - (last_resize_size * (last_resize_size + 1) // 2)
            self.sum_waste += (count * current_cap) - sum_sizes
            waste_after_resize = current_cap - last_resize_size
            if waste_after_resize > self.peak_waste:
                self.peak_waste = waste_after_resize
                
        t1 = time.perf_counter()

        waste_pct = ((self.capacity - self.size) / self.capacity) * 100.0
        avg_memory = self.sum_capacity / n if n > 0 else 0
        avg_waste = self.sum_waste / n if n > 0 else 0

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
            peak_memory=self.capacity,
            avg_memory=round(avg_memory, 4),
            peak_waste=self.peak_waste,
            avg_waste=round(avg_waste, 4),
        )


def fixed_2x_growth(capacity: int) -> int:
    return capacity * 2

def python_list_growth(capacity: int) -> int:
    newsize = capacity + 1
    return newsize + (newsize >> 3) + (3 if newsize < 9 else 6)

G_MIN = 1.1
G_MAX = 2.0

def make_formula_a_growth(alpha: float, beta: float):
    def growth_fn(capacity: int) -> int:
        ln_val = math.log(capacity + beta)
        g = 1.0 + alpha / ln_val
        g = min(G_MAX, max(G_MIN, g))
        return int(math.floor(capacity * g))
    return growth_fn

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
        alpha, beta = params
        sim = DynamicArraySimulator()
        r = sim.run(n, make_formula_a_growth(alpha, beta))
        j = calculate_j_score(r, base_waste, base_copy, base_time)
        opt_history_j.append(j)
        
        history_records.append({
            "Iteration": len(history_records) + 1,
            "Alpha": alpha,
            "Beta": beta,
            "Memory_Waste_%": r.memory_waste_pct,
            "Total_Copied": r.total_copied,
            "Exec_Time_ms": r.exec_time_ms,
            "J_Score": j
        })
        return j
        
    space = [Real(0.1, 10.0, name='alpha'), Real(1.0, 100.0, name='beta')]
    
    print("Starting Bayesian Optimization (35 calls)...")
    res_opt = gp_minimize(
        objective, 
        space, 
        n_calls=35, 
        n_initial_points=10, 
        random_state=42
    )
    
    best_alpha, best_beta = res_opt.x
    best_j = res_opt.fun
    print(f"Optimization complete! Best J: {best_j:.4f} (Alpha={best_alpha:.4f}, Beta={best_beta:.4f})")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(base_dir, "formula_a_bo_log.csv")
    
    # Sort history to find top 5
    sorted_history = sorted(history_records, key=lambda x: x["J_Score"])
    
    with open(log_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Iteration", "Alpha", "Beta", "Memory_Waste_%", "Total_Copied", "Exec_Time_ms", "J_Score"])
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
    plt.title("Bayesian Optimization Convergence for Formula A (Phase 1)")
    plt.xlabel("Iteration")
    plt.ylabel("J-Score (Cost)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(base_dir, "bo_convergence.png"), dpi=300)
    plt.close()
    
    # 2. Parameter Scatter Plot
    alphas = [r["Alpha"] for r in history_records]
    betas = [r["Beta"] for r in history_records]
    js = [r["J_Score"] for r in history_records]
    
    plt.figure(figsize=(10, 6))
    sc = plt.scatter(alphas, betas, c=js, cmap='viridis_r', s=100, edgecolor='k')
    plt.colorbar(sc, label='J-Score (lower is better)')
    plt.scatter(best_alpha, best_beta, c='red', marker='*', s=300, edgecolor='k', label='Best Configuration')
    plt.title("Explored Parameter Space (Alpha vs Beta)")
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
