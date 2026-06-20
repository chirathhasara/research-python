# Simulation Results: Formula B Phase 1 (Standard Harmonic Growth)

The simulation evaluates the Phase 1 Baseline for Formula B, which utilizes a harmonic sequence growth strategy driven by the number of resize operations ($k$):

$g(k) = \min(g_{max}, \max(g_{min}, 1 + \frac{c}{k}))$

We parameterized the numerator $c$ to test various levels of initial aggressiveness.

## Key Findings (N = 1,000,000 Insertions)

**1. Copy Costs vs. Resizes**
- **High Resize Counts:** Unlike Formula A, the Harmonic Growth model decays very quickly. This results in an incredibly high number of resizes as the array capacity grows.
- **Massive Copy Overhead:** Due to the frequent resizes, the total elements copied skyrockets. For example, `Formula B (c=1.0)` resulted in **106 resizes and 10,020,732 copies**, whereas `Formula A (a=3.5, b=10)` only required 32 resizes and 3.9M copies.
- Increasing the initial aggressiveness to `c=5.0` lowered the copies to **6,644,767**, but this is still substantially higher than both Formula A and fixed baselines.

**2. Memory Efficiency**
- The major upside of Harmonic Growth is extreme memory efficiency. As the growth factor heavily decays, it hugs the capacity boundary tightly.
- `Formula B (c=1.0)` achieved **0.21% waste**, and `Formula B (c=1.5)` achieved **1.89% waste**.

**3. Comparison with Formula A**
- While Formula B achieves negligible memory waste at large capacities, its toll on performance (element copying) is currently too high. Formula A (`a=3.5, b=10`) provides a vastly superior balance, sacrificing a minor amount of memory (~7.69% waste) to save millions of element copies.

## Conclusion
Formula B Phase 1 demonstrates that pure Harmonic Growth decays too rapidly for standard workloads, causing an unacceptable bottleneck in array resizing (thrashing). To make this formula viable, Phase 2 will need to inject workload-awareness (velocity) into the numerator to significantly flatten the decay curve during sustained insertions.
