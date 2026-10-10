"""Binary packet framing shared by the RP2040 firmware and the host tools."""
from __future__ import annotations

from dataclasses import dataclass
import struct

MAGIC = b"ULAC"
VERSION = 1
# Little-endian on RP2040: magic, version, flags, GPIO, reserved, rate, count, trigger index
HEADER = struct.Struct("<4sBBBBIII")


class CaptureProtocolError(ValueError):
    """Raised when a capture packet is incomplete or invalid."""


@dataclass(frozen=True)
class Capture:
    sample_rate_hz: int
    gpio_pin: int
    trigger_index: int
    edge_triggered: bool
    samples: list[int]


def encode_packet(capture: Capture) -> bytes:
    if capture.sample_rate_hz <= 0:
        raise CaptureProtocolError("sample rate must be positive")
    if not 0 <= capture.gpio_pin <= 29:
        raise CaptureProtocolError("GPIO pin must be in the range 0..29")
    if not capture.samples:
        raise CaptureProtocolError("capture must contain samples")
    if any(sample not in (0, 1) for sample in capture.samples):
        raise CaptureProtocolError("samples must be binary values")
    flags = 1 if capture.edge_triggered else 0
    header = HEADER.pack(MAGIC, VERSION, flags, capture.gpio_pin, 0,
                         capture.sample_rate_hz, len(capture.samples), capture.trigger_index)
    return header + bytes(capture.samples)


def decode_packet(data: bytes) -> Capture:
    if len(data) < HEADER.size:
        raise CaptureProtocolError("packet is shorter than the capture header")
    magic, version, flags, pin, _reserved, rate, count, trigger_index = HEADER.unpack_from(data)
    if magic != MAGIC:
        raise CaptureProtocolError("invalid packet magic")
    if version != VERSION:
        raise CaptureProtocolError(f"unsupported packet version: {version}")
    if flags & ~1:
        raise CaptureProtocolError("packet has unknown flag bits")
    if rate == 0:
        raise CaptureProtocolError("sample rate must be positive")
    if pin > 29:
        raise CaptureProtocolError("GPIO pin out of range")
    if count == 0:
        raise CaptureProtocolError("packet contains no samples")
    expected = HEADER.size + count
    if len(data) != expected:
        raise CaptureProtocolError(f"packet length mismatch: expected {expected}, got {len(data)}")
    if trigger_index >= count:
        raise CaptureProtocolError("trigger index is outside sample buffer")
    samples = list(data[HEADER.size:])
    if any(sample not in (0, 1) for sample in samples):
        raise CaptureProtocolError("sample payload contains non-binary values")
    return Capture(rate, pin, trigger_index, bool(flags & 1), samples)
