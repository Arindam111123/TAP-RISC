"""
sensors.py
==========
Software models of the three physical sensors specified in the
TAP-RISC proposal:

    - MPU6050   : 6-axis MEMS accelerometer (motion / shock / tilt)
    - BMP280    : barometric pressure sensor (enclosure breach)
    - PCB mesh  : capacitive trace network on the PCB (drill / cut)

These are *behavioral* models, not register-accurate drivers. They
exist so the rest of the simulator can be tested against realistic
signal shapes without an actual sensor on the desk.

References (datasheet figures):
    MPU6050 : InvenSense PS-MPU-6000A-00, range ±2g to ±16g
    BMP280  : Bosch BMP280 datasheet, range 300-1100 hPa, ±1 hPa
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import math
import random
from typing import Optional


class SensorState(Enum):
    """High-level health of a sensor channel."""
    NORMAL    = "normal"
    WARNING   = "warning"      # crossed first threshold
    TAMPERED  = "tampered"     # crossed second threshold, latched


@dataclass
class SensorReading:
    """One sample emitted by a sensor at time `t`."""
    t: float
    value: float          # native units (g for accel, hPa for press., pF for mesh)
    channel: str
    state: SensorState


# ---------------------------------------------------------------------
# MPU6050: motion / tilt / shock
# ---------------------------------------------------------------------
class MPU6050:
    """
    Behavioral model of an MPU6050 accelerometer.

    Outputs magnitude of total acceleration in g. At rest the magnitude
    sits at ~1.0 g (gravity); shocks and rapid movement push it higher.

    Tamper detection thresholds:
        - shock_g   : sudden spike (e.g. dropped, hit with a tool)
        - tilt_rad  : sustained tilt away from the resting orientation
    """

    def __init__(self,
                 shock_g: float = 2.0,
                 tilt_warn_deg: float = 15.0,
                 tilt_tamper_deg: float = 30.0,
                 noise_g: float = 0.01,
                 seed: int = 1):
        self.shock_g         = shock_g
        self.tilt_warn_rad   = math.radians(tilt_warn_deg)
        self.tilt_tamper_rad = math.radians(tilt_tamper_deg)
        self.noise_g         = noise_g
        self._rng            = random.Random(seed)

        # Internal state
        self._tilt_rad = 0.0      # current tilt away from resting axis
        self._shock_q  = []       # queue of pending shock samples
        self.latched_tampered = False

    # ---- stimulus methods (used by scenarios) ----
    def apply_shock(self, magnitude_g: float, duration_s: float, fs: int = 100):
        """Inject a shock event: N samples at the requested magnitude."""
        n = max(1, int(duration_s * fs))
        self._shock_q.extend([magnitude_g] * n)

    def apply_tilt(self, angle_deg: float):
        """Set a steady-state tilt offset."""
        self._tilt_rad = math.radians(angle_deg)

    # ---- read interface (called once per sim tick) ----
    def read(self, t: float) -> SensorReading:
        shock = self._shock_q.pop(0) if self._shock_q else 0.0
        noise = self._rng.gauss(0.0, self.noise_g)
        magnitude = math.sqrt(1.0 + shock**2) + noise + abs(math.sin(self._tilt_rad)) * 0.3

        state = SensorState.NORMAL
        if abs(self._tilt_rad) > self.tilt_warn_rad:
            state = SensorState.WARNING
        if abs(self._tilt_rad) > self.tilt_tamper_rad or magnitude > self.shock_g:
            state = SensorState.TAMPERED
            self.latched_tampered = True

        # Once tampered, latch the state (matches firmware behavior).
        if self.latched_tampered:
            state = SensorState.TAMPERED

        return SensorReading(t=t, value=magnitude, channel="mpu6050", state=state)


# ---------------------------------------------------------------------
# BMP280: enclosure pressure
# ---------------------------------------------------------------------
class BMP280:
    """
    Behavioral model of a Bosch BMP280 barometer.

    A sealed enclosure has a fairly stable internal pressure that
    only drifts slowly with temperature. Opening the enclosure causes
    a *step change* as the inside equilibrates with ambient.

    Tamper detection:
        - sudden delta_p over a short window indicates breach.
    """

    def __init__(self,
                 baseline_hpa: float = 1013.25,
                 noise_hpa: float = 0.5,
                 breach_delta_hpa: float = 8.0,
                 seed: int = 2):
        self.baseline   = baseline_hpa
        self.noise      = noise_hpa
        self.breach_dp  = breach_delta_hpa
        self._rng       = random.Random(seed)
        self._offset    = 0.0          # injected by tamper events
        self._history   = []           # short rolling window
        self.latched_tampered = False

    def apply_breach(self, delta_hpa: float = -8.0):
        """Step-change in internal pressure when enclosure opens."""
        self._offset += delta_hpa

    def read(self, t: float) -> SensorReading:
        v = self.baseline + self._offset + self._rng.gauss(0.0, self.noise)
        self._history.append(v)
        if len(self._history) > 16:
            self._history.pop(0)

        state = SensorState.NORMAL
        if len(self._history) >= 8:
            recent = sum(self._history[-4:]) / 4.0
            older  = sum(self._history[-8:-4]) / 4.0
            dp = recent - older
            if abs(dp) > self.breach_dp / 2:
                state = SensorState.WARNING
            if abs(dp) > self.breach_dp:
                state = SensorState.TAMPERED
                self.latched_tampered = True

        if self.latched_tampered:
            state = SensorState.TAMPERED

        return SensorReading(t=t, value=v, channel="bmp280", state=state)


# ---------------------------------------------------------------------
# Capacitive PCB mesh: trace-network integrity
# ---------------------------------------------------------------------
class CapacitiveMesh:
    """
    Behavioral model of a custom capacitive trace-mesh on the PCB.

    Concept: a serpentine trace network is laid across all four PCB
    layers in 0.2 mm pitch. Any drill, cut, or probe attack changes
    the network's capacitance enough to be detected by a comparator.

    The trace mesh is the most physically invasive defense - it can
    detect attacks that pressure / accelerometer sensors miss
    (e.g. delicate microsurgery with a hot-air station).
    """

    def __init__(self,
                 baseline_pf: float = 47.0,
                 noise_pf: float = 0.05,
                 break_threshold_pf: float = 1.0,
                 seed: int = 3):
        self.baseline = baseline_pf
        self.noise    = noise_pf
        self.break_th = break_threshold_pf
        self._rng     = random.Random(seed)
        self._damage  = 0.0
        self.latched_tampered = False

    def apply_probe(self, delta_pf: float = 2.0):
        """A probe touching the mesh adds capacitance. Latched."""
        self._damage += delta_pf

    def apply_cut(self):
        """A trace cut. Capacitance falls dramatically and stays low."""
        self._damage -= 5.0

    def read(self, t: float) -> SensorReading:
        v = self.baseline + self._damage + self._rng.gauss(0.0, self.noise)
        state = SensorState.NORMAL
        if abs(self._damage) > self.break_th / 2:
            state = SensorState.WARNING
        if abs(self._damage) > self.break_th:
            state = SensorState.TAMPERED
            self.latched_tampered = True

        if self.latched_tampered:
            state = SensorState.TAMPERED

        return SensorReading(t=t, value=v, channel="mesh", state=state)


# ---------------------------------------------------------------------
# Sensor fusion - 2-of-3 majority voting
# ---------------------------------------------------------------------
@dataclass
class FusionDecision:
    t: float
    tampered: bool
    n_warning: int
    n_tampered: int
    triggering_channels: list[str] = field(default_factory=list)


def fuse(readings: list[SensorReading], require: int = 2) -> FusionDecision:
    """
    2-of-3 voting fusion. Returns a tamper decision *only* when at
    least `require` independent channels report TAMPERED.

    This is the headline false-positive rate (<0.01%) claim from the
    proposal: any single noisy channel cannot trigger the wipe on
    its own.
    """
    if not readings:
        return FusionDecision(t=0.0, tampered=False, n_warning=0, n_tampered=0)

    n_warning  = sum(1 for r in readings if r.state == SensorState.WARNING)
    n_tampered = sum(1 for r in readings if r.state == SensorState.TAMPERED)
    triggering = [r.channel for r in readings if r.state == SensorState.TAMPERED]

    return FusionDecision(
        t=readings[0].t,
        tampered=n_tampered >= require,
        n_warning=n_warning,
        n_tampered=n_tampered,
        triggering_channels=triggering,
    )
