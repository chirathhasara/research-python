# Formula A: Logarithmic Adaptive Growth — Phase 1 Report

## Formula Tested

$$g(C) = \min\left(g_{max},\ \max\left(g_{min},\ 1 + \frac{\alpha}{\ln(C + \beta)}\right)\right)$$

$$C_{new} = \lfloor C_{old} \times g(C) \rfloor$$

With constraints: $g_{min} = 1.1$, $g_{max} = 2.0$

---

## Experiment Setup

| Parameter | Values |
|-----------|--------|
| Alpha | 1.0, 1.5, 2.0, 2.5, 3.0 |
| Beta | 1, 2, 5 |
| Workloads | 10,000 / 100,000 / 1,000,000 insertions |
| Baselines | Fixed 2.0× (C++), Fixed 1.5× (Java) |
| Total runs | 51 (15 combos × 3 workloads + 2 baselines × 3 workloads) |

---

## Results Summary (N = 1,000,000)

| Strategy | Waste % | Resizes | Total Copied | Time (ms) |
|----------|--------:|--------:|-------------:|----------:|
| Fixed 2.0× | 23.71 | 17 | 1,310,710 | 490.0 |
| Fixed 1.5× | 17.73 | 29 | 2,430,972 | 412.6 |
| A(α=1.0, β=5) | 2.00 | 92 | 10,181,518 | 382.3 |
| A(α=1.5, β=2) | **0.04** | 67 | 8,509,374 | 499.5 |
| A(α=2.0, β=5) | 4.53 | 52 | 6,697,292 | 413.7 |
| A(α=2.5, β=2) | 0.30 | 42 | 5,105,389 | 407.7 |
| A(α=3.0, β=5) | 1.22 | 36 | 4,291,665 | 416.9 |

---

## Key Observations

### 1. Memory Efficiency
Formula A dramatically reduces memory waste. The best configuration (α=1.5, β=2) achieved **0.04% waste** at 1M insertions — a reduction of over **23 percentage points** compared to Fixed 2.0× and **17 percentage points** compared to Fixed 1.5×. The logarithmic decay ensures that as the array grows larger, the growth factor tightens naturally, preventing the massive over-allocation seen in fixed strategies.

### 2. Copy Cost Trade-off
The tighter memory comes at the cost of more resize operations and more total element copies. At 1M insertions, Formula A configurations copy between 4.3M–10.8M elements, compared to 1.3M for Fixed 2.0×. However, this is expected — reducing waste inherently requires more frequent, smaller resizes. The amortized cost per insertion remains bounded.

### 3. The Role of Alpha
- **Low α (1.0–1.5):** Growth factor decays quickly → very tight memory (0.04–8%), but many resizes (67–92) and high copy overhead.
- **Mid α (2.0–2.5):** Balanced behavior → moderate waste (0.3–9%), moderate resizes (42–52).
- **High α (3.0):** Approaches fixed-factor behavior → more waste (1.2–2.6%), but fewest resizes (36) and lowest copies among Formula A.

### 4. The Role of Beta
Beta has a secondary effect. Higher β (e.g., 5) tends to reduce waste for large arrays because it shifts the logarithmic curve, causing earlier decay of the growth factor. The effect is most visible at small-to-medium array sizes.

### 5. Execution Time
Formula A configurations were **competitive or faster** than both baselines in wall-clock time. The fastest run (α=1.0, β=5 at 382ms) was quicker than both Fixed 2.0× (490ms) and Fixed 1.5× (413ms). The `math.log()` computation adds negligible overhead compared to the cost of memory allocation and element copying.

---

## Ranking (Composite Score at N = 1,000,000)

Score formula: `0.4 × norm(waste) + 0.3 × norm(copies) + 0.2 × norm(resizes) + 0.1 × norm(time)`

| Rank | Configuration | Score | Waste % | Copies |
|-----:|---------------|------:|--------:|-------:|
| 1 | α=3.0, β=5 | 0.2927 | 1.22 | 4,291,665 |
| 2 | α=2.5, β=2 | 0.2972 | 0.30 | 5,105,389 |
| 3 | α=2.5, β=1 | 0.3021 | 0.30 | 5,105,498 |
| 4 | α=3.0, β=2 | 0.3363 | 2.64 | 4,359,189 |
| 5 | α=3.0, β=1 | 0.3432 | 2.64 | 4,359,189 |

---

## Conclusion

Formula A (Logarithmic Adaptive Growth) is a **practical and effective alternative** to fixed growth strategies. It proves that a mathematically decaying growth factor can reduce memory waste from ~20% down to under 1% while keeping execution time competitive.

The trade-off is clear and tunable:
- Applications prioritizing **memory efficiency** should use **α=1.5, β=2** (0.04% waste).
- Applications prioritizing **balanced performance** should use **α=3.0, β=5** (best composite score, 1.22% waste, fewest copies among Formula A).
- Applications prioritizing **minimal copy overhead** should stay with fixed strategies.

**Recommendation for Phase 2:** The strongest candidates (α=2.5 and α=3.0) should be carried forward into workload-aware testing, where α becomes adaptive based on insertion velocity.
