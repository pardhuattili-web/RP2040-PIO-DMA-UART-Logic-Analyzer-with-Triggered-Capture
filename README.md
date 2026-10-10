# RP2040 PIO/DMA UART Logic Analyzer with Triggered Capture

[![Host tests](https://github.com/pardhuattili-web/RP2040-PIO-DMA-UART-Logic-Analyzer-with-Triggered-Capture/actions/workflows/host-tests.yml/badge.svg)](https://github.com/pardhuattili-web/RP2040-PIO-DMA-UART-Logic-Analyzer-with-Triggered-Capture/actions/workflows/host-tests.yml)
[![Platform](https://img.shields.io/badge/platform-RP2040-blue.svg)](https://www.raspberrypi.com/products/raspberry-pi-pico/)
[![Language](https://img.shields.io/badge/firmware-C%2FC%2B%2B-informational.svg)](https://www.raspberrypi.com/documentation/microcontrollers/c_sdk.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A compact embedded debugging instrument for capturing digital UART TX waveforms with RP2040 PIO and DMA, streaming binary samples to a host over USB CDC, decoding UART frames in Python, and exporting decoded CSV / waveform VCD. Firmware capture uses a bounded buffer and an edge-trigger option; host-side protocol logic and synthetic captures are testable without a Pico attached.

> **Scope / validation note:** host decoder and packet-format tests run in CI. Firmware compilation requires the Raspberry Pi Pico SDK. Real capture timing, USB throughput, and electrical signal capture still require validation on a physical RP2040 board. This instrument is a diagnostic aid, not a certified protocol analyzer.

## Highlights

- PIO samples a GPIO input at a configurable firmware clock divisor.
- DMA transfers PIO FIFO words into a fixed-size sample buffer.
- Immediate or edge-triggered capture modes.
- USB CDC control/transfer protocol with versioned capture packet header.
- Python host client, UART decoder, CSV export, and VCD export.
- Host-side unit tests with synthetic UART waveforms and malformed packet cases.
- Hardware wiring, build instructions, limitations, and validation checklist.

## System architecture

```text
Target UART TX (3.3 V logic) -> GPIO input -> PIO sampler -> RX FIFO -> DMA
                                                           |
                                                           v
                                                   Capture RAM buffer
                                                           |
                                                           v
                                              USB CDC binary capture packet
                                                           |
                                                           v
                                                  Python host application
                                                           |
                                  +------------------------+-------------------+
                                  v                        v                   v
                              UART decode              CSV export           VCD export
```

## Hardware

- Raspberry Pi Pico / compatible RP2040 board
- USB data cable
- Target MCU/UART transmitter
- Optional level shifter for targets that are not 3.3 V compatible

Connect target UART **TX** to the selected input GPIO and connect grounds. The RP2040 GPIO is not 5 V tolerant; use a proper level shifter when required. Do not connect unknown signals until their voltage range is confirmed.

See [hardware setup](docs/hardware_setup.md) for details.

## Repository layout

```text
firmware/
  CMakeLists.txt
  src/main.c
  src/capture.c
  src/capture.h
  pio/uart_sampler.pio
host/
  logic_capture.py
  uart_decoder.py
  export_vcd.py
  protocol.py
tests/
  test_uart_decoder.py
  test_protocol.py
examples/
  sample_capture.json
  sample_decoded.csv
docs/
  architecture.md
  hardware_setup.md
  protocol.md
  validation.md
.github/workflows/host-tests.yml
CMakeLists.txt
Makefile
LICENSE
```

## Build firmware

Install the Raspberry Pi Pico SDK and toolchain using the [official Pico SDK documentation](https://github.com/raspberrypi/pico-sdk). Set `PICO_SDK_PATH` to the SDK root.

```sh
cmake -S . -B build -DPICO_SDK_PATH="$PICO_SDK_PATH"
cmake --build build
```

The build produces a UF2 for the Pico bootloader workflow. Hold BOOTSEL while connecting the board, then copy the UF2 to the mounted drive.

Firmware compile status depends on the Pico SDK and toolchain versions installed on your build host. The CI workflow in this repository covers the portable Python host utilities.

## Host utilities

Python 3.10+ is recommended. No third-party packages are needed for decoding synthetic JSON captures.

```sh
python3 host/logic_capture.py --input examples/sample_capture.json --baud 115200 --csv decoded.csv
python3 host/logic_capture.py --input examples/sample_capture.json --baud 115200 --vcd waveform.vcd
python3 -m unittest discover -s tests -v
```

`sample_capture.json` contains uniformly sampled digital values and sampling rate metadata. The host tools can decode it without the RP2040 hardware. For live use, capture the raw USB CDC byte stream to a file and pass that file to the decoder; the host extracts a versioned `ULAC` packet from any preceding text banner. A future improvement is an interactive PySerial capture client that sends commands and saves packet boundaries automatically.

## UART decoder assumptions

- UART idle is logic high.
- A falling edge marks a candidate start bit.
- Configurable baud rate, data bits, parity, and stop bits are supported by the host decoder.
- The sample rate should be several times the configured baud rate; higher oversampling improves timing tolerance.
- This first version decodes samples from a single digital input and does not provide analog thresholding or multi-channel correlation. Edge trigger currently gates the start of capture; circular pre-trigger history is not implemented.

## Performance and limitations

- Sampling rate and buffer capacity must be chosen together; buffer size bounds the capture duration.
- General USB host scheduling may add transfer latency; timestamps represent sample indices/rate rather than host arrival time.
- This firmware is intended for observing UART TX logic, not driving outputs or replacing production safety/debug equipment.
- Actual maximum stable sampling rate and loss-free USB transfer rate must be measured on the chosen board and target configuration.

## Presentation demo

1. Build and flash the firmware.
2. Connect a UART TX source using safe 3.3 V logic levels.
3. Capture a short known message such as `Hello\r\n`.
4. Transfer the capture to the host application.
5. Decode bytes and export CSV/VCD.
6. Compare the decoded bytes to the transmitter's known payload and keep the log/screenshot with the project report.

## Test

```sh
make test
```

Tests verify packet parsing, UART start/data/stop sampling logic, parity and framing handling, and output generation using synthetic test fixtures. Host tests do not validate physical GPIO timing or firmware DMA timing.

## Portfolio talking points

- Why use PIO rather than an interrupt per sample?
- What work does DMA remove from the CPU?
- How do sample rate and capture capacity determine time resolution and duration?
- How does the decoder sample near the centre of each UART bit?
- What changes are needed for multiple channels or pre-trigger ring-buffer capture?
- Which performance claims require hardware measurements?

## License

MIT — see [LICENSE](LICENSE).
