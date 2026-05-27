# Hardware Bill of Materials

Estimated component costs at India retail (June 2025). All quantities
are for a single TAP-RISC prototype unit.

## Core compute

| Item | Qty | Approx. cost (INR) | Source / notes |
|---|---|---|---|
| Xilinx Artix-7 100T (e.g. Arty A7-100T board) | 1 | 22,000 | Hosts the VEGA AT1051 soft core + security peripherals |
| VEGA AT1051 RISC-V IP (RV32IMA) | 1 | 0 | C-DAC indigenous IP, free for academic / DIR-V use |
| Programmer / JTAG (Digilent HS3 or similar) | 1 | 4,500 | Development only, removed for deployment |

## Tamper sensor stack

| Item | Qty | Approx. cost (INR) | Notes |
|---|---|---|---|
| MPU6050 6-axis IMU breakout | 1 | 150 | ±2g to ±16g configurable |
| BMP280 pressure sensor breakout | 1 | 200 | 300-1100 hPa, ±1 hPa |
| Custom 4-layer PCB with capacitive mesh | 1 | 1,200 | JLCPCB / similar, fabbed in qty 5 for ~₹600 each in volume |

## Communication

| Item | Qty | Approx. cost (INR) | Notes |
|---|---|---|---|
| Ai-Thinker RA-02 LoRa module (433 MHz) | 1 | 450 | Up to ~15 km LoS |
| LoRa antenna (3 dBi whip) | 1 | 150 | SMA connector |
| BLE 5.2 module (integrated on dev kit) | - | 0 | Included on most Artix-7 starter boards via daughter card |

## Power and enclosure

| Item | Qty | Approx. cost (INR) | Notes |
|---|---|---|---|
| LiPo battery, 2000 mAh | 1 | 350 | 8+ hours runtime at active poll |
| Battery management board (TP4056) | 1 | 80 | USB-C charging |
| IP67 ABS enclosure (120×80×60 mm) | 1 | 700 | Bud Industries equivalents |
| Anti-tamper resin (epoxy + opaque pigment) | 50 ml | 250 | For potting around the FPGA + key OTP |
| Conformal coating spray | 100 ml | 350 | Acrylic, MG Chemicals or equivalent |
| Tactile push-button (commissioning) | 1 | 30 | One-time pairing |
| Status LEDs (RGB) | 2 | 40 | Visible through enclosure |

## Subtotal (prototype)

| Bucket | Cost (INR) |
|---|---|
| Core compute (dev board) | 26,500 |
| Sensors | 1,550 |
| Communications | 600 |
| Power / enclosure | 1,800 |
| Miscellaneous (wires, headers, PCB jumpers) | 500 |
| **Total prototype unit** | **~₹30,950** |

## Production estimate

Once moved off the development board and onto a custom Artix-7-equivalent
SoC with integrated MCU, the BOM target is **₹10,000 per unit at
1,000-unit volumes**, matching the DIR-V proposal's headline number.
Bulk pricing assumes:

| Item | Volume cost (INR) |
|---|---|
| Custom 4-layer PCB with FPGA + sensors | 4,500 |
| LoRa + BLE radio | 600 |
| LiPo + BMS | 400 |
| Enclosure + sealing | 1,500 |
| Assembly / test | 2,500 |
| Margin / contingency | 500 |
| **Per-unit BOM at qty 1k** | **~₹10,000** |

## Comparison anchor

For reference, the cheapest Thales Luna USB HSM retails at ~₹1,00,000+
per unit (IndiaMart, June 2025) and provides only a subset of TAP-RISC's
capabilities (no field deployment, no autonomous response).
