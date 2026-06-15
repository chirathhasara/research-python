# Phase 2: Workload-Aware Alpha — Explanation

## 1. Velocity Calculation

Insertion velocity measures how fast elements are being added to the array. At each resize event, we compute:

```
v_current = (insertions_since_last_resize) / (time_since_last_resize)
```

This raw velocity is then smoothed using an Exponential Moving Average (EMA):

```
v_smooth = 0.9 * v_previous + 0.1 * v_current
```

The EMA prevents sudden spikes from causing erratic growth decisions. The smoothing factor (0.9) is configurable.

## 2. Adaptive Alpha Calculation

In Phase 1, alpha was a fixed constant. In Phase 2, alpha becomes a function of the smoothed velocity:

```
alpha(v) = alpha_base + k * v_smooth
```

Where:
- `alpha_base` = baseline aggressiveness (e.g., 2.0)
- `k` = velocity sensitivity coefficient (e.g., 0.001)
- `v_smooth` = EMA-smoothed insertion velocity

This alpha is then used in the same logarithmic growth formula:

```
g(C,v) = min(g_max, max(g_min, 1 + alpha(v) / ln(C + beta)))
C_new  = ceil(C_old * g(C,v))
```

## 3. Expected Behavior

| Workload | Velocity | Alpha | Growth Factor | Behavior |
|----------|----------|-------|---------------|----------|
| Fast burst | High | High (alpha_base + k*v) | Larger | Aggressive growth, fewer resizes |
| Slow trickle | Low | ~alpha_base | Smaller | Conservative growth, tight memory |
| Bursty | Alternating | Oscillating | Varying | Adapts to current insertion rate |
| Mixed | Gradual change | Smooth transition | Smooth | Follows workload trend |

## 4. Observed Behavior

The experiments confirm the theoretical predictions:

- **Fast workloads** produce high velocity -> higher alpha -> larger growth factors -> fewer total resizes.
- **Slow workloads** keep velocity near zero -> alpha stays near alpha_base -> growth behaves like Phase 1.
- **Bursty workloads** show oscillating velocity and alpha, with the EMA smoothing preventing whiplash.
- **The velocity-alpha scatter plot** shows a clear positive linear correlation, validating the formula `alpha(v) = alpha_base + k*v`.

Phase 2 demonstrates that workload awareness adds meaningful adaptivity on top of Phase 1's capacity-based decay, particularly for non-uniform insertion patterns.
