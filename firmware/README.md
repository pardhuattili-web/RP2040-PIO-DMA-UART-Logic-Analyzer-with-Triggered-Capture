# Firmware notes

This folder contains the RP2040 Pico SDK application and PIO sampler. Firmware compilation requires the official Pico SDK and ARM GCC toolchain.

Current firmware scope:
- GPIO input sampling through PIO;
- DMA transfer into fixed-size words;
- bounded capture count;
- immediate and falling-edge-gated modes;
- USB CDC packet header plus samples.

The host tools are intentionally testable without the board. Before claiming a live demo, build the firmware with your installed SDK, flash a Pico, capture a known UART payload, and record the results.

Do not treat `pretrigger_samples` as implemented ring-buffer pre-trigger capture in this version.
