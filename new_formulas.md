# Dynamic Array Adaptive Growth Research

## 1. Introduction

Traditional dynamic arrays commonly use fixed growth factors such as:

- 2× growth
- 1.5× growth

Although these methods provide efficient insertion performance, they may waste memory for very large arrays.

This research investigates adaptive growth strategies where the growth factor changes dynamically instead of remaining fixed.

Two adaptive approaches are considered:

- Formula A: Logarithmic Adaptive Growth
- Formula B: Harmonic Sequence Growth

The research will be implemented and benchmarked using Python.

---

# 2. Formula A: Logarithmic Adaptive Growth

## 2.1 Main Formula

The proposed logarithmic growth formula is:

\[
C_{new} = C_{old}
\left(
1 + \frac{\alpha}{\ln(C_{old} + \beta)}
\right)
\]

Where:

- \(C_{old}\) = current capacity
- \(C_{new}\) = new capacity
- \(\alpha\) = growth aggressiveness parameter
- \(\beta\) = logarithmic stabilization parameter

---

## 2.2 Main Concept

The idea is:

- Small arrays grow aggressively
- Large arrays grow conservatively
- Memory waste decreases for large arrays

---

## 2.3 Minimum and Maximum Growth Constraints

To avoid extremely small or extremely large growth values, the growth factor is constrained using minimum and maximum limits.

\[
g(C) =
\min
\left(
g_{max},
\max
\left(
g_{min},
1 + \frac{\alpha}{\ln(C+\beta)}
\right)
\right)
\]

Suggested values:

\[
1.1 \le g_{min} \le 1.2
\]

\[
1.8 \le g_{max} \le 2.0
\]

---

## 2.4 Phase 1: Constant Alpha

In Phase 1:

- \(\alpha\) remains constant
- Only array capacity affects growth

Purpose:

- Compare against fixed growth methods
- Measure memory waste and copy cost

---

## 2.5 Phase 2: Workload-Aware Alpha

In Phase 2, \(\alpha\) becomes dependent on insertion velocity.

Insertion velocity is defined as:

\[
v = \frac{\Delta N}{\Delta t}
\]

Where:

- \(\Delta N\) = number of insertions
- \(\Delta t\) = time gap between insertions

### Adaptive Alpha

\[
\alpha(v) = \alpha_{base} + kv
\]

Final formula:

\[
g(C,v)
=
\min
\left(
g_{max},
\max
\left(
g_{min},
1 + \frac{\alpha(v)}{\ln(C+\beta)}
\right)
\right)
\]

This makes the growth strategy workload-aware.

---

# 3. Formula B: Harmonic Sequence Growth

## 3.1 Main Formula

Formula B uses resize history to determine growth.

\[
C_{new}
=
C_{old}
\left(
1 + \frac{1}{k}
\right)
\]

Where:

- \(k\) = number of resize operations

---

## 3.2 Main Concept

The idea is:

- Early resizes grow aggressively
- Later resizes grow conservatively
- Growth naturally decays over time

### Example

| Resize Count (k) | Growth Factor |
|------------------|---------------|
| 1 | 2.00× |
| 2 | 1.50× |
| 3 | 1.33× |
| 4 | 1.25× |

---

## 3.3 Minimum and Maximum Growth Constraints

To prevent the growth factor from becoming too small or too large:

\[
g(k)
=
\min
\left(
g_{max},
\max
\left(
g_{min},
1 + \frac{1}{k}
\right)
\right)
\]

Suggested values:

\[
1.1 \le g_{min} \le 1.2
\]

\[
1.8 \le g_{max} \le 2.0
\]

---

## 3.4 Phase 1: Standard Harmonic Growth

In Phase 1:

- Growth depends only on resize count
- Workload behavior is ignored

Purpose:

- Analyze resize-history-based adaptation
- Compare against Formula A and fixed growth methods

---

## 3.5 Phase 2: Workload-Aware Harmonic Growth

In Phase 2, insertion velocity is integrated into Formula B.

### Insertion Velocity

\[
v = \frac{\Delta N}{\Delta t}
\]

### Adaptive Harmonic Growth

\[
g(k,v)
=
1 +
\frac{1 + \lambda \ln(1+v)}{k}
\]

Where:

- \(\lambda\) = workload sensitivity parameter
- \(v\) = insertion velocity

To stabilize the formula:

\[
g(k,v)
=
\min
\left(
g_{max},
\max
\left(
g_{min},
1 +
\frac{1 + \lambda \ln(1+v)}{k}
\right)
\right)
\]

---

## 3.6 Expected Behavior

- Burst insertions produce larger growth
- Slow insertions produce smaller growth
- Older arrays still maintain conservative behavior

---

# 4. Evaluation Metrics

The proposed methods will be compared using:

- Memory waste
- Resize count
- Total elements copied
- Execution time

---

# 5. Implementation

The research will be implemented using Python.

A custom dynamic array structure will be developed to:

- Track capacity
- Monitor resize operations
- Measure memory waste
- Apply custom growth strategies

---

# 6. Summary

This research investigates adaptive dynamic array growth strategies using logarithmic and harmonic growth models.

The study includes both:

- Standard adaptive growth
- Workload-aware adaptive growth

The proposed methods aim to reduce memory waste while maintaining efficient insertion performance.