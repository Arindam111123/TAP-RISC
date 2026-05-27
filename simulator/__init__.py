"""
TAP-RISC simulator package.

Concept-level reference implementation of the TAP-RISC tamper-aware
edge platform. Models sensors, sensor-fusion voting, secure boot,
cryptographic erase, and chained tamper-evident logging.

This is *not* hardware emulation. It exists so that the algorithmic
choices in the DIR-V Grand Challenge proposal can be exercised,
debugged, and demonstrated without an FPGA on the desk.
"""

__version__ = "0.1.0"
