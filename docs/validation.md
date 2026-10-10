# Validation checklist and evidence

## Automated host checks

Run `make test`. Tests cover:

- packet encoding/decoding round trips;
- invalid magic, incomplete packets, length mismatch, and invalid sample data;
- UART decoding of known synthetic bytes;
- framing-error reporting after corrupting a stop bit;
- VCD waveform export.

These tests run without physical hardware.

## Firmware compile

```sh
cmake -S . -B build -DPICO_SDK_PATH="$PICO_SDK_PATH"
cmake --build build
```

A build needs the official Pico SDK, ARM GCC toolchain, and TinyUSB support provided by the SDK. The host-only CI workflow does not claim to compile firmware.

## Hardware-in-the-loop checklist

- [ ] Confirm Pico enumerates as USB CDC device.
- [ ] Verify immediate capture with a known idle-high signal.
- [ ] Verify edge mode triggers on high-to-low transition.
- [ ] Send known UART bytes and compare the decoded result.
- [ ] Test 9,600, 38,400, 57,600, and 115,200 baud.
- [ ] Record observed sample rate, capture window, and serial transfer duration.
- [ ] Test a disconnected input and a noisy input.
- [ ] Confirm no overrun/truncation occurs at intended settings.

## Known limitations in version 1

- Edge mode gates capture start, but there is no circular pre-trigger buffer.
- The PIO sample program pushes packed words, while USB sends a simple one-byte-per-sample payload.
- The host CDC framing client is not yet fully integrated; raw packet decode is implemented.
- The firmware command loop and USB CDC integration must be verified against the selected SDK version and physical board.
- No hard-real-time or maximum-throughput claim is made without measurements.
