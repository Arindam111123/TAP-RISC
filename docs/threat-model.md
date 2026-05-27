# Threat Model

This document enumerates the adversary capabilities TAP-RISC is
designed to resist, what we explicitly do *not* protect against, and
how each defense maps to the layered architecture.

## Adversary capabilities

We assume an adversary who can:

- **Physically possess** a deployed TAP-RISC device (worst case for
  embedded security).
- **Open the enclosure** with hand tools.
- **Probe the PCB** with multimeters, logic analyzers, or hot-air
  rework stations.
- **Flash arbitrary firmware** to the device's storage.
- **Sniff over-the-air** LoRa and BLE traffic at will.
- **Replay captured packets** at the radio interface.

We *do not* assume the adversary can:

- Extract the Artix-7 OTP fuses non-destructively (an OEM-level capability,
  out of scope).
- Defeat the AES-256 cipher mathematically.
- Coerce the manufacturer to sign rogue firmware (this is supply-chain
  risk, addressed by indigenous fabrication policy, not by the chip).

## Attack scenarios and defenses

The table below maps each attack to (a) which layer of TAP-RISC catches
it, (b) which test scenario in `simulator/threat_scenarios.py`
demonstrates the defense.

| # | Attack | Layer that catches it | Demonstrated by |
|---|---|---|---|
| 1 | Drill / saw the enclosure | Detection (mesh + barometer + accel) → Response | `scenario_drill_attack` |
| 2 | Voltage glitch the CPU | RoT-level (out of software-sim scope) | `scenario_voltage_glitch_only` shows sensor layer correctly does NOT fire |
| 3 | Flash unsigned firmware | Secure boot (HMAC-SHA256) | `scenario_firmware_injection` |
| 4 | Edit audit log post-hoc | Chained SHA-256 hash | `scenario_log_tamper` |
| 5 | Single-sensor false positive | Fusion (2-of-3 voter) | `scenario_single_sensor_noise` |
| 6 | LoRa packet sniff | AES-128-CCM payload encryption | (architecture; no scenario needed) |
| 7 | LoRa replay | Per-packet nonce, sequence numbers | (architecture) |
| 8 | Brute force AES key | 2^256 keyspace | (architecture) |
| 9 | JTAG / SWD debug probe | OTP-fuse blown after manufacture | (architecture) |
| 10 | Cold boot / DRAM remanence | Keys live in SRAM tied to power; tamper triggers wipe | (architecture) |

## Defense-in-depth flow

When a determined adversary breaks one layer, the next layer should
still hold. The visual flow:

```
                 +-------------------------+
  Adversary -->  | 1. Physical enclosure   |   IP67 case + resin
                 +-----------+-------------+
                             |
                       (drilled through)
                             v
                 +-------------------------+
                 | 2. Tamper sensors       |   accel + baro + mesh
                 +-----------+-------------+
                             |
                       (fusion votes)
                             v
                 +-------------------------+
                 | 3. Fusion 2-of-3        |   < 0.01% false positive
                 +-----------+-------------+
                             |
                     (tamper confirmed)
                             v
                 +-------------------------+
                 | 4. Response: WIPE       |   < 500 ms AES-256 erase
                 |                  ALERT  |   LoRa encrypted broadcast
                 |                  LOG    |   SHA-256 chained entry
                 +-----------+-------------+
                             |
                             v
                 +-------------------------+
                 | 5. Tamper-lock state    |   device inert until
                 |                         |   manual servicing
                 +-------------------------+
```

The state machine in `simulator/device.py::TAPRISCDevice` is the
executable form of this flow.

## Residual risks

Honest disclosure of what TAP-RISC does *not* claim to solve:

1. **Side-channel attacks on the AES engine** (DPA, EM emanations).
   The proposal mentions side-channel resistance as a goal but does
   not prescribe specific countermeasures yet. Production silicon
   would need masking + hiding strategies on the AES core.

2. **Optical fault injection** through the silicon die. Requires
   decapsulation + a femtosecond laser; out of the realistic threat
   profile for the deployment scenarios (border posts, smart grids,
   ATMs).

3. **Supply-chain attacks** on the AT1051 mask set. Mitigated by
   using a vendor (C-DAC) under direct government oversight.

4. **Insider attacks** with valid signing keys. Solvable only by
   process (separation of duties, HSM-protected signing) not by
   firmware. TAP-RISC keeps the secure-boot chain honest *given*
   that the signing infrastructure is honest.

5. **Denial of service via repeated tamper triggers**. An adversary
   could intentionally fail tamper sensors to force a wipe on
   deployed devices. Mitigation is operational (lock down access)
   rather than technical.
