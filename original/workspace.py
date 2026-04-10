import numpy as np
import matplotlib.pyplot as plt

# --- constants / profiles ---
t = np.arange(1440)  # minutes in a day

idle = 103.2

display = {
    "idle":  np.linspace(38,   257.3, 101),
    "call":  np.linspace(16.7, 112.9, 101),
    "web":   np.linspace(164.2, 1111.7, 101),
    "video": np.linspace(15.1, 102.0, 101),
}

call = 1135.4

email = {"cell": 690.7, "wifi": 505.6}
web   = {"cell": 500.0, "wifi": 430.4}
network = {"cell": 929.7, "wifi": 1053.7}

video = 558.8
audio = 419.0

# --- knobs ---
service = "wifi"
brightness = 100  # 0..100

# Precompute display contributions at this brightness
disp_idle  = float(display["idle"][brightness])
disp_call  = float(display["call"][brightness])
disp_web   = float(display["web"][brightness])
disp_video = float(display["video"][brightness])

# Base power for whole day
P = np.full(t.shape, idle + disp_idle, dtype=float)

# --- schedule as events: (start_min, end_min, extra_power) ---
events = [
    # Check emails and make a call at 8:00
    (480, 510, email[service]),
    (510, 525, call + disp_call),
    (525, 540, email[service]),

    # Play a game on your break at 12:00
    (720, 780, network[service] + video + disp_video + audio),

    # Watch videos online when you get home at 5:00
    (1020, 1180, web[service] + disp_web + video + disp_video + audio),
]

for start, end, extra in events:
    P[start:end] += extra

E_cuns=np.cumsum(P)/60000
battery_Energy = 13.7 #watt hours

plt.subplot(1, 2, 1)
plt.plot(t, P)
plt.subplot(1, 2, 2)
plt.plot(t, -E_cuns+battery_Energy)
plt.plot(t, [0]*len(t))
plt.show()
