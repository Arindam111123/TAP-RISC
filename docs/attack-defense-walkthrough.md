# Attack & Defense Walkthrough

Step-by-step traces of how TAP-RISC defends against representative
attack patterns. Each example pairs the attacker action with the
specific layer of TAP-RISC that catches it. The corresponding
threat-scenario code is in `simulator/threat_scenarios.py`.

> Realistic disclaimer: no system is 100% unhackable. TAP-RISC
> dramatically **raises the cost and complexity** of attacks by
> stacking independent defenses, so an adversary has to break
> several at once - and the response chain is autonomous, so they
> don't get a second attempt.

## Attack pattern A — Install malicious firmware

### Goal of the attacker

Inject custom firmware to bypass security, extract cryptographic keys,
or hijack the communication channel.

### Step 1: connect via debug port (JTAG / UART)

| Attacker action | TAP-RISC defense |
|---|---|
| Tries to interface with the debug port and upload firmware | Debug interfaces disabled by default once firmware is deployed (OTP-fused). |
| Opens the enclosure to access the port | Tamper sensors (MPU6050 + BMP280 + capacitive mesh) detect physical intrusion. |
| | Response: keys wiped, CPU halted, audit log appended. |

**Result:** Attack blocked **before firmware upload.**

### Step 2: attempt to flash malicious firmware

| Attacker action | TAP-RISC defense |
|---|---|
| Tries to overwrite flash with custom OS or spyware | **Secure Boot** verifies firmware HMAC-SHA256 against the OTP-fused root key. |
| | If signature is invalid: boot refuses, device halts in `BRICKED` state. |

**Result:** Malicious firmware **rejected by secure boot.**
Demonstrated by `scenario_firmware_injection` in the threat-scenario
suite.

### Step 3: exploit vulnerability in running firmware (e.g., buffer overflow)

| Attacker action | TAP-RISC defense |
|---|---|
| Inject malicious code via malformed input or unvalidated data | **Minimal firmware** — no shell, no REPL, no general-purpose network stack. Reduces attack surface. |
| | **MPU (Memory Protection Unit)** in the AT1051 blocks code from accessing privileged regions. |

**Result:** Reduced attack surface + MPU together leave the adversary
with nowhere to land payload.

### Step 4: brute-force the encrypted data

| Attacker action | TAP-RISC defense |
|---|---|
| Try to decrypt stored logs or keys | **AES-256** keyspace = 2^256 combinations - mathematically infeasible. |
| | Keys live in OTP fuses and SRAM, never exposed to firmware via readable register. |

**Result:** Data is **unreadable**; brute force is not a path.

### Step 5: replay attack on the radio channel

| Attacker action | TAP-RISC defense |
|---|---|
| Snoop and replay LoRa / BLE packets | **AES-128-CCM** payload encryption prevents reading. |
| | **Per-packet nonces + sequence numbers** prevent replay. |
| | Anomalous packet patterns surface in the audit log. |

**Result:** Replay attempts ignored at the protocol level.

---

## Attack pattern B — How Indian defense currently handles electronic security (and where TAP-RISC fits)

### Existing approaches in Indian defense

1. **Physical Security (enclosure-level)**
   - Tamper-proof enclosures with security screws or epoxy
   - Conformal coatings on PCBs
   - Guarded, access-controlled facilities
   - **Limitation:** physical security helps, but it doesn't *react*
     to tampering.

2. **Cybersecurity & Software Security**
   - Strong encryption (AES, RSA) in software
   - Secure boot for signed firmware
   - Firewalls, air-gapped systems
   - **Limitation:** software protections can be bypassed if an
     attacker gains physical access to the chip.

3. **Secure Hardware (DRDO / BEL systems)**
   - Custom secure microcontrollers with tamper detection, secure
     key storage, data wipe in high-security systems
   - **Limitation:** proprietary, expensive, not widely available;
     reserved for strategic deployments.

### Where India still has gaps (and what TAP-RISC fills)

| Challenge | Current defense | Gap TAP-RISC can fill |
|---|---|---|
| Field-deployed devices (e.g. drones) | Physical locks + software | Automatic, reactive protection on the device |
| Mass-produced electronics | Cost prevents high-end secure chips | TAP-RISC uses open-source RISC-V → 90% cost reduction |
| Real-time alerting of tampering | Rarely implemented | TAP-RISC adds LoRa alerts |
| Student / startup-friendly solutions | Not publicly available | TAP-RISC is reproducible and open |

> Most secure electronics in India are **expensive, closed-source, and
> used only in strategic zones**. TAP-RISC shows that open, affordable,
> tamper-resistant designs can be built using RISC-V and basic
> components — perfect for student innovation, startups, or smaller
> defense deployments.

## Layered defense summary

| Layer | Protection |
|---|---|
| Physical | Tamper detection sensors + resin + IP67 enclosure |
| Hardware | Secure crypto engine + MPU + OTP key fuses |
| Boot process | Secure boot + firmware signature verification |
| Firmware | Minimal code + watchdog + chained audit logs |
| Communication | AES-256 encryption + LoRa / BLE pairing |

This layered approach is the architectural realization of **defense in
depth** — every successful attack has to break multiple independent
mechanisms simultaneously.
