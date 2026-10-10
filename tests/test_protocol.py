import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "host"))
from protocol import Capture, CaptureProtocolError, decode_packet, encode_packet


class ProtocolTests(unittest.TestCase):
    def test_round_trip(self):
        original = Capture(1_000_000, 2, 0, True, [1, 1, 0, 0, 1])
        self.assertEqual(decode_packet(encode_packet(original)), original)

    def test_reject_truncated_packet(self):
        with self.assertRaises(CaptureProtocolError):
            decode_packet(b"ULA")

    def test_reject_bad_magic(self):
        data = bytearray(encode_packet(Capture(1_000_000, 2, 0, False, [1, 0])))
        data[0] = ord("X")
        with self.assertRaises(CaptureProtocolError):
            decode_packet(bytes(data))

    def test_reject_count_mismatch(self):
        packet = encode_packet(Capture(1_000_000, 2, 0, False, [1, 0]))
        with self.assertRaises(CaptureProtocolError):
            decode_packet(packet[:-1])

    def test_reject_invalid_sample(self):
        with self.assertRaises(CaptureProtocolError):
            encode_packet(Capture(1_000_000, 2, 0, False, [1, 2]))


if __name__ == "__main__":
    unittest.main()
