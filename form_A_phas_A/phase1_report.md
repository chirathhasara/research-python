# Simulation Results: Formula A Phase 1

The simulation evaluates the Phase 1 Baseline for adaptive array scaling. The formula relies on constant Alpha and Beta parameters without workload-awareness:

`g(C) = min(g_max, max(g_min, 1 + alpha / ln(C + beta)))`

## Key Findings (N = 1,000,000 Insertions)

**1. Memory Efficiency**
- **Best Formula A configuration:** `FormulaA(a=1.5, b=2)` with **0.04% waste**.
- **Fixed 2.0x waste:** 23.71%
- **Fixed 1.5x waste:** 17.73%

**2. Copy Cost (The impact of `alpha=3.5` and `beta=10`)**
- The new configuration **`FormulaA(a=3.5, b=10)` emerged as the lowest-copy configuration** among all Formula A combinations, with **3,951,990 copies**.
- This is significantly lower than other Formula A combos but higher than Fixed 2.0x (`1,310,710` copies) and Fixed 1.5x (`2,430,972` copies).
- It achieved this by maintaining a higher initial growth factor, avoiding frequent early-stage resizing while still tapering off to reduce long-term memory waste (Memory waste: 7.69%).

**3. Execution Performance**
- All `FormulaA` variations performed very fast, clocking in ~400-600ms, which remains highly competitive with fixed growth strategies.

**4. Overall Ranking**
- The new `FormulaA(a=3.5, b=10)` strikes a balanced trade-off between copy cost and memory waste compared to extreme low-alpha variants, acting as a great bridge before moving into Phase 2.
