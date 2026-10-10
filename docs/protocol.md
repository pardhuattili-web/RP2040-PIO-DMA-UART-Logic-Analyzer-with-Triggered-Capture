# USB CDC capture packet format

Protocol version 1 uses a 20-byte little-endian header followed by exactly `sample_count` bytes, one byte per sample.

| Offset | Size | Field | Description |
|---:|---:|---|---|
| 0 | 4 | magic | ASCII `ULAC` |
| 4 | 1 | version | `1` |
| 5 | 1 | flags | bit 0 set when falling-edge trigger mode was requested |
| 6 | 1 | gpio_pin | GPIO number |
| 7 | 1 | reserved | must be zero in version 1 |
| 8 | 4 | sample_rate_hz | sample clock in Hz |
| 12 | 4 | sample_count | number of sample bytes after the header |
| 16 | 4 | trigger_index | sample offset of the trigger; currently zero |

All multi-byte integer fields are little-endian. The payload contains binary sample values 0 or 1, one per sample. Version 1 is deliberately simple and is not bandwidth-efficient; a packed-bit transport format could reduce transfer size by 8× in a later version.

Host validation rejects unknown versions, unknown flag bits, zero rate/count, impossible GPIO numbers, out-of-range trigger indices, malformed lengths, and non-binary sample values.

## Firmware / host note

The firmware's capture buffer is a byte array in the public capture result, but acquisition uses DMA into a temporary 32-bit word array and unpacks that into one byte per sample before USB transfer. Host utilities accept both JSON synthetic fixtures and raw packet bytes.
