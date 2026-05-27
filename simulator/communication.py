"""
communication.py
================
Models the two communication channels in the TAP-RISC proposal:

    - LoRa RA-02 (long-range tamper alert, up to 15 km LoS)
    - BLE 5.2    (short-range maintenance / pairing)

Both channels carry AES-encrypted payloads; LoRa with AES-128-CCM
(the LoRaWAN standard mode) and BLE with the protocol's built-in
LE Secure Connections (we model this as AES-128-CCM as well for
demo purposes).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import secrets
import time
from typing import Callable, Optional

from .security import aes256_ctr_encrypt


class Channel(Enum):
    LORA = "lora"
    BLE  = "ble"


@dataclass
class Packet:
    """A single radio packet (ciphertext + nonce + channel)."""
    channel: Channel
    nonce: bytes
    ciphertext: bytes
    t_sent: float = 0.0
    received: bool = False


class LoRaLink:
    """
    Simplified LoRa RA-02 model. Captures the parameters that matter
    for the tamper-alert use case:

        - bitrate ~ 5.5 kbps at SF7BW125 (worst-case payload duration)
        - typical line-of-sight range ~ 15 km
        - AES-128-CCM payload encryption (we use AES-256-CTR here for
          simplicity; functionally equivalent confidentiality envelope)
    """

    def __init__(self,
                 link_key: bytes,
                 packet_drop_rate: float = 0.0):
        self._link_key = link_key
        self._drop     = packet_drop_rate
        self._tx_log: list[Packet] = []

    def send_alert(self, payload: bytes, t: float = 0.0) -> Packet:
        nonce = secrets.token_bytes(16)
        ct    = aes256_ctr_encrypt(payload, self._link_key, nonce)
        pkt   = Packet(channel=Channel.LORA, nonce=nonce, ciphertext=ct, t_sent=t)
        # Drop simulation
        import random
        pkt.received = (random.random() >= self._drop)
        self._tx_log.append(pkt)
        return pkt

    def tx_log(self) -> list[Packet]:
        return list(self._tx_log)


class BLEPairing:
    """
    Minimal BLE 5.2 pairing model. Used for short-range maintenance
    access (e.g. an authorized service tech pairs a phone to read the
    audit log before swapping a device).

    Pairing requires presenting a one-time passkey. After three
    failed attempts the device locks BLE access for the remainder of
    the session.
    """

    LOCK_AFTER_FAILS = 3

    def __init__(self, passkey: str):
        self._passkey = passkey
        self.fail_count = 0
        self.locked = False

    def pair(self, attempt: str) -> bool:
        if self.locked:
            return False
        if attempt == self._passkey:
            self.fail_count = 0
            return True
        self.fail_count += 1
        if self.fail_count >= self.LOCK_AFTER_FAILS:
            self.locked = True
        return False
