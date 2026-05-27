# Comparative Analysis

This document positions TAP-RISC against existing Indian and global
secure-electronics solutions. Numbers and behaviors are summarized
from public datasheets and the references at the bottom.

## Headline comparison

| System | Unit cost (INR) | Tamper response | Field deployable | RISC-V / open |
|---|---|---|---|---|
| Thales Luna HSM (network)        | ~₹1,00,000+ | Policy-based, manual recovery | Limited (rack) | No (proprietary) |
| BEL Critical Infra Radar         | ~₹50,00,000 | None (physical hardening only) | Fixed install | No |
| NEC Tamper Detect (memory inspect) | n/a (closed) | 6 ms memory inspection | Limited | No |
| **TAP-RISC (this project)**      | **~₹10,000** | **Autonomous wipe + alert in <500 ms** | **Yes (portable, IP67)** | **Yes (VEGA RISC-V, open spec)** |

The ~90% cost reduction comes from three places:

1. **No royalty cost on the ISA**. RISC-V is unencumbered; ARM Cortex
   secure-element variants carry per-unit licensing fees.
2. **Commodity sensors** instead of proprietary tamper switches.
   MPU6050 and BMP280 are bulk parts costing well under $1 each.
3. **JLCPCB-class fabrication** instead of automotive-qualified PCBs.
   This is appropriate for the threat model: we're protecting cargo,
   meters, and edge boxes, not orbital electronics.

## Detailed comparison by capability

### Tamper detection

| | Existing approach | TAP-RISC approach |
|---|---|---|
| Sensing modality | Single-mode (mostly mechanical switches or memory checks) | Triple-modal: motion + pressure + capacitive mesh |
| False positive rate | ~1-5% on commercial HSMs with policy-based detection | <0.01% via 2-of-3 voting |
| Response time | Manual intervention often required (Thales) | Fully autonomous, <500 ms wipe |
| Detection latency | 6 ms (NEC memory inspection, single-mode) | ~10 ms sensor poll × 2 ticks = ~20 ms confirmation |

### Cryptographic response

| | Existing approach | TAP-RISC approach |
|---|---|---|
| Key storage | Software-accessible (with HSM gating) | OTP-fused root key, never readable |
| Wipe trigger | Manual or policy-triggered | Autonomous on sensor fusion event |
| Wipe technique | Soft-delete + key zeroize | Three-pass NIST SP 800-88 purge in SRAM |
| Audit | External SIEM log (mutable) | On-device SHA-256 chained log (tamper-evident) |

### Communication

| | Existing approach | TAP-RISC approach |
|---|---|---|
| Range | Dedicated RF or wired (BEL radar) - vulnerable to jamming | LoRa (15 km) + BLE 5.2 backup |
| Encryption | Proprietary (varies) | AES-128-CCM (LoRaWAN std) + FIDO2 BLE pairing |
| Replay protection | Often handled at application layer | Nonce + sequence number per packet |

### Openness and reproducibility

| | Existing approach | TAP-RISC approach |
|---|---|---|
| ISA license | Proprietary (ARM) or restricted | RISC-V (open standard) |
| HDL / firmware availability | Closed; NDA required | MIT/Apache licensed; published on GitHub |
| Educational use | Restricted | Reference design for academic curricula |
| Third-party audit | Vendor-controlled | Anyone can audit |

## Strategic complementarity, not replacement

TAP-RISC is positioned as a **complement** to existing defense
infrastructure, not a wholesale replacement:

- It can sit **inside** a BEL radar installation's downstream sensor
  payloads, adding active tamper resistance to a system that today
  relies only on perimeter security.
- It can **augment** EVMs with active tamper monitoring (the
  currently used air-gap approach is passive).
- It is **cheap enough** to deploy in volumes where Thales-grade
  HSMs are economically prohibitive (e.g. smart meters, border
  sensors, UAV electronics).

## References

| # | Source |
|---|---|
| 1 | BEL Critical Infrastructure Protection System product page |
| 2 | Election Commission of India press statements on EVM security |
| 3 | Thales Luna HSM administrative documentation |
| 4 | NEC tamper-detect press release (2018) |
| 5 | IndiaMart pricing data for Thales Luna network HSM |
| 6 | DRDO Cyber Information & Communication Security overview |
| 7 | Wikipedia: Indian Ballistic Missile Defence Programme |
| 8 | C-DAC VEGA AT1051 product datasheet |
| 9 | AMD/Xilinx XC7A100T product brief |
| 10 | MeitY DIR-V program announcement (PIB, 2022) |
| 11 | IoT market sizing: IDC India (2024-2025) |
