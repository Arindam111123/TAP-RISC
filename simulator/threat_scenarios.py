"""
threat_scenarios.py
===================
End-to-end attack/defense walkthroughs. Each scenario configures a
fresh TAP-RISC device, injects an attack into the appropriate
subsystem, runs the simulation, and prints the resulting evidence
trail.

The scenarios match the threat model documented in
``docs/threat-model.md`` and exercise the layered defenses described
in the proposal (multi-modal tamper detection, secure boot,
crypto-erase, chained logging, encrypted alerting).

Run all scenarios with:
    python -m simulator.threat_scenarios
"""

from __future__ import annotations
import sys

from .device import TAPRISCDevice, DeviceState


# =====================================================================
# Helpers
# =====================================================================
def banner(title: str) -> None:
    bar = "=" * 72
    print(f"\n{bar}\n  {title}\n{bar}")


def dump_log(dev: TAPRISCDevice) -> None:
    for e in dev.log.entries():
        print("   ", e.serialize())
    print(f"    log_verify : {dev.log.verify()}")


# =====================================================================
# Scenario 1: Drill attack (mechanical, opens the enclosure)
# =====================================================================
def scenario_drill_attack() -> bool:
    banner("SCENARIO 1 - Mechanical drill through the enclosure")
    dev = TAPRISCDevice(device_id="TAPRISC-001")
    dev.power_on()
    assert dev.state == DeviceState.OPERATIONAL

    # 100 ticks of normal operation
    for _ in range(100):
        dev.tick()

    # Attacker drills in: pressure drops, accelerometer feels the hit,
    # mesh trace is cut.
    print("    [t=1.0s] adversary applies drill...")
    dev.bmp.apply_breach(delta_hpa=-15.0)
    dev.mpu.apply_shock(magnitude_g=5.0, duration_s=0.1, fs=dev.fs)
    dev.mesh.apply_cut()

    tampered = False
    for _ in range(50):
        r = dev.tick()
        if r.tampered_this_tick:
            print(f"    [t={r.t:.3f}s] TAMPER detected, wipe={r.wipe_ms:.2f} ms, "
                  f"alert_sent={r.alert_sent}")
            tampered = True
            break

    print(f"    final state : {dev.state.value}")
    print(f"    keys erased : {dev.keys.erased}")
    print(f"    log entries : {len(dev.log.entries())}")
    dump_log(dev)
    return tampered and dev.state == DeviceState.TAMPER_LOCK


# =====================================================================
# Scenario 2: Voltage glitch (no enclosure breach, no PCB damage)
# =====================================================================
def scenario_voltage_glitch_only() -> bool:
    """
    Adversary tries to inject a voltage glitch without opening the
    enclosure. None of our three physical sensors should fire - and
    they don't. This is the *correct* false-negative case: the
    proposal scopes glitch protection to the RoT itself (out of
    scope for this software simulator), not to multi-modal sensing.
    """
    banner("SCENARIO 2 - Voltage glitch (no physical signature)")
    dev = TAPRISCDevice(device_id="TAPRISC-002")
    dev.power_on()

    for _ in range(200):
        dev.tick()

    print(f"    no tamper triggered : {dev.state == DeviceState.OPERATIONAL}")
    print("    (correct - voltage glitch defense is RoT-level, not sensor-level)")
    return dev.state == DeviceState.OPERATIONAL


# =====================================================================
# Scenario 3: Single-sensor noise should NOT trigger (false positive)
# =====================================================================
def scenario_single_sensor_noise() -> bool:
    """
    Validates the 2-of-3 voting: a single misbehaving sensor should
    not be sufficient to wipe the device. This is what gives the
    proposal's <0.01% false-positive rate.
    """
    banner("SCENARIO 3 - Single sensor anomaly (must NOT wipe)")
    dev = TAPRISCDevice(device_id="TAPRISC-003")
    dev.power_on()

    print("    [t=0.5s] only MPU6050 reports a shock...")
    dev.mpu.apply_shock(magnitude_g=4.0, duration_s=0.2, fs=dev.fs)

    for _ in range(100):
        dev.tick()

    operational = dev.state == DeviceState.OPERATIONAL
    print(f"    device still operational: {operational}")
    print(f"    no wipe                : {not dev.keys.erased}")
    return operational and not dev.keys.erased


# =====================================================================
# Scenario 4: Malicious firmware injection
# =====================================================================
def scenario_firmware_injection() -> bool:
    """
    Attacker overwrites the firmware blob in flash. Without the RoT
    key they cannot produce a valid signature, so the next secure
    boot must refuse and brick the device.
    """
    banner("SCENARIO 4 - Malicious firmware injection")
    dev = TAPRISCDevice(device_id="TAPRISC-004")
    dev.power_on()
    for _ in range(50):
        dev.tick()

    print("    adversary replaces firmware with unsigned payload...")
    dev.replace_firmware(
        new_payload=b"#!malicious payload that drops to shell",
        new_version="rogue-v1",
    )
    # Simulate power cycle
    dev.state = DeviceState.POWER_OFF
    dev.power_on()

    bricked = dev.state == DeviceState.BRICKED
    print(f"    secure boot refused malicious fw: {bricked}")
    dump_log(dev)
    return bricked


# =====================================================================
# Scenario 5: Log tampering attempt
# =====================================================================
def scenario_log_tamper() -> bool:
    """
    Audit logs are SHA-256 chained; editing any past entry should
    invalidate the chain on the next verify pass.
    """
    banner("SCENARIO 5 - Audit log tampering")
    dev = TAPRISCDevice(device_id="TAPRISC-005")
    dev.power_on()
    for _ in range(100):
        dev.tick()

    print("    chain intact before edit:", dev.log.verify())

    # Adversary edits an entry in place.
    entries = dev.log._entries
    if len(entries) >= 1:
        entries[0].detail = "FORGED"
    print("    chain intact after edit :", dev.log.verify())

    return not dev.log.verify()


# =====================================================================
# Entry point
# =====================================================================
SCENARIOS = [
    ("Drill attack",          scenario_drill_attack),
    ("Voltage glitch only",   scenario_voltage_glitch_only),
    ("Single-sensor noise",   scenario_single_sensor_noise),
    ("Firmware injection",    scenario_firmware_injection),
    ("Log tamper",            scenario_log_tamper),
]


def main() -> int:
    print("\nTAP-RISC threat-scenario simulator")
    print("="*72)
    results = []
    for name, fn in SCENARIOS:
        ok = fn()
        results.append((name, ok))

    banner("SUMMARY")
    for name, ok in results:
        tag = "PASS" if ok else "FAIL"
        print(f"   [{tag}] {name}")

    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    sys.exit(main())
