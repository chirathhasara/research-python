# Phase 2: Workload-Aware Harmonic Growth — Explanation

## 1. Velocity Calculation

Just like in Formula A, insertion velocity ($v$) is calculated at each resize event:
$$v_{current} = \frac{\Delta N}{\Delta t}$$

This is smoothed using an Exponential Moving Average (EMA) to prevent erratic jumps:
$$v_{smooth} = 0.9 \cdot v_{previous} + 0.1 \cdot v_{current}$$

## 2. Workload-Aware Numerator

In Phase 1, Harmonic Growth decayed based strictly on the number of resizes ($k$) using a constant numerator ($1.0$). 
In Phase 2, the numerator adapts based on the logarithmic scale of the smoothed insertion velocity:

$$\text{Numerator}(v) = 1 + \lambda \ln(1 + v_{smooth})$$

Where $\lambda$ (lambda) is the workload sensitivity parameter. 

This numerator replaces the constant $1$ in the harmonic formula:

$$g(k,v) = \min\left(g_{max},\ \max\left(g_{min},\ 1 + \frac{\text{Numerator}(v)}{k}\right)\right)$$

## 3. Expected Behavior vs Observed Behavior

### Standard Harmonic Problem (Phase 1)
Harmonic growth naturally decays very quickly (e.g., $1 + 1/5 = 1.2$ by the 5th resize). For bursty workloads, this forces premature tight allocations, causing frequent resizes and high copy overhead while the system is under heavy load.

### Phase 2 Solution
By scaling the numerator via $\lambda \ln(1+v)$, the harmonic curve gets "lifted" dynamically when insertions happen rapidly. 
- **Fast Workloads**: Velocity is high $\rightarrow$ Numerator is large $\rightarrow$ Growth factor stays elevated longer, resisting the fast $1/k$ decay and preventing thrashing.
- **Slow Workloads**: Velocity is near zero $\rightarrow$ Numerator stays close to $1.0$ $\rightarrow$ Behaves identically to standard Phase 1 conservative growth.
- **Bursty Workloads**: Adapts to the bursts, lifting the curve when under load, and dropping back to the standard curve when idle.

This allows the array to handle massive data ingest without dying from resize-thrashing, while preserving the mathematical guarantee of near-zero memory waste as $k \rightarrow \infty$ during idle periods.
