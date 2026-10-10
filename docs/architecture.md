# Architecture and firmware design

## Data path

1. A GPIO input is sampled by a PIO state machine at a configured rate.
2. The PIO input shift register pushes packed groups of samples to its RX FIFO.
3. DMA moves FIFO words into an aligned fixed-size SRAM word buffer.
4. The capture layer unpacks each word into one byte per sample for the first binary packet format.
5. Firmware writes a versioned header followed by one byte per sample to USB CDC.
6. The Python host validates the packet and decodes UART frames from sample centres.

## PIO/DMA rationale

A CPU interrupt for every sample would have substantial latency and jitter. PIO provides a compact, deterministic sampling loop and DMA transfers completed words to memory. CPU work is limited to starting capture, waiting for bounded transfer completion, unpacking samples, and moving a packet to USB CDC.

## Trigger behaviour

`immediate` starts sampling as soon as the state machine is enabled. `edge` waits for a high-to-low transition before arming the sampler. This is a start-edge gate, not a circular pre-trigger acquisition; `pretrigger_samples` is reserved for a future ring-buffer implementation and must not be described as a working pre-trigger feature in this version.

## Capture limits

- The public sample count is bounded by `CAPTURE_MAX_SAMPLES`.
- The initial firmware turns packed PIO words into one byte per sample for a simple host representation.
- The selected sample rate is applied by setting the PIO clock divider; achievable rates depend on system clock and PIO instruction timing.
- The maximum sustained rate, timing error, and USB throughput are board-specific measurement items, not inferred guarantees.

## Safety and design boundary

The tool reads a digital signal and does not drive the target. Verify target output voltage before connecting it to RP2040 GPIO. Never connect a 5 V or unknown-voltage signal directly to the RP2040.
