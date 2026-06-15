# Formula B: Harmonic Growth — Phase 1 Report

## Formula Tested

Formula B uses the array's **resize history** (the number of resize operations, $k$) to determine the growth factor.

$$g(k) = \min\left(g_{max},\ \max\left(g_{min},\ 1 + \frac{c}{k}\right)\right)$$

$$C_{new} = \lfloor C_{old} \times g(k) \rfloor$$

With constraints: 
- $g_{min} = 1.1$ or $1.2$
- $g_{max} = 2.0$

*(Note: The research document defines the strict harmonic formula as $c = 1.0$. We extended testing to $c=1.5$ and $c=2.0$ to explore tuning capabilities.)*

---

## Experiment Setup

| Parameter | Values |
|-----------|--------|
| $c$ (Numerator) | 1.0, 1.5, 2.0 |
| $g_{min}$ | 1.1, 1.2 |
| Workloads | 10,000 / 100,000 / 1,000,000 insertions |
| Baselines | Fixed 2.0×, Fixed 1.5×, Formula A ($\alpha=1.5, \beta=2$) |
| Total runs | 27 (6 combos × 3 workloads + 3 baselines × 3 workloads) |

---

## Results Summary (N = 1,000,000)

| Strategy | Waste % | Resizes | Total Copied | Time (ms) |
|----------|--------:|--------:|-------------:|----------:|
| Fixed 2.0× | 23.71 | 17 | 1,310,710 | 910.0 |
| Fixed 1.5× | 17.73 | 29 | 2,430,972 | 909.6 |
| **Formula A (α=1.5, β=2)** | **0.04** | **67** | **8,509,374** | 649.1 |
| B ($c=1.0, g_{min}=1.1$) | 0.21 | 106 | 10,020,732 | 662.8 |
| B ($c=1.0, g_{min}=1.2$) | 9.24 | 59 | 5,509,160 | 662.0 |
| B ($c=1.5, g_{min}=1.1$) | 1.89 | 98 | 10,191,391 | 700.3 |
| B ($c=1.5, g_{min}=1.2$) | 3.58 | 56 | 5,185,272 | 659.0 |
| B ($c=2.0, g_{min}=1.1$) | 7.32 | 89 | 10,784,771 | 673.9 |
| B ($c=2.0, g_{min}=1.2$) | 8.44 | 53 | 5,460,447 | 664.9 |

---

## Key Observations

### 1. High Memory Efficiency
Just like Formula A, the Harmonic Growth formula successfully collapses memory waste. The strict mathematical definition ($c=1.0, g_{min}=1.1$) brings waste down to **0.21%** compared to the ~24% waste of a Fixed 2.0× strategy.

### 2. Harmonic vs. Logarithmic Decay
While both formulas achieve near-zero waste, they take different paths:
- **Formula A** (Logarithmic) relies on the *current capacity*. It yielded 0.04% waste with 67 resizes.
- **Formula B** (Harmonic) relies on the *resize count*. It yielded 0.21% waste but required **106 resizes**, resulting in more copying overhead (10 million vs 8.5 million elements). Harmonic decay drops off very aggressively early on, forcing the array to hit the $g_{min}$ floor sooner and causing many small, frequent resizes at the tail end.

### 3. The Critical Role of $g_{min}$
Because Formula B decays so fast (e.g., $1 + 1/4 = 1.25$ by just the 4th resize), the minimum growth constraint ($g_{min}$) heavily dictates the late-stage performance. 
Raising $g_{min}$ from 1.1 to 1.2 effectively halved the number of resizes (from 106 down to 59 for $c=1.0$), drastically reducing copy costs. However, it predictably increased memory waste (from 0.21% up to 9.24%). 

### 4. Tuning with the Numerator ($c$)
Adjusting the numerator $c$ stretches out the harmonic curve. $B(c=1.5, g_{min}=1.2)$ proved to be an excellent balanced configuration, achieving a tight **3.58% waste** while keeping resizes (56) and copy operations (5.1M) very manageable.

---

## Conclusion

Phase 1 of Formula B demonstrates that **resize-history-based harmonic growth is a highly effective dynamic sizing strategy**. It inherently bounds memory waste as the array grows. 

However, compared to the capacity-based logarithmic approach of Formula A, standard Harmonic Growth drops off too quickly, leading to a higher frequency of resizes unless the $g_{min}$ floor is raised. 

**Recommendation for Phase 2:**
The strict $c=1.0$ formula relies heavily on the $g_{min}$ floor to prevent excessive thrashing. In Phase 2, injecting insertion velocity into the numerator (making $c$ workload-aware) should directly solve this issue by naturally raising the curve during high-velocity bursts.
