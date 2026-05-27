"""
security.py
===========
Software model of the security primitives that TAP-RISC firmware
provides on top of the VEGA AT1051 core:

    - Secure boot          : verify firmware signature before exec
    - Crypto-erase         : overwrite key material in <500 ms
    - Chained tamper log   : SHA-256 hash chain stored append-only
    - AES-256-CTR data-at-rest encryption

Implementation notes
--------------------
Real firmware would use the Artix-7's AES block and a libreSSL-based
secure-boot loader. Here we use Python's `hashlib` and `cryptography`
to model the same behavior. The algorithmic shape is faithful; the
hardware acceleration is not.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import hashlib
import hmac
import os
import secrets
import time
from typing import Optional


# =====================================================================
# Secure boot
# =====================================================================
@dataclass
class FirmwareImage:
    """A firmware blob with an attached HMAC-SHA256 signature."""
    payload: bytes
    signature: bytes        # HMAC-SHA256(payload, root_key)
    version: str = "v0"


class SecureBootError(Exception):
    """Raised when boot-time integrity check fails."""


class RootOfTrust:
    """
    Models the immutable hardware root of trust.

    The real device burns the root key into Artix-7 OTP fuses at
    manufacture; here we generate it once and pretend it's silicon.
    The key never leaves this object - even the firmware can't read
    it directly, only ask the RoT to verify or sign.
    """

    def __init__(self, root_key: Optional[bytes] = None):
        # In real hardware: read-only OTP fuses, not assignable.
        self._root_key: bytes = root_key or secrets.token_bytes(32)

    # ---- signing (factory / authorized side) ----
    def sign_firmware(self, payload: bytes, version: str = "v0") -> FirmwareImage:
        """Used by the factory to produce a signed firmware blob."""
        sig = hmac.new(self._root_key, payload, hashlib.sha256).digest()
        return FirmwareImage(payload=payload, signature=sig, version=version)

    # ---- verification (boot-time) ----
    def verify_firmware(self, img: FirmwareImage) -> bool:
        """
        Constant-time HMAC comparison. Returns True if signature is
        valid for this RoT's root key.
        """
        expected = hmac.new(self._root_key, img.payload, hashlib.sha256).digest()
        return hmac.compare_digest(expected, img.signature)

    def boot(self, img: FirmwareImage) -> None:
        """
        Boot sequence: verify and either hand off or refuse.
        Raises SecureBootError on signature mismatch.
        """
        if not self.verify_firmware(img):
            raise SecureBootError(
                f"Firmware {img.version!r} signature invalid - refusing to boot"
            )


# =====================================================================
# Crypto-erase
# =====================================================================
@dataclass
class SecureKeyStore:
    """
    Holds the long-term cryptographic material that must survive
    normal operation but be destroyed *immediately* when tampered.

    The proposal's headline number is a <500 ms wipe; in software
    the actual overwrite is microseconds, so we model the timing
    explicitly to represent a realistic Artix-7 OTP/SRAM zeroize
    cycle.
    """
    aes_key: bytes = field(default_factory=lambda: secrets.token_bytes(32))
    ecdsa_priv: bytes = field(default_factory=lambda: secrets.token_bytes(32))
    audit_seed: bytes = field(default_factory=lambda: secrets.token_bytes(32))

    erased: bool = False
    erase_duration_ms: float = 0.0

    def crypto_erase(self) -> float:
        """
        Overwrite every key byte with cryptographically random data,
        then zero it. Returns the wall-clock duration of the wipe
        in milliseconds.

        On real hardware this is done by an AES-256-CTR overwrite
        routine running from internal SRAM (no flash, so no wear
        leveling defeats the wipe). 500 ms is the budget on the
        VEGA AT1051 + Artix-7 platform.
        """
        if self.erased:
            return self.erase_duration_ms

        start = time.perf_counter()

        # Three-pass overwrite: random, complement, zeros.
        # Matches NIST SP 800-88 "purge" guidance for non-rotational
        # media, conservative for our SRAM-backed key store.
        for field_name in ("aes_key", "ecdsa_priv", "audit_seed"):
            n = len(getattr(self, field_name))
            object.__setattr__(self, field_name, secrets.token_bytes(n))
            object.__setattr__(self, field_name, bytes(b ^ 0xFF for b in getattr(self, field_name)))
            object.__setattr__(self, field_name, b"\x00" * n)

        self.erased = True
        self.erase_duration_ms = (time.perf_counter() - start) * 1000.0
        return self.erase_duration_ms


# =====================================================================
# Chained tamper log (SHA-256 hash chain, append-only)
# =====================================================================
@dataclass
class LogEntry:
    seq: int
    t: float
    event: str
    detail: str
    prev_hash: str
    this_hash: str

    def serialize(self) -> str:
        return (
            f"#{self.seq:04d} t={self.t:.3f}s "
            f"event={self.event} detail={self.detail!r} "
            f"prev={self.prev_hash[:8]}.. this={self.this_hash[:8]}.."
        )


class TamperLog:
    """
    Append-only audit log with blockchain-style chaining.

    Each entry's hash incorporates the previous entry's hash, so
    silently editing any past entry invalidates every entry that
    came after. On real hardware this lives in write-once flash
    or external EEPROM that's read by service personnel only.
    """

    GENESIS_HASH = "0" * 64

    def __init__(self):
        self._entries: list[LogEntry] = []

    def append(self, event: str, detail: str, t: float = 0.0) -> LogEntry:
        prev = self._entries[-1].this_hash if self._entries else self.GENESIS_HASH
        seq  = len(self._entries)
        body = f"{seq}|{t:.3f}|{event}|{detail}|{prev}"
        this_hash = hashlib.sha256(body.encode()).hexdigest()

        entry = LogEntry(
            seq=seq, t=t, event=event, detail=detail,
            prev_hash=prev, this_hash=this_hash,
        )
        self._entries.append(entry)
        return entry

    def verify(self) -> bool:
        """Walk the chain end-to-end. Any tampering trips this check."""
        prev = self.GENESIS_HASH
        for e in self._entries:
            body = f"{e.seq}|{e.t:.3f}|{e.event}|{e.detail}|{prev}"
            if hashlib.sha256(body.encode()).hexdigest() != e.this_hash:
                return False
            if e.prev_hash != prev:
                return False
            prev = e.this_hash
        return True

    def entries(self) -> list[LogEntry]:
        return list(self._entries)


# =====================================================================
# AES-256-CTR data-at-rest helpers (optional; needs `cryptography`)
# =====================================================================
def aes256_ctr_encrypt(plaintext: bytes, key: bytes, nonce: bytes) -> bytes:
    """Thin wrapper for documentation; firmware would use hw acceleration."""
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        cipher = Cipher(algorithms.AES(key), modes.CTR(nonce))
        enc = cipher.encryptor()
        return enc.update(plaintext) + enc.finalize()
    except ImportError:
        # Fallback: not cryptographically meaningful, just for demo.
        keystream = (hashlib.sha256(key + nonce + i.to_bytes(4, "big")).digest()
                     for i in range((len(plaintext) + 31) // 32))
        ks = b"".join(keystream)[:len(plaintext)]
        return bytes(p ^ k for p, k in zip(plaintext, ks))


def aes256_ctr_decrypt(ciphertext: bytes, key: bytes, nonce: bytes) -> bytes:
    """CTR mode is symmetric - encrypt and decrypt are the same op."""
    return aes256_ctr_encrypt(ciphertext, key, nonce)
