"""
draw_architecture.py
====================
Draws the TAP-RISC system block diagram as an SVG, so it renders
crisply in the GitHub README without any external dependencies.

Run from the repo root:
    python scripts/draw_architecture.py
"""

from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True)


SVG = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 980 620" font-family="Inter, system-ui, sans-serif">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M0,0 L10,5 L0,10 z" fill="#444"/>
    </marker>
    <style><![CDATA[
      .box        { fill: #f6f8fa; stroke: #444; stroke-width: 1.2; rx: 6; }
      .core       { fill: #e6f4ea; stroke: #2c7a3f; stroke-width: 1.5; }
      .sensor     { fill: #fff4e5; stroke: #c06800; }
      .crypto     { fill: #e8f0fe; stroke: #1958b8; }
      .radio      { fill: #fce8e6; stroke: #b3261e; }
      .label      { font-size: 13px; fill: #111; }
      .title      { font-size: 14px; font-weight: 600; fill: #111; }
      .sub        { font-size: 11px; fill: #555; }
      .heading    { font-size: 18px; font-weight: 700; fill: #111; }
      .arrow      { stroke: #444; stroke-width: 1.3; fill: none; marker-end: url(#arrow); }
      .bus        { stroke: #2c7a3f; stroke-width: 2.2; fill: none; marker-end: url(#arrow); }
    ]]></style>
  </defs>

  <text x="490" y="34" text-anchor="middle" class="heading">TAP-RISC Block Architecture</text>
  <text x="490" y="54" text-anchor="middle" class="sub">VEGA AT1051 (RV32IMA) + Artix-7 100T FPGA + multi-modal tamper detection</text>

  <!-- ============ Sensor layer (left) ============ -->
  <text x="120" y="92" text-anchor="middle" class="title">Tamper Sensors</text>

  <rect x="40" y="110" width="160" height="58" class="box sensor"/>
  <text x="120" y="132" text-anchor="middle" class="title">MPU6050</text>
  <text x="120" y="150" text-anchor="middle" class="sub">6-axis accel (±2g – ±16g)</text>
  <text x="120" y="164" text-anchor="middle" class="sub">tilt / shock</text>

  <rect x="40" y="186" width="160" height="58" class="box sensor"/>
  <text x="120" y="208" text-anchor="middle" class="title">BMP280</text>
  <text x="120" y="226" text-anchor="middle" class="sub">300-1100 hPa, ±1 hPa</text>
  <text x="120" y="240" text-anchor="middle" class="sub">enclosure breach</text>

  <rect x="40" y="262" width="160" height="58" class="box sensor"/>
  <text x="120" y="284" text-anchor="middle" class="title">Capacitive PCB Mesh</text>
  <text x="120" y="302" text-anchor="middle" class="sub">0.2 mm pitch traces</text>
  <text x="120" y="316" text-anchor="middle" class="sub">drill / cut / probe</text>

  <!-- ============ VEGA / Artix core (center) ============ -->
  <rect x="300" y="100" width="380" height="240" class="box core"/>
  <text x="490" y="124" text-anchor="middle" class="title">Compute &amp; Security Core</text>

  <rect x="320" y="142" width="160" height="58" class="box"/>
  <text x="400" y="164" text-anchor="middle" class="title">VEGA AT1051</text>
  <text x="400" y="180" text-anchor="middle" class="sub">RV32IMA, 5-stage in-order</text>
  <text x="400" y="194" text-anchor="middle" class="sub">C-DAC indigenous core</text>

  <rect x="500" y="142" width="160" height="58" class="box"/>
  <text x="580" y="164" text-anchor="middle" class="title">Artix-7 100T</text>
  <text x="580" y="180" text-anchor="middle" class="sub">~101K logic cells</text>
  <text x="580" y="194" text-anchor="middle" class="sub">AES-256, SHA-256 IP</text>

  <rect x="320" y="218" width="340" height="48" class="box crypto"/>
  <text x="490" y="240" text-anchor="middle" class="title">Sensor Fusion (2-of-3 voter)</text>
  <text x="490" y="256" text-anchor="middle" class="sub">false positives &lt; 0.01% via majority logic</text>

  <rect x="320" y="278" width="160" height="48" class="box crypto"/>
  <text x="400" y="298" text-anchor="middle" class="title">Secure Boot</text>
  <text x="400" y="314" text-anchor="middle" class="sub">HMAC/SHA-256 + LibreSSL</text>

  <rect x="500" y="278" width="160" height="48" class="box crypto"/>
  <text x="580" y="298" text-anchor="middle" class="title">Crypto-Erase</text>
  <text x="580" y="314" text-anchor="middle" class="sub">&lt; 500 ms AES-256-CTR wipe</text>

  <!-- ============ Right column ============ -->
  <text x="850" y="92" text-anchor="middle" class="title">Comms &amp; Storage</text>

  <rect x="760" y="110" width="180" height="58" class="box radio"/>
  <text x="850" y="132" text-anchor="middle" class="title">LoRa RA-02</text>
  <text x="850" y="150" text-anchor="middle" class="sub">~15 km LoS, AES-128-CCM</text>
  <text x="850" y="164" text-anchor="middle" class="sub">tamper alerts</text>

  <rect x="760" y="186" width="180" height="58" class="box radio"/>
  <text x="850" y="208" text-anchor="middle" class="title">BLE 5.2</text>
  <text x="850" y="226" text-anchor="middle" class="sub">secure pairing (FIDO2)</text>
  <text x="850" y="240" text-anchor="middle" class="sub">maintenance access</text>

  <rect x="760" y="262" width="180" height="58" class="box crypto"/>
  <text x="850" y="284" text-anchor="middle" class="title">Chained Audit Log</text>
  <text x="850" y="302" text-anchor="middle" class="sub">SHA-256 hash chain</text>
  <text x="850" y="316" text-anchor="middle" class="sub">append-only EEPROM</text>

  <!-- ============ Power / enclosure (bottom) ============ -->
  <rect x="300" y="360" width="380" height="80" class="box"/>
  <text x="490" y="384" text-anchor="middle" class="title">Power &amp; Enclosure</text>
  <text x="490" y="404" text-anchor="middle" class="sub">IP67 housing, conformal coating, anti-tamper resin</text>
  <text x="490" y="420" text-anchor="middle" class="sub">USB / battery, watchdog timer</text>

  <!-- ============ RTOS (bottom strip) ============ -->
  <rect x="40" y="460" width="900" height="60" class="box"/>
  <text x="490" y="484" text-anchor="middle" class="title">Zephyr RTOS</text>
  <text x="490" y="502" text-anchor="middle" class="sub">open-source, RISC-V-aware, modular subsystem drivers (sensors / crypto / radio)</text>

  <!-- ============ Footer ============ -->
  <text x="490" y="556" text-anchor="middle" class="sub">Defense in depth: physical → detection → response → forensics</text>
  <text x="490" y="576" text-anchor="middle" class="sub">DIR-V Grand Challenge 2025 · Team YugaMicro · BMS Institute of Technology and Management</text>

  <!-- ============ Arrows ============ -->
  <!-- sensors to core -->
  <path class="arrow" d="M200,139 C 240,139 260,200 300,200"/>
  <path class="arrow" d="M200,215 L300,215"/>
  <path class="arrow" d="M200,291 C 240,291 260,232 300,232"/>

  <!-- core to comms -->
  <path class="arrow" d="M660,210 C 700,210 720,139 760,139"/>
  <path class="arrow" d="M660,250 L760,250"/>
  <path class="arrow" d="M660,300 L760,291"/>

  <!-- core to enclosure / rtos -->
  <path class="bus" d="M490,340 L490,360"/>
  <path class="bus" d="M490,440 L490,460"/>
</svg>
'''


def main():
    out = OUT / "architecture.svg"
    out.write_text(SVG)
    print(f"Wrote {out}")

    # Also rasterize to PNG for clients that prefer it (e.g. some
    # markdown viewers don't render SVG well).
    try:
        import cairosvg
        png = OUT / "architecture.png"
        cairosvg.svg2png(bytestring=SVG.encode(), write_to=str(png),
                         output_width=1600)
        print(f"Wrote {png}")
    except ImportError:
        print("(install cairosvg to also emit a PNG version)")


if __name__ == "__main__":
    main()
