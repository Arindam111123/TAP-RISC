"""
device.py
=========
Top-level state machine for a single TAP-RISC node.

Composes the sensor models, security primitives, and communication
channels into one object whose behavior matches the proposal:

    1. Power on -> RoT verifies firmware signature (secure boot).
    2. Normal operation: poll sensors every tick, run 2-of-3 fusion.
    3. On tamper trigger:
        a. Append "TAMPER" event to chained log.
        b. Crypto-erase the key store.
        c. Broadcast encrypted LoRa alert.
        d. Halt - device remains inert until manual servicing.
    4. Boot loop refuses to re-enter normal operation after a wipe.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import secrets

from .sensors import MPU6050, BMP280, CapacitiveMesh, fuse
from .security import (
    RootOfTrust, FirmwareImage, SecureBootError,
    SecureKeyStore, TamperLog,
)
from .communication import LoRaLink


class DeviceState(Enum):
    POWER_OFF    = "power_off"
    SECURE_BOOT  = "secure_boot"
    OPERATIONAL  = "operational"
    TAMPER_LOCK  = "tamper_lock"
    BRICKED      = "bricked"     # signature failed at boot


@dataclass
class TickResult:
    """What happened during one simulator tick."""
    t: float
    state: DeviceState
    tampered_this_tick: bool = False
    fusion_votes: int = 0
    alert_sent: bool = False
    wipe_ms: float = 0.0


class TAPRISCDevice:
    """
    One TAP-RISC instance. Owns its sensors, root of trust, firmware
    image, key store, log, and LoRa radio.
    """

    def __init__(self,
                 fs: int = 100,
                 device_id: str = "TAPRISC-001"):
        # Boot infrastructure
        self.fs        = fs                              # sensor poll rate
        self.device_id = device_id
        self.rot       = RootOfTrust()
        self.keys      = SecureKeyStore()
        self.log       = TamperLog()
        # Communication link key derived from RoT in real fw; here we
        # just generate one for the simulation.
        self.lora      = LoRaLink(link_key=secrets.token_bytes(32))

        # Sensors
        self.mpu = MPU6050()
        self.bmp = BMP280()
        self.mesh = CapacitiveMesh()

        # Firmware: factory signs a payload with our RoT; in real life
        # this would be done in a separate signing environment.
        self.firmware = self.rot.sign_firmware(
            payload=b"<TAP-RISC firmware v0.1.0 minimal payload>",
            version="v0.1.0",
        )

        self.state = DeviceState.POWER_OFF
        self.t     = 0.0

    # ------------------------------------------------------------------
    # Boot sequence
    # ------------------------------------------------------------------
    def power_on(self) -> None:
        self.log.append("POWER_ON", self.device_id, t=self.t)
        self.state = DeviceState.SECURE_BOOT

        try:
            self.rot.boot(self.firmware)
        except SecureBootError as e:
            self.log.append("BOOT_FAIL", str(e), t=self.t)
            self.state = DeviceState.BRICKED
            return

        self.log.append("BOOT_OK", f"fw={self.firmware.version}", t=self.t)
        self.state = DeviceState.OPERATIONAL

    # ------------------------------------------------------------------
    # Replace-firmware attack helper (used by threat scenarios)
    # ------------------------------------------------------------------
    def replace_firmware(self, new_payload: bytes, new_version: str = "rogue") -> None:
        """
        Simulates an attacker overwriting the firmware blob in flash
        without having the root-of-trust key. The next boot will fail.
        """
        self.firmware = FirmwareImage(
            payload=new_payload,
            signature=secrets.token_bytes(32),  # garbage sig
            version=new_version,
        )

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def tick(self) -> TickResult:
        """Advance one sample period (1/fs seconds)."""
        result = TickResult(t=self.t, state=self.state)
        dt = 1.0 / self.fs

        if self.state in (DeviceState.POWER_OFF,
                          DeviceState.BRICKED,
                          DeviceState.TAMPER_LOCK):
            self.t += dt
            return result

        # Poll all three sensors and fuse.
        readings = [
            self.mpu.read(self.t),
            self.bmp.read(self.t),
            self.mesh.read(self.t),
        ]
        decision = fuse(readings, require=2)
        result.fusion_votes = decision.n_tampered

        if decision.tampered:
            self._handle_tamper(decision.triggering_channels)
            result.tampered_this_tick = True
            result.alert_sent = True
            result.wipe_ms = self.keys.erase_duration_ms
            result.state = self.state

        self.t += dt
        return result

    # ------------------------------------------------------------------
    # Tamper response
    # ------------------------------------------------------------------
    def _handle_tamper(self, channels: list[str]) -> None:
        # 1. Audit log entry FIRST so the evidence survives even if
        #    wipe takes priority over comms.
        self.log.append("TAMPER",
                        detail=f"channels={'+'.join(channels)}",
                        t=self.t)

        # 2. Wipe before alert: secrets must die before any attempt to
        #    transmit them (defense in depth).
        wipe_ms = self.keys.crypto_erase()
        self.log.append("WIPE",
                        detail=f"duration_ms={wipe_ms:.1f}",
                        t=self.t)

        # 3. Encrypted LoRa alert. Payload is minimal - identifier
        #    plus timestamp, not the key material itself (which no
        #    longer exists).
        payload = f"TAMPER {self.device_id} t={self.t:.3f}".encode()
        pkt = self.lora.send_alert(payload, t=self.t)
        self.log.append(
            "ALERT_TX",
            detail=f"channel=lora received={pkt.received}",
            t=self.t,
        )

        # 4. Halt. Device requires manual servicing to come back.
        self.state = DeviceState.TAMPER_LOCK

    # ------------------------------------------------------------------
    # Diagnostic helpers
    # ------------------------------------------------------------------
    def status_dump(self) -> str:
        return (
            f"[{self.device_id}] state={self.state.value} "
            f"t={self.t:.3f}s log_entries={len(self.log.entries())} "
            f"keys_erased={self.keys.erased}"
        )
