# Simulation Results: Formula C (Weighted Capacity-History Hybrid)

Formula C is designed to blend the best characteristics of our two previous models: the capacity-aware stability of Formula A and the burst-responsive history-awareness of Formula B. It does this by combining them with static weights ($w_A$ and $w_B$):

$g(C,k,v) = 1 + w_A \left( \frac{3.0+2.0\ln(1+v)}{\ln(C+5)} \right) + w_B \left( \frac{1}{k} \right)$

We evaluated three static weight configurations:
- **FC (0.8/0.2)**: Capacity-Oriented
- **FC (0.7/0.3)**: Balanced
- **FC (0.6/0.4)**: Burst-Oriented

## Key Findings (N = 1,000,000 Insertions)

**1. Optimization of Accelerating Workloads**
- **Formula A Phase 2:** 30 resizes, 3.36M copies, 6.66% waste.
- **Formula C (0.8/0.2):** **30 resizes, 3.22M copies, 5.05% waste.**
- *Takeaway:* By injecting just 20% of Formula B's harmonic behavior, the capacity-oriented hybrid formula was able to shave off 140,000 element copies while simultaneously reducing memory waste compared to pure Formula A. 

**2. The Spiky Workload Dilemma**
- **Formula B Phase 2:** 17 resizes, 1.20M copies, 5.09% waste.
- **Formula C (0.8/0.2):** 20 resizes, 2.54M copies, 24.82% waste.
- *Takeaway:* The static weights completely compromised Formula B's ability to handle spikes. Because $w_B$ was fixed to a maximum of 0.4 (or 0.2 in the optimal run), the harmonic burst simply wasn't strong enough to absorb the spike, leading to higher copies and significant memory waste. 

## Conclusion
Formula C proved that blending the formulas yields tangible optimizations for smooth, accelerating workloads. However, the static nature of the weights makes it too rigid to handle intense bursts. It acts as a "jack of all trades, master of none."

This perfectly sets the stage for **Formula D (Dynamic Weight Hybrid)**. By using a dynamic weight function $w(v)$ to automatically shift to 100% Formula B during spikes, and 100% Formula A during normal operation, we can achieve the best of both worlds without compromise.
