# TAP-RISC Software Simulator

A concept-level reference implementation of the TAP-RISC tamper-aware
edge platform. The simulator exists so that the algorithmic choices in
the DIR-V Grand Challenge proposal can be **exercised, debugged, and
demonstrated without an FPGA on the desk**.

This is **not** hardware emulation. The code models the *behavior* of
each subsystem (sensors, crypto, comms, state machine) faithfully
enough to validate the design, but the cycle-accurate Artix-7 + VEGA
AT1051 integration belongs to the next project phase.

## What's inside

| Module | Purpose |
|---|---|
| `sensors.py` | MPU6050, BMP280, capacitive PCB mesh behavioral models + 2-of-3 fusion voter |
| `security.py` | Secure boot (HMAC-SHA256), crypto-erase, SHA-256 chained audit log, AES-256-CTR helpers |
| `communication.py` | LoRa RA-02 alert link + BLE 5.2 pairing model |
| `device.py` | Top-level `TAPRISCDevice` state machine that wires everything together |
| `threat_scenarios.py` | Five end-to-end attack/defense walkthroughs |
| `tests/` | 19 unit tests covering sensors, fusion, secure boot, crypto-erase, audit log |

## Quick start

```bash
# Optional: install the cryptography library for real AES backend
pip install -r requirements.txt

# Run all threat scenarios end-to-end
python -m simulator.threat_scenarios

# Run the unit tests
python -m unittest discover simulator/tests -v
```

Expected output of the threat-scenario runner:

```
[PASS] Drill attack
[PASS] Voltage glitch only
[PASS] Single-sensor noise
[PASS] Firmware injection
[PASS] Log tamper
```

## Anatomy of a tamper event

When the 2-of-3 voter trips:

1. The current sensor decision is appended to the SHA-256 audit log as
   a `TAMPER` event.
2. `SecureKeyStore.crypto_erase()` performs a three-pass NIST SP 800-88
   purge on every long-term key.
3. An encrypted `TAMPER {device_id} t={time}` packet is broadcast over
   LoRa.
4. The device transitions to `TAMPER_LOCK` state and stays there until
   manual servicing.

You can trace the whole sequence in the printed audit log at the end
of each scenario.

## Scenario coverage

| # | Scenario | What it validates |
|---|---|---|
| 1 | Drill attack | All three sensors fire, fusion confirms, wipe + alert + lock |
| 2 | Voltage glitch only | Sensors *correctly* do NOT fire (RoT-level defense, out of software scope) |
| 3 | Single-sensor anomaly | One sensor going TAMPERED alone must NOT trigger the response |
| 4 | Firmware injection | Replacing the firmware with an unsigned blob → boot fails → device bricked |
| 5 | Log tampering | Editing any past audit-log entry invalidates the chain |

## Visualizing a scenario

The `scripts/visualize_scenario.py` script (in the repo root) renders
a 4-panel timeline of the drill-attack scenario:

```bash
python scripts/visualize_scenario.py
```

Output goes to `docs/images/scenario_timeline.png`.
