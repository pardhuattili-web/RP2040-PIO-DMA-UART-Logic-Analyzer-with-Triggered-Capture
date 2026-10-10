"""Sample-based asynchronous UART decoder; no hardware dependency."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UartFrame:
    start_sample: int
    value: int
    data_bits: int
    parity: str
    stop_bits: int
    parity_ok: bool | None
    framing_ok: bool
    end_sample: int


def decode_uart(samples: list[int], sample_rate_hz: int, baud: int,
                data_bits: int = 8, parity: str = "none",
                stop_bits: int = 1, idle: int = 1) -> list[UartFrame]:
    """Decode UART frames from uniformly spaced digital samples.

    The falling edge is detected at a high-to-low transition. Bits are sampled near
    their centres. This simple decoder is intended for clean captures with a sample
    rate >= 8x baud; it does not attempt automatic baud estimation.
    """
    if sample_rate_hz <= 0 or baud <= 0:
        raise ValueError("sample rate and baud must be positive")
    if sample_rate_hz < baud * 4:
        raise ValueError("sample rate should be at least 4 times the baud rate")
    if data_bits not in (5, 6, 7, 8, 9):
        raise ValueError("data_bits must be between 5 and 9")
    parity = parity.lower()
    if parity not in ("none", "even", "odd"):
        raise ValueError("parity must be none, even, or odd")
    if stop_bits not in (1, 2):
        raise ValueError("stop_bits must be 1 or 2")
    if idle not in (0, 1) or any(s not in (0, 1) for s in samples):
        raise ValueError("samples and idle must be binary")
    spb = sample_rate_hz / baud
    frames: list[UartFrame] = []
    i = 1
    n = len(samples)

    while i < n:
        if samples[i - 1] == idle and samples[i] != idle:
            start = i
            start_centre = start + 0.5 * spb
            # Verify candidate start bit is still low at its centre.
            start_idx = int(start_centre)
            if start_idx >= n or samples[start_idx] == idle:
                i += max(1, int(spb / 2))
                continue

            value = 0
            bit_centre = start + 1.5 * spb
            enough = True
            for bit in range(data_bits):
                idx = int(bit_centre + bit * spb)
                if idx >= n:
                    enough = False
                    break
                value |= samples[idx] << bit
            if not enough:
                break

            cursor = start + (1.5 + data_bits) * spb
            parity_ok: bool | None = None
            if parity != "none":
                pidx = int(cursor)
                if pidx >= n:
                    break
                pbit = samples[pidx]
                ones = value.bit_count()
                expected = (ones & 1) if parity == "even" else (1 - (ones & 1))
                parity_ok = pbit == expected
                cursor += spb

            framing_ok = True
            for stop in range(stop_bits):
                sidx = int(cursor + stop * spb)
                if sidx >= n:
                    enough = False
                    break
                if samples[sidx] != idle:
                    framing_ok = False
            if not enough:
                break
            end_sample = min(n - 1, int(cursor + stop_bits * spb))
            frames.append(UartFrame(start, value, data_bits, parity, stop_bits,
                                    parity_ok, framing_ok, end_sample))
            i = max(i + 1, end_sample)
        else:
            i += 1
    return frames


def synthesize_uart(data: bytes, sample_rate_hz: int, baud: int,
                    data_bits: int = 8, parity: str = "none",
                    stop_bits: int = 1, idle_samples: int = 2) -> list[int]:
    """Generate idealized sample data for tests and examples."""
    if sample_rate_hz <= 0 or baud <= 0 or sample_rate_hz % baud != 0:
        raise ValueError("sample rate must be a positive integer multiple of baud")
    if data_bits not in (5, 6, 7, 8, 9) or stop_bits not in (1, 2):
        raise ValueError("unsupported frame configuration")
    parity = parity.lower()
    if parity not in ("none", "even", "odd"):
        raise ValueError("parity must be none, even, or odd")
    spb = sample_rate_hz // baud
    samples = [1] * idle_samples
    mask = (1 << data_bits) - 1
    for byte in data:
        value = byte & mask
        samples.extend([0] * spb)
        for bit in range(data_bits):
            samples.extend([(value >> bit) & 1] * spb)
        if parity != "none":
            parity_bit = (value.bit_count() & 1) if parity == "even" else (1 - (value.bit_count() & 1))
            samples.extend([parity_bit] * spb)
        samples.extend([1] * (stop_bits * spb))
        samples.extend([1] * idle_samples)
    return samples
