import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "host"))
from uart_decoder import decode_uart, synthesize_uart
from export_vcd import write_vcd
import tempfile


class UartDecoderTests(unittest.TestCase):
    def test_decode_known_bytes(self):
        sample_rate, baud = 9600 * 8, 9600
        samples = synthesize_uart(b"Hi\n", sample_rate, baud, idle_samples=16)
        frames = decode_uart(samples, sample_rate, baud)
        self.assertEqual([frame.value for frame in frames], list(b"Hi\n"))
        self.assertTrue(all(frame.framing_ok for frame in frames))

    def test_invalid_rate_rejected(self):
        with self.assertRaises(ValueError):
            decode_uart([1, 0, 1], 9600, 9600)

    def test_bad_stop_bit_reported(self):
        sample_rate, baud = 9600 * 8, 9600
        samples = synthesize_uart(b"A", sample_rate, baud, idle_samples=16)
        # Corrupt the centre of the first stop bit.
        frame_start = 16
        stop_centre = int(frame_start + (1.5 + 8 + 0.5) * 8)
        samples[stop_centre] = 0
        frames = decode_uart(samples, sample_rate, baud)
        self.assertEqual(len(frames), 1)
        self.assertFalse(frames[0].framing_ok)

    def test_vcd_export(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "wave.vcd"
            write_vcd([1, 1, 0, 0, 1], 1_000_000, path)
            text = path.read_text()
            self.assertIn("$timescale 1ns $end", text)
            self.assertIn("0!", text)
            self.assertIn("1!", text)


if __name__ == "__main__":
    unittest.main()
