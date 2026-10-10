#!/usr/bin/env python3
"""Decode a JSON capture fixture or a raw firmware packet and export CSV/VCD."""
from __future__ import annotations

import argparse
import csv
import json
import struct
from pathlib import Path

from protocol import Capture, decode_packet, HEADER
from uart_decoder import decode_uart
from export_vcd import write_vcd


def load_capture(path: Path) -> Capture:
    raw = path.read_bytes()
    if raw[:4] == b"ULAC":
        return decode_packet(raw)
    # Firmware currently writes a short text banner to USB CDC before command mode.
    # Extract one packet by its magic marker and declared sample count.
    marker = raw.find(b"ULAC")
    if marker >= 0:
        tail = raw[marker:]
        if len(tail) < HEADER.size:
            raise ValueError("found ULAC marker but header is incomplete")
        count = struct.unpack_from("<I", tail, 12)[0]
        packet_len = HEADER.size + count
        if len(tail) < packet_len:
            raise ValueError(f"incomplete USB capture packet: need {packet_len}, got {len(tail)}")
        return decode_packet(tail[:packet_len])
    doc = json.loads(raw.decode("utf-8"))
    samples = doc["samples"]
    return Capture(int(doc["sample_rate_hz"]), int(doc.get("gpio_pin", 2)),
                   int(doc.get("trigger_index", 0)), bool(doc.get("edge_triggered", False)),
                   [int(x) for x in samples])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="JSON capture fixture or binary ULAC packet")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--data-bits", type=int, default=8)
    parser.add_argument("--parity", choices=("none", "even", "odd"), default="none")
    parser.add_argument("--stop-bits", type=int, choices=(1, 2), default=1)
    parser.add_argument("--csv", type=Path, help="write decoded frame CSV")
    parser.add_argument("--vcd", type=Path, help="write full sample waveform VCD")
    args = parser.parse_args()

    capture = load_capture(args.input)
    frames = decode_uart(capture.samples, capture.sample_rate_hz, args.baud,
                         args.data_bits, args.parity, args.stop_bits)
    print(f"capture: {len(capture.samples)} samples at {capture.sample_rate_hz} Hz; GPIO{capture.gpio_pin}")
    print(f"decoded {len(frames)} frame(s) at {args.baud} baud")
    for frame in frames:
        print(f"sample={frame.start_sample:6d} byte=0x{frame.value:02X} "
              f"char={chr(frame.value) if 32 <= frame.value < 127 else '.'!r} "
              f"parity_ok={frame.parity_ok} framing_ok={frame.framing_ok}")

    if args.csv:
        with args.csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["start_sample", "time_ns", "value", "hex", "character", "parity_ok", "framing_ok"])
            for frame in frames:
                writer.writerow([frame.start_sample,
                                 round(frame.start_sample * 1_000_000_000 / capture.sample_rate_hz),
                                 frame.value, f"0x{frame.value:02X}",
                                 chr(frame.value) if 32 <= frame.value < 127 else "",
                                 frame.parity_ok, frame.framing_ok])
    if args.vcd:
        write_vcd(capture.samples, capture.sample_rate_hz, args.vcd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
