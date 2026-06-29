"""
Generate Workload Pattern Graphs
For Phase 2 Research

Creates:
    workload_patterns_100000.png
    workload_patterns_1000000.png
"""

import numpy as np
import matplotlib.pyplot as plt

# ----------------------------------------------------------
# Configuration
# ----------------------------------------------------------

WORKLOADS = [100_000, 1_000_000]

# velocities
V_LOW = 10
V_HIGH = 1000

np.random.seed(42)

# ----------------------------------------------------------
# Pattern generators
# ----------------------------------------------------------

def uniform(n):
    return np.full(n, V_LOW)

def increasing(n):
    return np.linspace(V_LOW, V_HIGH, n)

def decreasing(n):
    return np.linspace(V_HIGH, V_LOW, n)

def burst(n):

    velocity = np.full(n, V_LOW)

    burst_size = n // 20

    for start in [n//5, n//2, 4*n//5]:
        velocity[start:start+burst_size] = V_HIGH

    return velocity

def random_pattern(n):

    return np.random.uniform(V_LOW, V_HIGH, n)

def periodic(n):

    x = np.linspace(0, 10*np.pi, n)

    return V_LOW + (V_HIGH-V_LOW)/2 * (1 + np.sin(x))

def mixed(n):

    velocity = np.full(n, V_LOW)

    velocity[:n//4] = V_LOW

    velocity[n//4:n//2] = np.linspace(V_LOW, V_HIGH, n//4)

    velocity[n//2:3*n//4] = np.random.uniform(V_LOW, V_HIGH, n//4)

    velocity[3*n//4:] = V_HIGH

    return velocity


patterns = {
    "Uniform": uniform,
    "Increasing": increasing,
    "Decreasing": decreasing,
    "Burst": burst,
    "Random": random_pattern,
    "Periodic": periodic,
    "Mixed": mixed,
}

# ----------------------------------------------------------
# Plot
# ----------------------------------------------------------

for workload in WORKLOADS:

    fig, axes = plt.subplots(
        4,
        2,
        figsize=(14,12)
    )

    fig.suptitle(
        f"Phase 2 Workload Patterns (N = {workload:,})",
        fontsize=18,
        fontweight="bold"
    )

    axes = axes.flatten()

    for i, (name, generator) in enumerate(patterns.items()):

        velocity = generator(workload)

        x = np.linspace(0,100,len(velocity))

        axes[i].plot(
            x,
            velocity,
            linewidth=2
        )

        axes[i].set_title(name)

        axes[i].set_xlabel("Insertion Progress (%)")

        axes[i].set_ylabel("Insertion Velocity (insertions/s)")

        axes[i].grid(True, alpha=0.3)

    axes[-1].axis("off")

    plt.tight_layout()

    plt.savefig(
        f"workload_patterns_{workload}.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

print("Done.")