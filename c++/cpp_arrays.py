"""
C++ std::vector Behavior Replication & Analysis
================================================
Replicates the internal resizing behavior of a typical C++ std::vector:
  - Default initial capacity: 1 (or 10 for easier comparison with Java)
  - Growth factor: 2.0x  (newCapacity = oldCapacity * 2)
  - Copies all elements into the new backing array on resize

Produces 6 matplotlib charts:
  1. Insertions vs Capacity Growth (step chart)
  2. Size, Capacity & Wasted Space over insertions
  3. Time (copy cost) per Resize Event
  4. Cumulative Copy Cost vs Insertions
  5. Load Factor (size / capacity) over insertions
  6. Space Efficiency — Wasted Ratio over insertions

Author : Research Project – Dynamic Growth Factor Study
Date   : 2026-05-14
"""

import sys
import os
import time

# Ensure Unicode output works on Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import matplotlib
# matplotlib.use("Agg")  # Removed so the graph window can pop up interactively
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np


# ──────────────────────────────────────────────
# 1.  C++ Vector Simulator
# ──────────────────────────────────────────────
class CppVectorSimulator:
    """Faithfully replicates typical C++ std::vector resizing semantics."""

    DEFAULT_CAPACITY = 10

    def __init__(self, initial_capacity: int = DEFAULT_CAPACITY):
        self.capacity: int = initial_capacity
        self.size: int = 0
        # The "backing array" — we don't actually need the data, but we
        # allocate a real Python list so timing measurements are realistic.
        self._data: list = [None] * self.capacity

        # ── Tracking metrics ──
        self.history_size: list[int] = []          # size after each add()
        self.history_capacity: list[int] = []      # capacity after each add()
        self.history_wasted: list[int] = []        # capacity - size
        self.history_load_factor: list[float] = [] # size / capacity

        # Resize-event specific
        self.resize_events: list[dict] = []        # per-resize snapshot

    # -- C++ typical growth formula ------------------------------------------
    @staticmethod
    def _new_capacity(old: int) -> int:
        """Mirrors std::vector capacity growth:
           newCapacity = oldCapacity * 2
        """
        return old * 2 if old > 0 else 1

    # -- Core operations -------------------------------------------------------
    def add(self, value=None):
        """Equivalent to std::vector push_back(e)."""
        if self.size == self.capacity:
            self._grow()
        self._data[self.size] = value
        self.size += 1
        self._record_snapshot()

    def _grow(self):
        """Resize the backing array — mirrors std::vector growth."""
        old_cap = self.capacity
        new_cap = self._new_capacity(old_cap)

        # Measure the actual copy cost (wall-clock)
        t0 = time.perf_counter_ns()
        new_data = [None] * new_cap
        for i in range(self.size):
            new_data[i] = self._data[i]
        t1 = time.perf_counter_ns()

        copy_time_us = (t1 - t0) / 1_000  # microseconds

        self._data = new_data
        self.capacity = new_cap

        self.resize_events.append({
            "insertion_number": self.size + 1,   # the add() that triggered it
            "old_capacity": old_cap,
            "new_capacity": new_cap,
            "elements_copied": self.size,
            "growth_ratio": new_cap / old_cap if old_cap > 0 else 0,
            "copy_time_us": copy_time_us,
        })

    def _record_snapshot(self):
        self.history_size.append(self.size)
        self.history_capacity.append(self.capacity)
        self.history_wasted.append(self.capacity - self.size)
        self.history_load_factor.append(self.size / self.capacity)


# ──────────────────────────────────────────────
# 2.  Run the Simulation
# ──────────────────────────────────────────────
def run_simulation(n: int = 2000) -> CppVectorSimulator:
    """Insert *n* elements and return the fully-instrumented simulator."""
    sim = CppVectorSimulator()
    for i in range(n):
        sim.add(i)
    return sim


# ──────────────────────────────────────────────
# 3.  Plotting Helpers
# ──────────────────────────────────────────────
# Color palette — vibrant but cohesive
C_PRIMARY   = "#E17055"   # coral/orange for C++
C_SECONDARY = "#00CEC9"   # teal
C_ACCENT    = "#FD79A8"   # pink
C_WARN      = "#FDCB6E"   # amber
C_DANGER    = "#E17055"   # coral
C_SUCCESS   = "#00B894"   # green
C_BG        = "#1E1E2E"   # dark bg
C_GRID      = "#3B3B5C"   # subtle grid
C_TEXT       = "#CDD6F4"  # light text


def _style_ax(ax, title, xlabel, ylabel):
    """Apply a consistent dark theme to an axes."""
    ax.set_facecolor(C_BG)
    ax.set_title(title, color=C_TEXT, fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel, color=C_TEXT, fontsize=10)
    ax.set_ylabel(ylabel, color=C_TEXT, fontsize=10)
    ax.tick_params(colors=C_TEXT, labelsize=8)
    ax.grid(True, color=C_GRID, linewidth=0.4, alpha=0.6)
    for spine in ax.spines.values():
        spine.set_color(C_GRID)


def plot_results(sim: CppVectorSimulator):
    """Generate 6 publication-quality charts from the simulation data."""

    insertions = np.arange(1, len(sim.history_size) + 1)
    size_arr   = np.array(sim.history_size)
    cap_arr    = np.array(sim.history_capacity)
    wasted_arr = np.array(sim.history_wasted)
    load_arr   = np.array(sim.history_load_factor)

    resize_ins   = [e["insertion_number"] for e in sim.resize_events]
    resize_old   = [e["old_capacity"] for e in sim.resize_events]
    resize_new   = [e["new_capacity"] for e in sim.resize_events]
    resize_copy  = [e["elements_copied"] for e in sim.resize_events]
    resize_time  = [e["copy_time_us"] for e in sim.resize_events]
    resize_ratio = [e["growth_ratio"] for e in sim.resize_events]

    cumulative_copies = np.cumsum(resize_copy)

    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    fig.patch.set_facecolor("#11111B")
    fig.suptitle(
        "C++ std::vector (2.0× Growth Factor) — Resizing Behaviour Analysis",
        color=C_TEXT, fontsize=16, fontweight="bold", y=0.98,
    )

    # ── Chart 1: Insertions vs Capacity (step) ───────────────────────────
    ax = axes[0, 0]
    _style_ax(ax, "① Insertions vs Capacity Growth", "Number of Insertions", "Capacity")
    ax.step(insertions, cap_arr, where="post", color=C_PRIMARY, linewidth=1.8,
            label="Capacity")
    ax.plot(insertions, size_arr, color=C_SECONDARY, linewidth=1.0,
            alpha=0.7, label="Size (elements stored)")
    # Mark resize points
    for ri, rc in zip(resize_ins, resize_new):
        ax.plot(ri, rc, "o", color=C_ACCENT, markersize=5, zorder=5)
    ax.fill_between(insertions, size_arr, cap_arr, color=C_ACCENT, alpha=0.10,
                    label="Wasted space")
    ax.legend(fontsize=8, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)

    # ── Chart 2: Size, Capacity & Wasted Space ───────────────────────────
    ax = axes[0, 1]
    _style_ax(ax, "② Size · Capacity · Remaining Capacity", "Number of Insertions", "Elements")
    ax.plot(insertions, cap_arr,   color=C_PRIMARY,   linewidth=1.6, label="Capacity")
    ax.plot(insertions, size_arr,  color=C_SECONDARY,  linewidth=1.6, label="Current Size")
    ax.plot(insertions, wasted_arr, color=C_DANGER, linewidth=1.2, alpha=0.8,
            label="Remaining (wasted) slots")
    ax.fill_between(insertions, 0, wasted_arr, color=C_DANGER, alpha=0.12)
    ax.legend(fontsize=8, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)

    # ── Chart 3: Copy Cost per Resize Event ──────────────────────────────
    ax = axes[1, 0]
    _style_ax(ax, "③ Time per Resize Event (Copy Cost)", "Resize Event #", "Time (µs)")
    event_idx = np.arange(1, len(resize_time) + 1)
    bars = ax.bar(event_idx, resize_time, color=C_PRIMARY, edgecolor=C_ACCENT,
                  linewidth=0.5, alpha=0.85)
    # Gradient-like coloring by magnitude
    max_t = max(resize_time) if resize_time else 1
    for bar, t in zip(bars, resize_time):
        ratio = t / max_t
        r = int(225 - 50 * ratio)  # coral to dark red
        g = int(112 - 90 * ratio)
        b = int(85 - 50 * ratio)
        bar.set_facecolor(f"#{r:02x}{g:02x}{b:02x}")
    ax.set_xticks(event_idx[::max(1, len(event_idx)//15)])

    # ── Chart 4: Cumulative Copy Cost ────────────────────────────────────
    ax = axes[1, 1]
    _style_ax(ax, "④ Cumulative Elements Copied vs Insertions",
              "Resize Event #", "Total Elements Copied")
    ax.plot(event_idx, cumulative_copies, color=C_SECONDARY, linewidth=2,
            marker="o", markersize=4, markerfacecolor=C_ACCENT)
    ax.fill_between(event_idx, 0, cumulative_copies, color=C_SECONDARY, alpha=0.12)
    # Annotate amortized cost
    if len(cumulative_copies):
        amort = cumulative_copies[-1] / len(sim.history_size)
        ax.text(0.02, 0.95,
                f"Amortized copy cost ≈ {amort:.2f} copies/insertion",
                transform=ax.transAxes, fontsize=9, color=C_WARN,
                verticalalignment="top",
                bbox=dict(boxstyle="round,pad=0.3", fc=C_BG, ec=C_GRID, alpha=0.9))

    # ── Chart 5: Load Factor ─────────────────────────────────────────────
    ax = axes[2, 0]
    _style_ax(ax, "⑤ Load Factor (size / capacity)", "Number of Insertions", "Load Factor")
    ax.plot(insertions, load_arr, color=C_SUCCESS, linewidth=1.0, alpha=0.85)
    ax.axhline(y=1.0, color=C_DANGER, linewidth=0.8, linestyle="--", alpha=0.5,
               label="Full (load = 1.0)")
    ax.axhline(y=0.5, color=C_WARN, linewidth=0.8, linestyle=":", alpha=0.5,
               label="Avg after resize ≈ 0.5")
    ax.set_ylim(0, 1.1)
    ax.legend(fontsize=8, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)

    # ── Chart 6: Wasted Ratio ────────────────────────────────────────────
    ax = axes[2, 1]
    _style_ax(ax, "⑥ Space Waste Ratio (wasted / capacity)", "Number of Insertions",
              "Waste Ratio")
    waste_ratio = wasted_arr / cap_arr
    ax.fill_between(insertions, 0, waste_ratio, color=C_ACCENT, alpha=0.25)
    ax.plot(insertions, waste_ratio, color=C_ACCENT, linewidth=1.0)
    ax.axhline(y=0.5, color=C_DANGER, linewidth=0.8, linestyle="--", alpha=0.5,
               label="50 % waste threshold")
    ax.set_ylim(0, 1.0)
    avg_waste = np.mean(waste_ratio)
    ax.axhline(y=avg_waste, color=C_WARN, linewidth=1, linestyle=":",
               label=f"Avg waste ratio = {avg_waste:.2%}")
    ax.legend(fontsize=8, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig("cpp_vector_analysis.png", dpi=180, facecolor="#11111B",
                bbox_inches="tight")
    plt.show()


# ──────────────────────────────────────────────
# 4.  Console Summary
# ──────────────────────────────────────────────
def print_summary(sim: CppVectorSimulator):
    n = len(sim.history_size)
    total_copies = sum(e["elements_copied"] for e in sim.resize_events)
    print("=" * 62)
    print("  C++ std::vector (2.0× Growth) — Simulation Summary")
    print("=" * 62)
    print(f"  Total insertions          : {n:,}")
    print(f"  Final capacity            : {sim.capacity:,}")
    print(f"  Final size                : {sim.size:,}")
    print(f"  Wasted slots (final)      : {sim.capacity - sim.size:,}")
    print(f"  Number of resizes         : {len(sim.resize_events)}")
    print(f"  Total elements copied     : {total_copies:,}")
    print(f"  Amortized copies/insert   : {total_copies / n:.4f}")
    print(f"  Avg load factor           : {np.mean(sim.history_load_factor):.4f}")
    print(f"  Min load factor           : {min(sim.history_load_factor):.4f}")
    print("-" * 62)
    print("  Resize Event Log:")
    print(f"  {'#':>3}  {'Trigger':>8}  {'OldCap':>8}  {'NewCap':>8}  "
          f"{'Copied':>8}  {'Ratio':>6}  {'Time(µs)':>10}")
    print("-" * 62)
    for idx, e in enumerate(sim.resize_events, 1):
        print(f"  {idx:3d}  {e['insertion_number']:8,}  {e['old_capacity']:8,}  "
              f"{e['new_capacity']:8,}  {e['elements_copied']:8,}  "
              f"{e['growth_ratio']:6.2f}  {e['copy_time_us']:10.1f}")
    print("=" * 62)


# ──────────────────────────────────────────────
# 5.  Entry Point
# ──────────────────────────────────────────────
if __name__ == "__main__":
    NUM_INSERTIONS = 2000
    print(f"\n> Running C++ std::vector simulation with {NUM_INSERTIONS:,} insertions ...\n")
    simulator = run_simulation(NUM_INSERTIONS)
    print_summary(simulator)
    plot_results(simulator)
