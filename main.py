"""
main.py – run base-case and parameter-sweep simulations.

Usage:
  python main.py            # plots base case + default sweeps
  
Edit the SWEEP SECTION at the bottom to change which parameter you vary.
"""

import numpy as np
import matplotlib.pyplot as plt
from config import (
    MAX_BATTERY_MWH, DEFAULT_BRIGHTNESS, SCREEN_AREA_MM2, SIM_DURATION_MIN,
)
from model import (
    AppEvent, IdleSchedule, calibrate_usage,
    simulate, power_to_battery,
)

# =====================================================================
# 1.  Define idle-radio schedules (one per sample day)
# =====================================================================

def build_schedules() -> list[IdleSchedule]:
    s1 = IdleSchedule(SIM_DURATION_MIN)
    s1.add(0,       5*60,  wifi="connected", bt=True)
    s1.add(5*60,   14*60,  cell="5G", wifi="searching", bt=True)
    s1.add(14*60,  SIM_DURATION_MIN, wifi="connected", bt=True)

    s2 = IdleSchedule(SIM_DURATION_MIN)
    s2.add(0,      11*60,  wifi="connected")
    s2.add(11*60,  16*60,  cell="5G", wifi="searching")
    s2.add(16*60,  SIM_DURATION_MIN, wifi="connected")

    return [s1, s2]

# =====================================================================
# 2.  Define app-usage events
# =====================================================================

EVENTS: list[list[AppEvent]] = [
    [   # Day 1
        AppEvent(6*60,  48,  "coros",     0.32, "",  "5G",   50,  "high"),
        AppEvent(8*60,  121, "life360",   0.09, "",  "",    200,  "low"),
        AppEvent(15*60, 10,  "gmail",     0.02, "d", "wifi", 70,  "med"),
        AppEvent(17*60, 18,  "polytopia", 0.04, "d", "",    130,  "high"),
        AppEvent(19*60, 26,  "chrome",    0.04, "d", "wifi",100,  "low"),
    ],
    [   # Day 2
        AppEvent(5*60,  180, "tiktok",    0.27, "d", "wifi",125,  "med"),
        AppEvent(8*60,  180, "pandora",   0.08, "",  "",    125,  "med"),
        AppEvent(11*60, 28,  "maps",      0.07, "d", "5G",  200,  "med"),
        AppEvent(12*60, 16,  "chrome",    0.04, "d", "5G",  200,  "low"),
        AppEvent(15*60+5, 28,"maps",      0.07, "d", "5G",  200,  "med"),
        AppEvent(16*60, 114, "tiktok",    0.18, "d", "wifi",125,  "med"),
        AppEvent(18*60, 17,  "phone",     0.02, "",  "wifi",200,  "low"),
        AppEvent(18*60+30, 19,"messages", 0.03, "d", "wifi",200,  "low"),
        AppEvent(19*60, 120, "tiktok",    0.18, "d", "wifi",125,  "med"),
    ],
]

# =====================================================================
# 3.  Calibrate CPU-usage from measured battery drain
# =====================================================================

schedules = build_schedules()
baselines = [s.build_baseline() for s in schedules]

all_usage: dict[str, list[float]] = {}
for evs, bl in zip(EVENTS, baselines):
    for k, v in calibrate_usage(evs, bl, DEFAULT_BRIGHTNESS, SCREEN_AREA_MM2).items():
        all_usage.setdefault(k, []).extend(v)

usage_lut = {k: float(np.mean(v)) for k, v in all_usage.items()}

print("── Calibrated CPU usage fractions ──")
for k, v in sorted(usage_lut.items()):
    print(f"  {k:12s}: {v:.4f}")

# =====================================================================
# 4.  Plotting helpers
# =====================================================================

T = np.arange(SIM_DURATION_MIN)
TICK_HOURS = list(range(1, 37, 5))
TICK_VALS  = np.array(TICK_HOURS) * 60


def plot_comparison(P_base, P_variants: dict[str, np.ndarray],
                    title: str = "Parameter sweep"):
    """
    2-row figure: power on top, battery % on bottom.
    P_base is the reference; P_variants is {label: power_array}.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

    # base case
    bat_base = power_to_battery(P_base)
    ax1.plot(T, P_base, "k-", lw=1.5, label="base case")
    ax2.plot(T, bat_base, "k-", lw=1.5, label="base case")

    # variants
    for label, P in P_variants.items():
        bat = power_to_battery(P)
        ax1.plot(T, P, label=label, alpha=0.8)
        ax2.plot(T, bat, label=label, alpha=0.8)
        idx_empty = np.abs(bat).argmin()
        ax2.annotate(f"{idx_empty // 60}h",
                     (T[idx_empty], bat[idx_empty]),
                     textcoords="offset points", xytext=(5, 5), fontsize=8)

    for ax in (ax1, ax2):
        ax.set_xticks(TICK_VALS, TICK_HOURS)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7)
    ax1.set_ylabel("Power (mW)")
    ax2.set_ylabel("Battery (%)")
    ax2.set_xlabel("Hour of day")
    fig.suptitle(title)
    fig.tight_layout()
    return fig


# =====================================================================
# 5.  Run simulations  –  EDIT THIS SECTION TO SWEEP PARAMETERS
# =====================================================================

if __name__ == "__main__":
    import os
    os.makedirs("plots", exist_ok=True)

    for day_idx in range(len(EVENTS)):
        bl = baselines[day_idx]
        evs = EVENTS[day_idx]

        # ── Base case ────────────────────────────────────────────────
        P_base = simulate(evs, bl, usage_lut,
                          DEFAULT_BRIGHTNESS, SCREEN_AREA_MM2)

        # ── Sweep: brightness ────────────────────────────────────────
        variants = {}
        for bri in [0.1, 0.2, 0.5, 0.8, 1.0]:
            label = f"brightness={bri}"
            variants[label] = simulate(
                evs, bl, usage_lut, DEFAULT_BRIGHTNESS, SCREEN_AREA_MM2,
                brightness_override=bri,
            )
        fig = plot_comparison(P_base, variants, f"Day {day_idx+1} – Brightness sweep")
        fig.savefig(f"plots/day{day_idx+1}_brightness.png", dpi=150, bbox_inches="tight")

        # ── Sweep: greyscale ─────────────────────────────────────────
        variants = {}
        for gs in [50, 125, 200, 255]:
            label = f"greyscale={gs}"
            variants[label] = simulate(
                evs, bl, usage_lut, DEFAULT_BRIGHTNESS, SCREEN_AREA_MM2,
                greyscale_override=gs,
            )
        fig = plot_comparison(P_base, variants, f"Day {day_idx+1} – Greyscale sweep")
        fig.savefig(f"plots/day{day_idx+1}_greyscale.png", dpi=150, bbox_inches="tight")

        # ── Sweep: clock speed (affects all apps) ────────────────────
        variants = {}
        for clk in ["low", "med", "high"]:
            label = f"clock={clk}"
            variants[label] = simulate(
                evs, bl, usage_lut, DEFAULT_BRIGHTNESS, SCREEN_AREA_MM2,
                clock_override=clk,
            )
        fig = plot_comparison(P_base, variants, f"Day {day_idx+1} – Clock speed sweep")
        fig.savefig(f"plots/day{day_idx+1}_clock.png", dpi=150, bbox_inches="tight")

        # ── Sweep: network configuration ─────────────────────────────
        # Each entry rebuilds the *entire* idle baseline with a uniform
        # radio config, so you can compare "what if I was on wifi all day"
        NETWORK_CONFIGS = {
            "wifi only":                 dict(wifi="connected"),
            "5G only":                   dict(cell="5G"),
            "5G + wifi searching":       dict(cell="5G", wifi="searching"),
            "LTE only":                  dict(cell="LTE"),
            "wifi + BT":                 dict(wifi="connected", bt=True),
            "5G + wifi searching + BT":  dict(cell="5G", wifi="searching", bt=True),
        }
        variants = {}
        for label, kw in NETWORK_CONFIGS.items():
            uniform = IdleSchedule(SIM_DURATION_MIN)
            uniform.add(0, SIM_DURATION_MIN, **kw)
            bl_net = uniform.build_baseline()
            variants[label] = simulate(
                evs, bl_net, usage_lut, DEFAULT_BRIGHTNESS, SCREEN_AREA_MM2,
            )
        fig = plot_comparison(P_base, variants, f"Day {day_idx+1} – Network sweep")
        fig.savefig(f"plots/day{day_idx+1}_network.png", dpi=150, bbox_inches="tight")

    print("Plots saved to plots/")