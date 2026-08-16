# Dynamic Growth Factor: Numerical Methods & Development Plan

## 1. Problem Definition
In standard contiguous arrays, the goal is to balance two opposing forces:
1. **Wasted Space (Error)**: The difference between current Capacity ($C$) and actual Size ($N$). We want to minimize $C - N$.
2. **Copy Cost**: Every time the array resizes, all $N$ elements must be copied. We want to minimize the total number of copies $\sum N_{copied}$.

Standard methods (like Java's $1.5\times$ or C++'s $2.0\times$) keep copy costs low ($O(1)$ amortized) but suffer from $O(N)$ wasted space. Our objective is to design a **dynamic, continuous formula** $C_{new} = f(C_{old})$ that minimizes the space error while keeping copy costs mathematically constrained.

---

## 2. Proposed Numerical Formulas for Testing

Here are 5 distinct mathematical formulas we will implement and benchmark. Each takes a different numerical approach to decay the growth factor as the array gets larger.

### Formula A: Logarithmic Decay Multiplier
Instead of a constant $1.5$, the multiplier smoothly decays toward $1.0$ as the array grows, using the natural logarithm.
* **Equation**: $C_{new} = C_{old} \times \left(1 + \frac{\alpha}{\ln(C_{old} + \beta)}\right)$
* **Concept**: Small arrays grow rapidly (e.g., $2.0\times$), while massive arrays grow very conservatively (e.g., $1.05\times$).
* **Parameters to tune**: $\alpha$ (decay rate) and $\beta$ (offset to prevent division by zero).

### Formula B: Fractional Root Growth (Brodnik-Inspired)
Inspired by the $O(\sqrt{N})$ space bound from Brodnik et al., we grow the array by an additive step rather than a multiplier.
* **Equation**: $C_{new} = C_{old} + \alpha \sqrt{C_{old}}$
* **Concept**: The wasted space is strictly bound to $O(\sqrt{N})$. However, because this is applied to a contiguous array, the copy cost will increase. We can test variations like $C_{old}^{0.75}$ to find the sweet spot between time and space.
* **Parameters to tune**: $\alpha$ (step coefficient) and the exponent (e.g., $0.5$ vs $0.75$).

### Formula C: Harmonic Sequence Growth
The multiplier reduces harmonically with each resize event $k$.
* **Equation**: $C_{new} = C_{old} \times \left(1 + \frac{1}{k}\right)$  *(where $k$ is the number of times the array has resized)*
* **Concept**: The 1st resize is $2.0\times$, the 2nd is $1.5\times$, the 3rd is $1.33\times$, the 4th is $1.25\times$, etc. This creates a beautifully smooth decay curve that guarantees bounded total copy costs but rapidly shrinks the waste percentage.

### Formula D: Golden Ratio / Fibonacci Step
Using the properties of the golden ratio $\Phi \approx 1.618$ and Fibonacci sequences, which are numerically optimal for certain packing problems.
* **Equation**: $C_{new} = C_{old} + C_{previous\_old}$ 
* **Concept**: Capacity follows the Fibonacci sequence. The growth ratio converges to $\approx 1.618$, but we can adapt this to a "Delayed Fibonacci" sequence (e.g., $C_k = C_{k-1} + C_{k-3}$) to converge to much smaller fractional ratios like $1.22\times$ while maintaining integer arithmetic.

### Formula E: Adaptive Velocity (Predictive)
A numerical method based on calculus (derivatives). It measures the *velocity* of insertions.
* **Equation**: $C_{new} = C_{old} + \left( \frac{\Delta N}{\Delta t} \times \text{Buffer\_Factor} \right)$
* **Concept**: If the program is doing a massive burst of insertions, the derivative is high, so the array grows substantially. If insertions are slow and sporadic, it grows tightly. This requires tracking time or instruction cycles between resizes.

---

## 3. Evaluation Metrics

To mathematically evaluate which formula is best, we will compute a **Cost Function (Loss)** for each simulation:

$$ \text{Loss} = W_1 \left( \frac{\text{Total Wasted Space Area}}{\text{Total Insertions}} \right) + W_2 \left( \frac{\text{Total Elements Copied}}{\text{Total Insertions}} \right) $$

We will plot the **Pareto Front** of these formulas to find the one that minimizes the loss function.

---

## 4. Development & Testing Plan

### Phase 1: Implementation of Formulas
* Create a new Python framework `dynamic_arrays.py`.
* Implement the 5 formulas above as interchangeable strategy functions.

### Phase 2: Standard Workload Benchmarking
* Run all 5 formulas against the standard benchmark ($N = 10,000$ to $1,000,000$ continuous insertions).
* Generate comparative overlay charts (Wasted Space vs Copy Cost).

### Phase 3: Variable Workload Benchmarking
* Real-world arrays don't just grow linearly. We will simulate:
  * **Burst workloads**: 1000 insertions instantly, then pause, then 1000 more.
  * **Slow workloads**: 1 insertion every few seconds.
* Observe how the adaptive numerical formulas perform compared to static formulas.

### Phase 4: Parameter Optimization (Gradient Descent)
* Once we identify the best mathematical curve (e.g., Formula A or C), we will run a numerical optimization script to find the exact perfect values for the constants ($\alpha, \beta$) that minimize our Loss function.
