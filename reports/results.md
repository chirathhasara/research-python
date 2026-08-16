# Comprehensive Experimental Benchmark Results (10M Insertions)

This document consolidates all empirical evaluation metrics and benchmark findings from the research reports located in `e:\Research\Coding\python\Formula results` (`formula_a.pdf`, `formula_a_2.pdf`, `formula_b.pdf`, `formula_b_2.pdf`, `formula_c.pdf`, `formula_d.pdf`) alongside the subsequent Bayesian Optimization hyperparameter tuning results—standardized specifically to **10,000,000 (10M) insertions** for clean cross-formula comparison.

---

## 1. Experimental Methodology Overview

The dynamic array resizing algorithms were evaluated across four primary formula strategies:
* **Formula A (Logarithmic Family):** Capacity-based logarithmic scaling (Phase 1: static, Phase 2: velocity-aware).
* **Formula B (Harmonic Family):** Resize-history harmonic scaling (Phase 1: static, Phase 2: velocity-aware).
* **Formula C (Hybrid Model):** Weighted interpolation blending Formula A logarithmic bounds and Formula B harmonic bounds ($g = 1 + w_A g_A + w_B g_B$, $w_B = 1 - w_A$).
* **Formula D (Optimized Hybrid Framework):** Automated Gaussian Process Bayesian Optimization framework tuning weight distribution ($w_A$) and velocity weight ($\lambda$).

### Formula Definitions:
1. **Formula A (Phase 1):** $g(C) = \min\left(2.0, \max\left(1.1, 1 + \frac{\alpha}{\ln(C + \beta)}\right)\right)$
2. **Formula A (Phase 2):** $g(C, v) = \min\left(2.0, \max\left(1.1, 1 + \frac{\alpha + \lambda \ln(1+v)}{\ln(C + \beta)}\right)\right)$
3. **Formula B (Phase 1):** $g(k) = \min\left(2.0, \max\left(1.1, 1 + \frac{c_0}{k}\right)\right)$
4. **Formula B (Phase 2):** $g(k, v) = \min\left(2.0, \max\left(1.1, 1 + \frac{c_0 + \lambda \ln(1+v)}{k}\right)\right)$
5. **Formula C (Hybrid):** $g(C, k, v) = 1 + w_A \left(\frac{\alpha_0 + \lambda \ln(1+v)}{\ln(C+\beta)}\right) + w_B \left(\frac{c_0 + \lambda \ln(1+v)}{k}\right)$
6. **Formula D (Opt Framework):** Automated GP optimization of Formula C space minimizing $J = 0.4 \cdot \text{Waste} + 0.4 \cdot \text{Copies} + 0.2 \cdot \text{Time}$.

---

## 2. Grid Search Benchmark Results (Pre-Bayesian Optimization @ 10M Insertions)

These results represent the initial empirical evaluation across discrete grid parameters at **10M insertions**:

### A. Formula A - Phase 1 ($N = 10\text{M}$ Sequential Insertions)
*Source: `formula_a.pdf` (Figure 8 & Section 4.5)*

| Strategy | Memory Waste (%) | Resize Count | Total Elements Copied | Execution Time (ms) |
| :--- | :---: | :---: | :---: | :---: |
| Fixed 2.0x (C++ `std::vector`) | 4.63% | 20 | 10,485,750 | 4377.1 ms |
| Fixed 1.5x (Java `ArrayList`) | 27.80% | 35 | 27,690,301 | 4720.6 ms |
| Python List ($1.125\times$) | 4.60% | 102 | 83,842,078 | 4500.1 ms |
| **Absolute Best Waste ($\alpha=1.0, \beta=10$)** | **0.50%** ⭐ | **116** | **104,188,382** | **4278.9 ms** |
| Formula A ($\alpha=1.5, \beta=10$) | 1.00% | 91 | 88,142,398 | 4203.8 ms |
| Formula A ($\alpha=2.0, \beta=10$) | 0.70% | 70 | 65,248,390 | 4331.9 ms |
| Reference Config ($\alpha=3.5, \beta=10$) | 8.80% | 43 | 47,288,928 | 4420.5 ms |

---

### B. Formula A - Phase 2 Workload-Aware ($N = 10\text{M}$ Mixed Workload)
*Source: `formula_a_2.pdf`*

| Strategy | Memory Waste (%) | Resize Count | Total Elements Copied | Throughput (ops/sec) |
| :--- | :---: | :---: | :---: | :---: |
| Fixed 2.0x | 4.63% | 20 | 10,485,750 | 7,277,700 |
| Fixed 1.5x | 27.77% | 35 | 27,690,301 | 7,134,555 |
| Python List | 4.59% | 102 | 83,842,078 | 7,050,870 |
| Absolute Best FA Phase 1 ($\alpha=1.0, \beta=10$) | 0.50% | 116 | 104,188,382 | 6,120,000 |
| FA Phase 1 Reference Config ($\alpha=3.5, \beta=10$) | 8.76% | 43 | 47,288,928 | 5,923,172 |
| **Best Formula A Phase 2 ($\alpha=2.5, \beta=15, \lambda=0.5$)** | **1.89%** ⭐ | **31** | **30,381,476** ⭐ | **6,080,745** ⭐ |

---

### C. Formula B - Phase 1 Harmonic ($N = 10\text{M}$ Sequential Insertions)
*Source: `formula_b.pdf`*

| Strategy | Memory Waste (%) | Resize Count | Total Elements Copied | Execution Time (ms) |
| :--- | :---: | :---: | :---: | :---: |
| Fixed 2.0x | 4.63% | 20 | 10,485,750 | 1807.9 ms |
| Fixed 1.5x | 27.77% | 35 | 27,690,301 | 1351.6 ms |
| Python List | 4.59% | 102 | 83,842,078 | 1383.2 ms |
| Absolute Best FA Phase 1 ($\alpha=1.0, \beta=10$) | 0.50% | 116 | 104,188,382 | 4278.9 ms |
| FA Phase 1 Reference Config ($\alpha=3.5, \beta=10$) | 8.76% | 43 | 47,288,928 | 1433.9 ms |
| **Absolute Best FB Phase 1 ($c=1.5$)** | **0.39%** ⭐ | **122** | **100,391,706** | **1303.4 ms** ⭐ |
| FB Phase 1 Reference Config ($c=1.0$) | 5.90% | 113 | 106,268,359 | 1320.0 ms |
| FB Phase 1 ($c=5.0$) | 3.80% | 59 | 96,557,401 | 1230.1 ms |

---

### D. Formula B - Phase 2 Workload-Aware ($N = 10\text{M}$ Mixed Workload)
*Source: `formula_b_2.pdf`*

| Strategy | Memory Waste (%) | Resize Count | Total Elements Copied | Throughput (ops/sec) |
| :--- | :---: | :---: | :---: | :---: |
| Fixed 2.0x | 4.63% | 20 | 10,485,750 | 5,984,961 |
| Fixed 1.5x | 27.77% | 35 | 27,690,301 | 6,245,380 |
| Python List | 4.59% | 102 | 83,842,078 | 6,339,194 |
| Absolute Best FA Phase 1 ($\alpha=1.0, \beta=10$) | 0.50% | 116 | 104,188,382 | 6,120,000 |
| Best FA Phase 2 ($\alpha=2.5, \beta=15, \lambda=0.5$) | 1.89% | 31 | 30,381,476 | 6,080,745 |
| Absolute Best FB Phase 1 ($c=1.5$) | 0.39% | 122 | 100,391,706 | 6,315,600 |
| FB Phase 1 Reference Config ($c=1.0$) | 7.90% | 131 | 108,572,640 | 6,315,600 |
| **Best Formula B Phase 2 ($c_0=2.0, \lambda=1.0$)** | **1.28%** ⭐ | **32** | **38,761,118** ⭐ | **6,396,909** ⭐ |

---

### E. Formula C - Hybrid Workload-Aware Strategy ($N = 10\text{M}$ Mixed Workload)
*Source: `formula_c.pdf` (Table 2)*

| Strategy | Memory Waste (%) | Resize Count | Total Elements Copied | Throughput (ops/sec) |
| :--- | :---: | :---: | :---: | :---: |
| Fixed 2.0x | 4.63% | 20 | 10,485,750 | 4,208,384 |
| Fixed 1.5x | 27.77% | 35 | 27,690,301 | 4,438,894 |
| Python List | 4.59% | 102 | 83,842,078 | 3,818,086 |
| FA Phase 1 Reference Config ($\alpha=3.5, \beta=10$) | 8.76% | 43 | 47,288,928 | 4,358,483 |
| FA Phase 2 Reference Config ($\alpha=3.5, \beta=10, \lambda=1.0$) | 1.87% | 31 | 30,377,760 | 4,275,988 |
| FB Phase 1 Reference Config ($c=1.0$) | 5.90% | 113 | 106,268,359 | 4,288,219 |
| FB Phase 2 Reference Config ($c_0=2.0, \lambda=1.0$) | 1.28% | 32 | 38,761,723 | 4,437,300 |
| **Best Formula C ($w_A=0.0, w_B=1.0, \lambda=1.0$)** | **1.28%** ⭐ | **32** | **38,761,723** ⭐ | **2,833,562** |
| *Absolute Best FA Phase 1 ($\alpha=1.0, \beta=10$)* | *0.50%* | *116* | *104,188,382* | *6,120,000* |
| *Absolute Best FB Phase 1 ($c=1.5$)* | *0.39%* | *122* | *100,391,706* | *6,315,600* |

---

### F. Formula D - Optimized Hybrid Framework ($N = 10\text{M}$ Mixed Workload)
*Source: `formula_d.pdf` (Table 1 & Table 2)*

| Strategy | Memory Waste (%) | Resize Count | Total Elements Copied | Throughput (ops/sec) | Unified J-Score |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Fixed 2.0x | 4.63% | 20 | 10,485,750 | 5,870,321 | 0.6400 |
| Fixed 1.5x | 27.77% | 35 | 27,690,301 | 6,132,004 | 2.7500 |
| Python List | 4.59% | 102 | 83,842,078 | 6,230,581 | 0.9500 |
| FA Phase 1 Reference Config ($\alpha=3.5, \beta=10$) | 8.76% | 43 | 47,288,928 | 6,432,519 | — |
| FA Phase 2 Reference Config ($\alpha=3.5, \beta=10, \lambda=1.0$) | 1.88% | 31 | 30,380,203 | 5,851,246 | 0.6200 |
| FB Phase 1 Reference Config ($c=1.0$) | 5.90% | 113 | 106,268,359 | 6,108,619 | — |
| FB Phase 2 Reference Config ($c_0=2.0, \lambda=1.0$) | 1.35% | 32 | 38,770,015 | 6,258,235 | 0.5800 |
| Formula C (Manual $w_A=0.5, \lambda=0.5$) | 13.04% | 27 | 29,219,252 | 6,078,739 | 1.4415 |
| **Formula D (GP-Optimized $w_A=0.9955, \lambda=3.0944$)** | **0.42%** ⭐ | **20** ⭐ | **10,485,750** ⭐ | **5,940,151** | **0.2589** ⭐ |
| *Absolute Best FA Phase 1 ($\alpha=1.0, \beta=10$)* | *0.50%* | *116* | *104,188,382* | *6,120,000* | *0.6700* |
| *Absolute Best FB Phase 1 ($c=1.5$)* | *0.39%* | *122* | *100,391,706* | *6,315,600* | *0.6800* |

*Note: Formula D achieved an **82.04% reduction in J-Score cost** compared to manual Formula C ($J=0.2589$ vs $J=1.4415$).*

---

## 3. Bayesian Optimization Fine-Tuning Results (Post-GP Tuning @ 10M Insertions)

To continuously search the multi-dimensional parameter space across all formulas, Gaussian Process Bayesian Optimization (`skopt.gp_minimize`, 35 iterations, 10M insertions) was executed with a composite objective function ($J = 0.4 \cdot \text{Waste} + 0.4 \cdot \text{Copies} + 0.2 \cdot \text{Time}$):

### Master Bayesian Optimization Comparison Table ($N = 10\text{M}$)

| Algorithm / Strategy | Model Variant | Optimal Parameters | Memory Waste (%) | Copied Elements | Resizes ($k$) | Exec Time | Best $J$-Score |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Formula A** | **Phase 1 (Logarithmic)** | $\alpha=4.6381, \beta=34.0696$ | **0.05%** ⭐ | **32.31M** | 25 | ~1871 ms | **0.3470** |
| **Formula A** | **Phase 2 (Log + Velocity)** | $\alpha=0.5024, \beta=15.9473, \lambda=6.4743$ | **4.63%** | **10.49M** | 20 | ~1414 ms | **0.5567** |
| **Formula B** | **Phase 1 (Harmonic)** | $c_0=7.5873$ | **2.44%** | **38.19M** | 32 | ~1460 ms | **0.5898** |
| **Formula B** | **Phase 2 (Harmonic + Vel)**| $c_0=5.7332, \lambda=7.1877$ | **4.63%** | **10.49M** | 20 | ~1172 ms | **0.5708** |
| **Formula D** | **Hybrid Optimization** | $w_A=0.9955, \lambda=3.0944$ | **0.42%** | **10.49M** ⭐ | **20** ⭐ | **~1400 ms** | **0.2589** ⭐ |
| Fixed 2.0x | Baseline (C++ `std::vector`) | — | 4.63% | 10.49M | 20 | ~1400 ms | Baseline |
| Fixed 1.5x | Baseline (Java `ArrayList`) | — | 27.77% | 27.69M | 35 | ~1600 ms | High Waste |
| Python List | Baseline ($1.125\times$) | — | 4.59% | **83.84M** | 102 | ~1900 ms | High Copies |

---

## 4. Key Comparative Findings & Research Insights

1. **Overall Winner:** **Formula D** achieved the lowest unified objective score ($J = \mathbf{0.2589}$), maintaining near-zero waste (**0.42%**) while taking only **20 resizes** and **10.49M copies** (matching Fixed 2.0x copy speed).
2. **Pure Memory Waste Leader:** **Formula A Phase 1** (BO-tuned) achieved an ultra-low **0.05% memory waste** at $10\text{M}$ insertions.
3. **Understanding PDF Baseline Choices:** The PDF reports for Formula C and D evaluated against specific **Reference Configurations** (FA Phase 1 $\alpha=3.5, \beta=10$, FB Phase 1 $c=1.0$). When compared against the **Absolute Best Phase 1 configurations** ($\alpha=1.0, \beta=10$ and $c=1.5$), Phase 2/Hybrid models drastically reduce element copying (>60-70% copy reduction) while maintaining tight memory bounds.
4. **Copy Cost Overhead:** Velocity-aware Phase 2 and Hybrid models reduce element copy migrations from **83.84M (Python List)** down to **10.49M** (an **>87% reduction**).
