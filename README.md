# Smartphone Battery Life Model

A physics-based power model that estimates smartphone battery drain from real usage data. Built for the MCM 2026 competition.

## What it does

The model computes per-minute power consumption (mW) for a phone over a simulated day using:

```
P(t) = P_display(t) + P_cpu(t) + P_idle(t) + P_stream(t) + P0
```

where each component is parameterized from real measurements. CPU usage fractions are back-solved from measured battery drain events (calibration), then used to run forward simulations.

`main.py` calibrates against two sample days of real usage data, then sweeps four parameters — brightness, greyscale, clock speed, and network configuration — producing comparison plots.

## Files

| File | Purpose |
|------|---------|
| `config.py` | All device-specific constants (battery, display, CPU profiles, radio powers) |
| `model.py` | Core physics: `p_display`, `p_cpu`, `p_idle`, `p_stream`, calibration, simulation |
| `main.py` | Sample events, calibration run, parameter sweep plots |

`deprecated/` contains earlier prototype scripts kept for reference.

## Quick start

```bash
pip install numpy matplotlib
python main.py
```

This prints calibrated CPU usage fractions and opens four sets of comparison plots (one per sweep × two sample days).

## Customizing

**Change the phone:** edit `config.py` — battery capacity, screen area, `ALPHA_DISP`, and CPU clock profiles are all there.

**Change the usage scenario:** edit the `EVENTS` list and `build_schedules()` in `main.py`. Each `AppEvent` takes:

```python
AppEvent(
    start,       # minute offset from midnight
    duration,    # minutes
    name,        # app name (used as key in usage_lut)
    bat_drain,   # fraction of full battery drained during this event
    display,     # "d" if screen is on, "" otherwise
    stream,      # network used for data: "wifi", "5G", "LTE", or ""
    greyscale,   # average screen grey level 0–255
    clock,       # CPU clock tier: "low", "med", or "high"
)
```

**Add a new parameter sweep:** call `simulate()` with any combination of `brightness_override`, `greyscale_override`, or `clock_override`, collect results in a dict, and pass to `plot_comparison()`.

## Model equation

Display power:

```
P_disp = I^2.2 × A × B × α_disp
```

where `I` is greyscale (0–255), `A` is screen area (mm²), `B` is brightness (0–1), and `α_disp = 552 × 10⁻⁹ mW/mm²`.

CPU power (linear in utilization per clock tier):

```
P_cpu = m × U + b
```

where `m` and `b` are from `CLOCK_PROFILES` and `U` is fractional core utilization (back-solved from measured drain during calibration).

Radio idle and streaming powers are lookup tables in `config.py` based on reported values for 5G/LTE/WiFi/Bluetooth.

## Known limitations

- CPU utilization is assumed constant within each app event (no intra-event variation).
- The baseline idle power is sampled at `ev.start` during calibration; events that straddle a radio-state transition will have a small calibration error.
- Battery is not clamped at 0% — the power trace continues past depletion in simulation.
