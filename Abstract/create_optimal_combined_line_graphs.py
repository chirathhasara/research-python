import pandas as pd
import matplotlib.pyplot as plt
import os

# Load dataset
csv_path = r"e:\Research\Coding\python\form_D_hybrid\formula_d_results.csv"
df = pd.read_csv(csv_path)

# Set clean academic matplotlib style
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 1.0

# ------------------------------------------------------------------------------
# 1. Plot 1: Combined Line Graph across Workload Patterns (N=10M)
# ------------------------------------------------------------------------------
df_10m = df[df['Workload'] == 10000000].copy()

patterns = ['Uniform', 'Increasing', 'Decreasing', 'Burst', 'Random', 'Periodic', 'Mixed']

# Key strategies to plot
key_strategies = {
    'Fixed 2.0x': {'color': '#e41a1c', 'marker': 'o', 'linestyle': '-'},
    'Fixed 1.5x': {'color': '#377eb8', 'marker': 's', 'linestyle': '--'},
    'Python List': {'color': '#4daf4a', 'marker': '^', 'linestyle': '-.'},
    'Formula A Phase 2': {'label': 'Logarithmic Variant', 'color': '#984ea3', 'marker': 'D', 'linestyle': ':'},
    'Formula B Phase 2': {'label': 'Harmonic Variant', 'color': '#ff7f00', 'marker': 'v', 'linestyle': '--'},
    'Formula D (optimized)': {'label': 'Proposed GP-Optimized Hybrid', 'color': '#2ca02c', 'marker': 'P', 'linestyle': '-', 'linewidth': 2.5}
}

fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)

for strat_name, style in key_strategies.items():
    label = style.get('label', strat_name)
    color = style['color']
    marker = style['marker']
    linestyle = style['linestyle']
    linewidth = style.get('linewidth', 1.8)
    
    y_vals = []
    for pat in patterns:
        row = df_10m[(df_10m['Pattern'] == pat) & (df_10m['Strategy'] == strat_name)]
        if not row.empty:
            y_vals.append(row['Memory Waste'].values[0])
        else:
            y_vals.append(None)
            
    ax.plot(patterns, y_vals, label=label, color=color, marker=marker, 
            linestyle=linestyle, linewidth=linewidth, markersize=7)

ax.set_title("Memory Waste (%) Comparison across Workload Patterns (N = 10,000,000)", fontsize=13, fontweight='bold', pad=12)
ax.set_xlabel("Workload Pattern", fontsize=11, labelpad=8)
ax.set_ylabel("Memory Waste (%)", fontsize=11, labelpad=8)
ax.grid(True, linestyle='--', alpha=0.5)
ax.set_ylim(-1, 48)
ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#cccccc', fontsize=9.0, loc='upper right', ncol=2)

plt.tight_layout()
output_paths1 = [
    r"e:\Research\Coding\python\Abstract\fd_combined_patterns_line.png",
    r"e:\Research\Coding\python\IEEE\fd_combined_patterns_line.png"
]
for p in output_paths1:
    plt.savefig(p, dpi=300, bbox_inches='tight')
    print(f"Saved: {p}")
plt.close()

# ------------------------------------------------------------------------------
# 2. Plot 2: Combined Line Graph across Workload Sizes (Mixed Workload)
# ------------------------------------------------------------------------------
workloads = [10000, 100000, 1000000, 10000000]
workload_labels = ['10K', '100K', '1M', '10M']

df_mixed = df[df['Pattern'] == 'Mixed'].copy()

fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)

for strat_name, style in key_strategies.items():
    label = style.get('label', strat_name)
    color = style['color']
    marker = style['marker']
    linestyle = style['linestyle']
    linewidth = style.get('linewidth', 1.8)
    
    y_vals = []
    for n in workloads:
        row = df_mixed[(df_mixed['Workload'] == n) & (df_mixed['Strategy'] == strat_name)]
        if not row.empty:
            y_vals.append(row['Memory Waste'].values[0])
        else:
            y_vals.append(None)
            
    ax.plot(workload_labels, y_vals, label=label, color=color, marker=marker, 
            linestyle=linestyle, linewidth=linewidth, markersize=7)

ax.set_title("Memory Waste (%) Scaling across Workload Sizes (Mixed Pattern)", fontsize=13, fontweight='bold', pad=12)
ax.set_xlabel("Workload Size (Elements)", fontsize=11, labelpad=8)
ax.set_ylabel("Memory Waste (%)", fontsize=11, labelpad=8)
ax.grid(True, linestyle='--', alpha=0.5)
ax.set_ylim(-1, 48)
ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#cccccc', fontsize=9.0, loc='upper right', ncol=2)

plt.tight_layout()
output_paths2 = [
    r"e:\Research\Coding\python\Abstract\fd_combined_workload_size_line.png",
    r"e:\Research\Coding\python\IEEE\fd_combined_workload_size_line.png"
]
for p in output_paths2:
    plt.savefig(p, dpi=300, bbox_inches='tight')
    print(f"Saved: {p}")
plt.close()

