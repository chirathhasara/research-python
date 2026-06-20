# Hybrid Dynamic Array Growth Strategies

## Formula C and Formula D

---

# 1. Introduction

Previous research introduced two adaptive dynamic array growth models:

### Formula A — Capacity-Aware Logarithmic Growth

Formula A determines the growth factor using the current array capacity and workload velocity.

### Formula B — Workload-Aware Harmonic Growth

Formula B determines the growth factor using resize history and workload velocity.

Experimental results showed that:

* Formula A performs well across most workloads.
* Formula B performs exceptionally well under bursty and spiky workloads.
* Both formulas possess complementary strengths.

To leverage the advantages of both approaches, two hybrid growth strategies are proposed:

1. Formula C — Weighted Capacity-History Hybrid
2. Formula D — Dynamic Weight Hybrid

---

# 2. Formula C: Weighted Capacity-History Hybrid

## 2.1 Motivation

Formula A contributes:

* Capacity awareness
* Stable behavior
* Good memory utilization

Formula B contributes:

* Burst responsiveness
* Resize-history awareness
* Aggressive reaction during spikes

Formula C combines both components using fixed weights.

---

## 2.2 Growth Formula

[
g(C,k,v)
========

1
+
w_A
\left(
\frac{\alpha+\lambda\ln(1+v)}
{\ln(C+\beta)}
\right)
+
w_B
\left(
\frac{\mu}{k}
\right)
]

---

## 2.3 Capacity Update

[
C_{new}
=======

C_{old}
\times
g(C,k,v)
]

---

## 2.4 Parameter Definitions

### Current Capacity

[
C
]

Current capacity of the dynamic array.

---

### New Capacity

[
C_{new}
]

Capacity after resizing.

---

### Resize Count

[
k
]

Number of resize operations performed.

Examples:

| Resize Number | k |
| ------------- | - |
| First Resize  | 1 |
| Second Resize | 2 |
| Third Resize  | 3 |

---

### Insertion Velocity

[
v
=

\frac{\Delta N}{\Delta t}
]

Where:

* (\Delta N) = number of insertions
* (\Delta t) = elapsed time interval

Velocity measures workload intensity.

---

### Base Growth Aggressiveness

[
\alpha
]

Controls the baseline growth contribution inherited from Formula A.

Recommended:

[
\alpha = 3
]

---

### Logarithmic Stabilization Constant

[
\beta
]

Prevents instability for small capacities.

Recommended:

[
\beta = 5
]

---

### Velocity Sensitivity

[
\lambda
]

Controls how strongly workload velocity affects growth.

Recommended:

[
\lambda = 2
]

---

### Harmonic Influence

[
\mu
]

Controls the contribution inherited from Formula B.

Recommended:

[
\mu = 1
]

---

### Formula A Weight

[
w_A
]

Contribution of Formula A.

---

### Formula B Weight

[
w_B
]

Contribution of Formula B.

Constraint:

[
w_A+w_B=1
]

---

## 2.5 Recommended Weight Configurations

### Capacity-Oriented Configuration

[
w_A=0.8
]

[
w_B=0.2
]

Characteristics:

* Strong Formula A influence
* Low memory waste
* Stable growth

---

### Balanced Configuration

[
w_A=0.7
]

[
w_B=0.3
]

Characteristics:

* Balanced behavior
* Suitable for mixed workloads

---

### Burst-Oriented Configuration

[
w_A=0.6
]

[
w_B=0.4
]

Characteristics:

* Increased responsiveness
* Better burst handling

---

## 2.6 Expected Behavior

### Small Arrays

Small capacities produce larger growth factors.

Result:

* Faster expansion
* Reduced early resize frequency

---

### Large Arrays

As capacity grows:

[
\ln(C+\beta)
]

increases.

Result:

* More conservative growth
* Better memory efficiency

---

### High Velocity Workloads

As velocity increases:

[
\ln(1+v)
]

increases.

Result:

* Temporary growth acceleration
* Fewer resizes during bursts

---

### Mature Arrays

As resize count increases:

[
\frac{\mu}{k}
\rightarrow 0
]

Result:

* Harmonic influence naturally fades
* Capacity-awareness becomes dominant

---

# 3. Formula D: Dynamic Weight Hybrid

## 3.1 Motivation

Formula C uses fixed weights.

However, workload characteristics change during execution.

Formula D dynamically adjusts the importance of Formula A and Formula B according to insertion velocity.

---

## 3.2 Dynamic Weight Function

[
w(v)
====

\frac{\ln(1+v)}
{\ln(1+v)+s}
]

---

## 3.3 Growth Formula

[
g(C,k,v)
========

1
+
w(v)
\left(
\frac{1+\lambda\ln(1+v)}
{k}
\right)
+
(1-w(v))
\left(
\frac{\alpha}
{\ln(C+\beta)}
\right)
]

---

## 3.4 Capacity Update

[
C_{new}
=======

C_{old}
\times
g(C,k,v)
]

---

## 3.5 Additional Parameter

### Smoothing Constant

[
s
]

Controls how quickly Formula B becomes dominant.

Recommended:

[
s=5
]

---

## 3.6 Recommended Parameters

### Formula A Parameters

[
\alpha=3
]

[
\beta=5
]

---

### Formula B Parameter

[
\lambda=5
]

---

### Dynamic Weight Parameter

[
s=5
]

---

## 3.7 Expected Behavior

### Low Velocity Workloads

When velocity is small:

[
w(v)
]

remains small.

Result:

* Formula A dominates
* Stable growth
* Low memory waste

---

### High Velocity Workloads

When velocity becomes large:

[
w(v)
]

increases.

Result:

* Formula B gains influence
* Strong burst response
* Reduced copy overhead

---

### Bursty Workloads

The model automatically shifts toward harmonic behavior during bursts and returns to logarithmic behavior afterward.

---

# 4. Growth Bounds

To prevent unrealistic growth factors, lower and upper bounds should be applied after calculating the raw growth factor.

---

## Lower Bound

[
g_{min}=1.1
]

Purpose:

* Prevents excessively small growth.
* Avoids resize thrashing.

---

## Upper Bound

[
g_{max}=2.0
]

Purpose:

* Prevents excessive memory allocation.
* Avoids unstable growth behavior.

---

## Final Growth Factor

For either Formula C or Formula D:

[
g_{final}
=========

\min(g_{max},
\max(g_{min},g))
]

---

## Final Capacity Update

[
C_{new}
=======

C_{old}
\times
g_{final}
]

---

# 5. Experimental Plan

The following configurations are recommended:

## Formula C

1. (w_A=0.8,;w_B=0.2)
2. (w_A=0.7,;w_B=0.3)
3. (w_A=0.6,;w_B=0.4)

---

## Formula D

1. (s=3)
2. (s=5)
3. (s=10)

---

## Baselines

Compare against:

* Fixed 1.5× Growth
* Fixed 2.0× Growth
* Formula A Phase 1
* Formula A Phase 2
* Formula B Phase 1
* Formula B Phase 2
* Formula C
* Formula D

---

# 6. Evaluation Metrics

Evaluate all strategies using:

* Memory Waste (%)
* Resize Count
* Total Elements Copied
* Copies per Insert
* Average Growth Factor
* Execution Time

---

# 7. Research Objective

The objective of the hybrid formulas is to combine:

* Capacity awareness
* Resize-history awareness
* Workload awareness

within a single adaptive dynamic array growth model.

Formula C emphasizes simplicity and stability, while Formula D emphasizes adaptive behavior and workload-driven decision making.
