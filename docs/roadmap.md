# Roadmap

The original DIR-V Grand Challenge 2025 proposal commits to the
following quarterly milestones. Status as of the latest update is
shown alongside each item.

## Q3 2025 — Design freeze (✅ completed)

- [x] Topic selection and literature review
- [x] Problem definition and solution architecture
- [x] System block diagram and subsystem interfaces
- [x] Online TAP-RISC simulator (this repository)
- [x] Bill of Materials and component selection report
- [ ] Schematic and preliminary PCB layout design files

**Output indicators:**
- ✅ Online simulator accurately models tamper events and system response
- ✅ Full system design reviewed by mentor
- 🔲 BOM and PCB designs ready for fabrication

## Q4 2025 — First prototype

- [ ] Fabricate first 4-layer PCB prototype
- [ ] Assemble TAP-RISC hardware (sensors + enclosure)
- [ ] Port simulator logic to embedded firmware on Zephyr
- [ ] Bring-up sensor integration test setup

**Output indicators:**
- 🔲 Hardware prototype boots and runs embedded firmware
- 🔲 Successful sensor data acquisition and basic tamper event detection
- 🔲 Initial crypto-erase logic validated on hardware

## Q1 2026 — Field testing

- [ ] Full system integration (hardware + software)
- [ ] Controlled-environment field tests
- [ ] Collect performance data (latency, detection accuracy)
- [ ] Refine design based on test results

**Output indicators:**
- 🔲 System passes integration tests (hardware/software co-validation)
- 🔲 Field test results: tamper accuracy, response latency, comms range
- 🔲 Documentation enables replication by other teams

## Q2 2026 — Pilot deployment

- [ ] Prepare pilot units for defense / smart infrastructure partners
- [ ] Finalize documentation for open-source release
- [ ] Engage with potential end-users
- [ ] Submit for evaluation / feedback

**Output indicators:**
- 🔲 Open-source package available on GitHub
- 🔲 Positive feedback from pilot deployments
- 🔲 Project presented to DIR-V / industry stakeholders

---

## Current status

This repository represents the **Q3 2025** milestone: a complete
conceptual design plus a working software simulator that exercises
the algorithmic core (sensor fusion, secure boot, crypto-erase,
chained audit logging, encrypted alerting).

**What is NOT yet done:**
- No real hardware prototype has been built.
- No RTL or firmware has been written for the actual Artix-7 + VEGA
  AT1051 combination.
- No field testing has occurred.

We were honest about this in the DIR-V Grand Challenge submission,
and the project was selected as a **quarterfinalist** on the strength
of the design and conceptual depth.
