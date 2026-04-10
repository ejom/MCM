"""
Core power-model functions corresponding to Equation 15.

P(t) = α_disp * I^2.2 * A * B * f(t)
      + α_freq(t) * U_chip(t) + β_freq(t)
      + S_net(t) + P_net(t) + P_BT(t) + P_search(t) + P0
"""

from __future__ import annotations
import numpy as np
from config import (
    ALPHA_DISP, NUM_CORES, CLOCK_PROFILES,
    CELL_POWER, WIFI_POWER, BT_POWER, STREAM_POWER, P0,
    MAX_BATTERY_MWH,
)


# ── Component helpers ────────────────────────────────────────────────

def p_display(greyscale: float, area_mm2: float, brightness: float) -> float:
    """Display power (mW)."""
    return greyscale ** 2.2 * area_mm2 * brightness * ALPHA_DISP


def p_cpu(usage: float, clock: str = "med", n_cores: int = NUM_CORES) -> float:
    """CPU power (mW) given fractional usage 0–1."""
    b, m = CLOCK_PROFILES[clock](n_cores)
    return m * usage + b


def usage_from_power(power_mw: float, clock: str = "med", n_cores: int = NUM_CORES) -> float:
    """Invert p_cpu to get usage fraction."""
    b, m = CLOCK_PROFILES[clock](n_cores)
    return (power_mw - b) / m


def p_idle(cell: str = "", wifi: str = "", bt: bool = False) -> float:
    """Sum of radio idle powers."""
    return CELL_POWER.get(cell, 0) + WIFI_POWER.get(wifi, 0) + (BT_POWER if bt else 0)


def p_stream(net: str = "") -> float:
    return STREAM_POWER.get(net, 0)


# ── Event / schedule types ───────────────────────────────────────────

class AppEvent:
    """One stretch of app usage."""
    __slots__ = (
        "start", "duration", "name", "bat_drain",
        "display", "stream", "greyscale", "clock",
    )

    def __init__(self, start, duration, name, bat_drain,
                 display="", stream="", greyscale=125, clock="med"):
        self.start = start          # minute offset
        self.duration = duration    # minutes
        self.name = name
        self.bat_drain = bat_drain  # fraction of full battery
        self.display = display      # 'd' or ''
        self.stream = stream        # 'wifi'/'5G'/'LTE'/''
        self.greyscale = greyscale
        self.clock = clock


class IdleSchedule:
    """Piecewise idle-radio schedule as list of (start, end, kwargs_for_p_idle)."""

    def __init__(self, duration: int):
        self.duration = duration
        self.segments: list[tuple[int, int, dict]] = []

    def add(self, start: int, end: int, *, cell="", wifi="", bt=False):
        self.segments.append((start, end, dict(cell=cell, wifi=wifi, bt=bt)))
        return self

    def build_baseline(self) -> np.ndarray:
        """Return minute-resolution baseline power array (idle + P0)."""
        P = np.full(self.duration, P0)
        for s, e, kw in self.segments:
            P[s:e] += p_idle(**kw)
        return P


# ── Calibration pass ─────────────────────────────────────────────────

def calibrate_usage(events: list[AppEvent], baseline: np.ndarray,
                    brightness: float, area_mm2: float) -> dict[str, list[float]]:
    """
    Back-solve CPU usage for each event from its measured battery drain.
    Returns {app_name: [usage_fraction, ...]}.
    """
    usage: dict[str, list[float]] = {}
    for ev in events:
        energy = ev.bat_drain * MAX_BATTERY_MWH
        drain = energy / (ev.duration / 60)          # mW
        drain -= baseline[ev.start]                   # subtract idle
        if ev.display:
            drain -= p_display(ev.greyscale, area_mm2, brightness)
        if ev.stream:
            drain -= p_stream(ev.stream)
        u = usage_from_power(drain, ev.clock)
        usage.setdefault(ev.name, []).append(u)
    return usage


# ── Forward simulation ───────────────────────────────────────────────

def simulate(events: list[AppEvent], baseline: np.ndarray,
             usage_lut: dict[str, float],
             brightness: float, area_mm2: float,
             # optional per-simulation overrides
             brightness_override: float | None = None,
             greyscale_override: float | None = None,
             clock_override: str | None = None,
             ) -> np.ndarray:
    """
    Run the forward model.  Override params replace the per-event value
    for *all* events so you can sweep a single variable.
    """
    P = baseline.copy()
    bri = brightness_override if brightness_override is not None else brightness

    for ev in events:
        gs = greyscale_override if greyscale_override is not None else ev.greyscale
        clk = clock_override if clock_override is not None else ev.clock
        pw = 0.0
        if ev.display:
            pw += p_display(gs, area_mm2, bri)
        if ev.stream:
            pw += p_stream(ev.stream)
        pw += p_cpu(usage_lut.get(ev.name, 0.0), clk)
        P[ev.start: ev.start + ev.duration] += pw
    return P


def power_to_battery(P: np.ndarray, max_bat: float = MAX_BATTERY_MWH):
    """Convert minute-resolution power to remaining battery (fraction)."""
    E = max_bat - np.cumsum(P) / 60
    return E / max_bat