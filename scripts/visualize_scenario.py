"""
visualize_scenario.py
=====================
Generates a 4-panel timeline plot of a drill-attack scenario:
sensor readings, fusion votes, device state, and tamper events.

Run from the repo root:
    python scripts/visualize_scenario.py

Outputs to docs/images/scenario_timeline.png
"""

from __future__ import annotations
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Make the package importable.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from simulator.device import TAPRISCDevice, DeviceState
from simulator.sensors import SensorState


OUT = ROOT / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True)


def run_scenario():
    dev = TAPRISCDevice(device_id="TAPRISC-DEMO", fs=100)
    dev.power_on()

    rows = []   # list of (t, accel, press, mesh, votes, state)

    def record(t):
        rows.append((
            t,
            dev.mpu.read(t).value,
            dev.bmp.read(t).value,
            dev.mesh.read(t).value,
            dev.state.value,
        ))

    # 1 s normal operation
    for i in range(100):
        t = i / 100
        dev.tick()
        rows.append((t,
                     dev.mpu._shock_q[0] + 1.0 if dev.mpu._shock_q else 1.0,
                     dev.bmp.baseline + dev.bmp._offset,
                     dev.mesh.baseline + dev.mesh._damage,
                     dev.state.value))

    # Attack at t=1.0 s
    dev.bmp.apply_breach(delta_hpa=-15.0)
    dev.mpu.apply_shock(magnitude_g=5.0, duration_s=0.1, fs=100)
    dev.mesh.apply_cut()

    # 1 s of response
    for i in range(100, 200):
        t = i / 100
        dev.tick()
        rows.append((t,
                     dev.mpu._shock_q[0] + 1.0 if dev.mpu._shock_q else 1.0,
                     dev.bmp.baseline + dev.bmp._offset,
                     dev.mesh.baseline + dev.mesh._damage,
                     dev.state.value))

    return dev, rows


def plot(dev, rows):
    t = np.array([r[0] for r in rows])
    accel = np.array([r[1] for r in rows])
    press = np.array([r[2] for r in rows])
    mesh  = np.array([r[3] for r in rows])
    state = [r[4] for r in rows]

    fig, axes = plt.subplots(4, 1, figsize=(11, 8.5), sharex=True)
    fig.suptitle("TAP-RISC drill-attack scenario timeline",
                 fontweight="bold")

    axes[0].plot(t, accel, color="#1f77b4", linewidth=1.4)
    axes[0].axhline(2.0, color="#d62728", linestyle="--",
                    label="shock threshold (2g)")
    axes[0].set_ylabel("MPU6050 |a| (g)")
    axes[0].grid(alpha=0.3); axes[0].legend(loc="upper left")
    axes[0].set_title("Layer 1: motion / shock sensor")

    axes[1].plot(t, press, color="#2ca02c", linewidth=1.4)
    axes[1].axhline(1013.25, color="#888", linestyle=":",
                    label="ambient (1013 hPa)")
    axes[1].set_ylabel("BMP280 (hPa)")
    axes[1].grid(alpha=0.3); axes[1].legend(loc="upper left")
    axes[1].set_title("Layer 2: enclosure pressure sensor")

    axes[2].plot(t, mesh, color="#9467bd", linewidth=1.4)
    axes[2].axhline(47.0, color="#888", linestyle=":",
                    label="intact mesh (47 pF)")
    axes[2].set_ylabel("Mesh (pF)")
    axes[2].grid(alpha=0.3); axes[2].legend(loc="upper left")
    axes[2].set_title("Layer 3: capacitive PCB mesh")

    # State strip
    state_map = {"power_off": 0, "secure_boot": 1, "operational": 2,
                 "tamper_lock": 3, "bricked": 4}
    state_vals = [state_map.get(s, -1) for s in state]
    axes[3].step(t, state_vals, where="post", color="#d62728", linewidth=1.6)
    axes[3].set_yticks(list(state_map.values()))
    axes[3].set_yticklabels(list(state_map.keys()))
    axes[3].grid(alpha=0.3)
    axes[3].set_title("Device state machine")
    axes[3].set_xlabel("time (s)")

    # Mark the attack instant on every panel
    for ax in axes:
        ax.axvline(1.0, color="#d62728", linewidth=0.8, alpha=0.4)

    plt.tight_layout()
    out_path = OUT / "scenario_timeline.png"
    plt.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def main():
    dev, rows = run_scenario()
    path = plot(dev, rows)
    print(f"Wrote {path}")
    print(f"Device ended in state: {dev.state.value}")
    print(f"Audit log entries    : {len(dev.log.entries())}")
    print(f"Keys erased          : {dev.keys.erased}")


if __name__ == "__main__":
    main()
