# System Architecture

This document expands on the block diagram with the rationale behind
each subsystem choice and how the pieces interact at runtime.

![Architecture](images/architecture.png)

## 1. Compute core: VEGA AT1051 + Artix-7 100T

**Why VEGA AT1051?**
The AT1051 is C-DAC's indigenous RISC-V CPU IP. It implements the
RV32IMA ISA on a 5-stage in-order pipeline with branch prediction
and an optional MMU. For TAP-RISC we use:

- **In-order pipeline** so we get predictable cycle-accurate timing -
  important when the watchdog needs to fire within a known budget.
- **RV32IMA** for the integer + multiply + atomics extensions;
  no FPU is needed for any of the security primitives we run.
- **C-DAC's silicon roadmap** so the project stays aligned with the
  MeitY/DIR-V indigenous-IP mandate.

**Why pair it with the Artix-7?**
The Artix-7 100T (Xilinx 7-series, ~101k logic cells) brings two things
the AT1051 alone can't:

1. **Hardware AES-256 / SHA-256 IP blocks** - we can clock crypto
   primitives at fabric speed instead of paying the multi-thousand-cycle
   software cost.
2. **Custom security peripherals** - the capacitive-mesh comparator,
   tamper interrupt aggregator, and OTP key fuses are all FPGA logic.
   This is where the "Tamper-Aware" piece of TAP-RISC actually lives.

The AT1051 sits inside the Artix as a soft core; the FPGA fabric
around it implements the security primitives that wrap normal compute.

## 2. Sensor layer (multi-modal, 2-of-3 voting)

Three physically independent sensors give us **defense in depth** plus
a way to keep false-positive rates extremely low.

| Sensor | Detects | Bypass mechanism |
|---|---|---|
| MPU6050 (6-axis MEMS accelerometer) | Shock, drop, tilt | Adversary must keep the device perfectly still |
| BMP280 (barometer) | Enclosure breach (pressure equalization) | Adversary needs a pressure-equalized airlock |
| Capacitive PCB mesh | Drill / cut / hot-air probe attacks | Adversary must defeat the trace network without changing its capacitance |

Each sensor has its own threshold and latches into a `TAMPERED` state
the moment it fires; the fusion voter requires at least **two of three**
channels to be in `TAMPERED` before the response chain triggers.

That 2-of-3 rule is the headline `<0.01%` false-positive figure from
the proposal: a single noisy sensor (e.g. EMI hit on the mesh, or
a transport shock on the accel) can't trigger a wipe on its own.

## 3. Security primitives

### Secure Boot
Implemented as HMAC-SHA256 verification with a key burned into the
Artix-7 OTP fuses at manufacture. Firmware that wasn't signed by the
authorized key simply doesn't run.

### Crypto-Erase (`<500 ms` budget)
Key store lives in internal SRAM (no flash → no wear leveling to defeat
the wipe). On tamper detection the firmware does a three-pass
overwrite (NIST SP 800-88 "purge" pattern) on:

- AES-256 data-at-rest key
- ECDSA signing private key
- Audit-log HMAC seed

The 500 ms figure is the platform budget, not a hard requirement -
the actual SRAM zeroize on a 100 MHz fabric runs in microseconds.

### Chained Audit Log
Each log entry stores `SHA-256(seq | t | event | detail | prev_hash)`.
Tampering with any past entry invalidates the hash chain from that
point forward, so service personnel can detect both deletion *and*
silent edits after the fact.

## 4. Communication channels

| Channel | Use | Encryption |
|---|---|---|
| LoRa RA-02 (433/868 MHz) | Long-range tamper alerts (~15 km LoS) | AES-128-CCM (LoRaWAN std.) |
| BLE 5.2 | Short-range maintenance pairing | LE Secure Connections + FIDO2 passkey |

Note: the LoRa alert payload is intentionally minimal - device ID and
timestamp only. We don't transmit *what* was tampered (which channels
fired) over the open air, because that information could help an
adversary calibrate their next attempt. Forensic detail lives only
in the chained audit log, readable via authenticated BLE.

## 5. RTOS: Zephyr

Zephyr is the obvious choice for a RISC-V security project:

- Permissively licensed, modular - easy to publish the entire image
  under an open license.
- First-class RISC-V support including RV32IMA on Artix-7 soft cores.
- Built-in mbed TLS / LibreSSL integration for crypto primitives.
- Real-time scheduler with sub-millisecond IRQ latency - matters for
  the watchdog and tamper interrupts.

## 6. Power and enclosure

- **IP67-rated case** (dust-tight, withstands brief immersion).
- **Conformal coating** on the PCB to resist humidity and casual probe
  attacks.
- **Anti-tamper resin** filling sensitive areas (around the FPGA and
  key OTP) so a determined attacker can't reach the silicon without
  breaking the capacitive mesh.
- **USB or battery powered** - the device is portable.
- **External hardware watchdog** so a hung CPU is restarted by the
  fabric, not by itself (defense against fault injection that disables
  the software watchdog).
