"""
Device-specific calibration parameters and physical constants for the
smartphone power model (Equation 15 in the paper).

Edit this file to match your phone / measurement campaign.
"""

# ── Battery ──────────────────────────────────────────────────────────
MAX_BATTERY_MWH = 13_819  # mWh

# ── Display ──────────────────────────────────────────────────────────
SCREEN_AREA_MM2 = 10_568.16          # mm²
ALPHA_DISP = 552e-9                  # mW / mm²  (display power parameter)
DEFAULT_BRIGHTNESS = 0.5             # 0–1
DEFAULT_GREYSCALE = 125              # 0–255

# ── Chip / CPU ───────────────────────────────────────────────────────
NUM_CORES = 6

# (baseline_mW, slope_mW) per clock tier
# slope is defined so P_cpu = slope * U + baseline
CLOCK_PROFILES = {
    "high": lambda N: (125, 1000 * N - 125),
    "med":  lambda N: (100,  500 * N - 100),
    "low":  lambda N: ( 75,  200 * N -  75),
}

# ── Idle / Radio ─────────────────────────────────────────────────────
P0 = 20.0  # constant base power (mW)

CELL_POWER = {"5G": 260, "LTE": 160, "": 0, None: 0}
WIFI_POWER = {"searching": 72, "connected": 32, "": 0, None: 0}
BT_POWER   = 88  # mW when active

# ── Streaming ────────────────────────────────────────────────────────
STREAM_POWER = {"wifi": 566, "LTE": 749, "5G": 859, "": 0, None: 0}

# ── Simulation ───────────────────────────────────────────────────────
SIM_DURATION_MIN = 40 * 60  # total minutes to simulate