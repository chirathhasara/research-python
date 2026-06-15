"""
Brodnik Optimal Array Simulation & Analysis
================================================
Replicates the optimal resizing strategy from the paper:
"Resizable Arrays in Optimal Time and Space" (Brodnik et al.)

Key mechanisms simulated:
  - Block-based storage (no full array copies)
  - Superblocks containing exponentially growing block sizes
  - Space wasted is strictly O(sqrt(n))
  - Copy cost per element is O(1) amortized (zero for data elements)

Produces 6 matplotlib charts for comparison with Java's ArrayList.

Author : Research Project – Dynamic Growth Factor Study
Date   : 2026-05-14
"""

import sys
import time

# Ensure Unicode output works on Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import matplotlib
# matplotlib.use("Agg") # Commented out so the graph window can pop up interactively
import matplotlib.pyplot as plt
import numpy as np


# ──────────────────────────────────────────────
# 1.  Brodnik Array Simulator
# ──────────────────────────────────────────────
class BrodnikArraySimulator:
    """
    Simulates the block allocation strategy of Brodnik et al.
    Instead of a single contiguous array, it allocates smaller blocks.
    Superblock k has 2^(floor(k/2)) blocks, each of size 2^(ceil(k/2)).
    """

    def __init__(self):
        self.capacity: int = 0
        self.size: int = 0
        
        # Block tracking
        self.blocks = []
        self.k = 0  # Superblock index
        self.blocks_allocated_in_k = 0
        
        # ── Tracking metrics ──
        self.history_size: list[int] = []
        self.history_capacity: list[int] = []
        self.history_wasted: list[int] = []
        self.history_load_factor: list[float] = []

        # Resize-event specific (here "resize" means "allocate a new block")
        self.resize_events: list[dict] = []

        # We start by allocating the first block
        self._allocate_next_block()

    def _allocate_next_block(self):
        """Calculates and allocates the next block size based on the paper's formula."""
        # Calculate sizes for current superblock k
        num_blocks = 2 ** (self.k // 2)
        block_size = 2 ** ((self.k + 1) // 2)
        
        # Measure allocation time (simulating allocation)
        t0 = time.perf_counter_ns()
        new_block = [None] * block_size
        t1 = time.perf_counter_ns()
        
        self.blocks.append(new_block)
        
        old_cap = self.capacity
        self.capacity += block_size
        
        self.resize_events.append({
            "insertion_number": self.size + 1,
            "old_capacity": old_cap,
            "new_capacity": self.capacity,
            "block_size_allocated": block_size,
            "elements_copied": 0, # Brodnik DOES NOT copy old elements!
            "alloc_time_us": (t1 - t0) / 1_000,
        })
        
        self.blocks_allocated_in_k += 1
        # If we exhausted the blocks for this superblock, move to next k
        if self.blocks_allocated_in_k >= num_blocks:
            self.k += 1
            self.blocks_allocated_in_k = 0

    def add(self, value=None):
        if self.size == self.capacity:
            self._allocate_next_block()
        
        self.size += 1
        self._record_snapshot()

    def _record_snapshot(self):
        self.history_size.append(self.size)
        self.history_capacity.append(self.capacity)
        self.history_wasted.append(self.capacity - self.size)
        self.history_load_factor.append(self.size / self.capacity)


# ──────────────────────────────────────────────
# 2.  Run the Simulation
# ──────────────────────────────────────────────
def run_simulation(n: int = 2000) -> BrodnikArraySimulator:
    sim = BrodnikArraySimulator()
    for i in range(n):
        sim.add(i)
    return sim


# ──────────────────────────────────────────────
# 3.  Plotting Helpers
# ──────────────────────────────────────────────
# Color palette
C_PRIMARY   = "#00CEC9"   # teal
C_SECONDARY = "#6C5CE7"   # purple
C_ACCENT    = "#00B894"   # green
C_WARN      = "#FDCB6E"   # amber
C_DANGER    = "#E17055"   # coral
C_BG        = "#1E1E2E"   # dark bg
C_GRID      = "#3B3B5C"   # subtle grid
C_TEXT       = "#CDD6F4"  # light text

def _style_ax(ax, title, xlabel, ylabel):
    ax.set_facecolor(C_BG)
    ax.set_title(title, color=C_TEXT, fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel, color=C_TEXT, fontsize=10)
    ax.set_ylabel(ylabel, color=C_TEXT, fontsize=10)
    ax.tick_params(colors=C_TEXT, labelsize=8)
    ax.grid(True, color=C_GRID, linewidth=0.4, alpha=0.6)
    for spine in ax.spines.values():
        spine.set_color(C_GRID)

def plot_results(sim: BrodnikArraySimulator):
    insertions = np.arange(1, len(sim.history_size) + 1)
    size_arr   = np.array(sim.history_size)
    cap_arr    = np.array(sim.history_capacity)
    wasted_arr = np.array(sim.history_wasted)
    load_arr   = np.array(sim.history_load_factor)

    resize_ins   = [e["insertion_number"] for e in sim.resize_events]
    resize_new   = [e["new_capacity"] for e in sim.resize_events]
    
    # Notice we use elements_copied which is always 0, so we plot block_size instead
    block_sizes  = [e["block_size_allocated"] for e in sim.resize_events]

    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    fig.patch.set_facecolor("#11111B")
    fig.suptitle(
        "Brodnik et al. Optimal Array — Resizing Behaviour Analysis",
        color=C_TEXT, fontsize=16, fontweight="bold", y=0.98,
    )

    # ── Chart 1: Insertions vs Capacity ───────────────────────────
    ax = axes[0, 0]
    _style_ax(ax, "① Capacity Growth (Tight O(√n) curve)", "Number of Insertions", "Capacity")
    ax.step(insertions, cap_arr, where="post", color=C_PRIMARY, linewidth=2.5,
            label="Capacity (sum of blocks)")
    ax.plot(insertions, size_arr, color=C_SECONDARY, linewidth=1.5,
            alpha=0.9, label="Size")
    ax.fill_between(insertions, size_arr, cap_arr, color=C_ACCENT, alpha=0.15,
                    label="Wasted space (minimal)")
    ax.legend(fontsize=9, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)

    # ── Chart 2: Size, Capacity & Wasted Space ───────────────────────────
    ax = axes[0, 1]
    _style_ax(ax, "② Wasted Slots (Grows as O(√n))", "Number of Insertions", "Elements")
    ax.plot(insertions, wasted_arr, color=C_DANGER, linewidth=1.5, alpha=0.9,
            label="Wasted slots (Max value = current block size)")
    ax.fill_between(insertions, 0, wasted_arr, color=C_DANGER, alpha=0.2)
    # Add an O(sqrt(n)) trendline to prove the paper's point
    sqrt_trend = np.sqrt(insertions) * 1.5  # scaled for visual comparison
    ax.plot(insertions, sqrt_trend, color=C_WARN, linestyle="--", linewidth=1.5, 
            label="O(√n) boundary curve")
    ax.legend(fontsize=9, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)

    # ── Chart 3: Block Size Allocated ──────────────────────────────
    ax = axes[1, 0]
    _style_ax(ax, "③ Size of New Block Allocated (No Copying!)", "Allocation Event #", "Block Size")
    event_idx = np.arange(1, len(block_sizes) + 1)
    ax.bar(event_idx, block_sizes, color=C_PRIMARY, edgecolor=C_ACCENT, alpha=0.8)
    
    # ── Chart 4: Cumulative Copy Cost ────────────────────────────────────
    ax = axes[1, 1]
    _style_ax(ax, "④ Cumulative Elements Copied", "Number of Insertions", "Total Elements Copied")
    ax.plot(insertions, np.zeros_like(insertions), color=C_ACCENT, linewidth=3,
            label="Zero data copied (O(1) time)")
    ax.text(0.5, 0.5, "Brodnik array never copies old data!\nCopy cost is exactly 0.", 
            color=C_WARN, fontsize=12, ha="center", va="center", transform=ax.transAxes)
    ax.legend(fontsize=9, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)

    # ── Chart 5: Load Factor ─────────────────────────────────────────────
    ax = axes[2, 0]
    _style_ax(ax, "⑤ Load Factor (Approaches 1.0)", "Number of Insertions", "Load Factor")
    ax.plot(insertions, load_arr, color=C_PRIMARY, linewidth=1.5, alpha=0.9)
    ax.axhline(y=1.0, color=C_DANGER, linewidth=1, linestyle="--", alpha=0.6)
    ax.set_ylim(0.5, 1.05)

    # ── Chart 6: Wasted Ratio ────────────────────────────────────────────
    ax = axes[2, 1]
    _style_ax(ax, "⑥ Space Waste Ratio (Decays to 0%)", "Number of Insertions", "Waste Ratio")
    waste_ratio = wasted_arr / cap_arr
    ax.fill_between(insertions, 0, waste_ratio, color=C_ACCENT, alpha=0.25)
    ax.plot(insertions, waste_ratio, color=C_ACCENT, linewidth=1.5)
    ax.axhline(y=0.0, color=C_TEXT, linewidth=1, linestyle="-", alpha=0.5)
    ax.set_ylim(-0.05, 0.5)
    
    avg_waste = np.mean(waste_ratio)
    ax.axhline(y=avg_waste, color=C_WARN, linewidth=1, linestyle=":",
               label=f"Avg waste ratio = {avg_waste:.2%}")
    ax.legend(fontsize=9, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig("brodnik_optimal_analysis.png", dpi=180, facecolor="#11111B", bbox_inches="tight")
    plt.show()


# ──────────────────────────────────────────────
# 4.  Console Summary
# ──────────────────────────────────────────────
def print_summary(sim: BrodnikArraySimulator):
    n = len(sim.history_size)
    print("=" * 70)
    print("  Brodnik et al. Optimal Array — Simulation Summary")
    print("=" * 70)
    print(f"  Total insertions          : {n:,}")
    print(f"  Final capacity            : {sim.capacity:,}")
    print(f"  Final size                : {sim.size:,}")
    print(f"  Wasted slots (final)      : {sim.capacity - sim.size:,}")
    print(f"  Total blocks allocated    : {len(sim.resize_events)}")
    print(f"  Total data copied         : 0 (Key advantage!)")
    print(f"  Avg load factor           : {np.mean(sim.history_load_factor):.4f}")
    print("-" * 70)
    print("  Allocation Event Log (First 15 & Last 5):")
    print(f"  {'#':>3}  {'Trigger':>8}  {'OldCap':>8}  {'NewCap':>8}  "
          f"{'BlockSize':>9}  {'Copied':>6}")
    print("-" * 70)
    
    def print_event(idx, e):
        print(f"  {idx:3d}  {e['insertion_number']:8,}  {e['old_capacity']:8,}  "
              f"{e['new_capacity']:8,}  {e['block_size_allocated']:9,}  "
              f"{e['elements_copied']:6d}")

    for idx, e in enumerate(sim.resize_events):
        if idx < 15 or idx >= len(sim.resize_events) - 5:
            print_event(idx + 1, e)
        elif idx == 15:
            print("  ...  " + " " * 45)
            
    print("=" * 70)


# ──────────────────────────────────────────────
# 5.  Entry Point
# ──────────────────────────────────────────────
if __name__ == "__main__":
    NUM_INSERTIONS = 2000
    print(f"\n> Running Brodnik Optimal Array simulation with {NUM_INSERTIONS:,} insertions ...\n")
    simulator = run_simulation(NUM_INSERTIONS)
    print_summary(simulator)
    plot_results(simulator)
