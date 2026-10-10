# Hardware setup

## Hardware list

- Raspberry Pi Pico or a compatible RP2040 board
- USB data cable
- Another MCU, USB-UART adapter with 3.3 V logic, or test source for UART TX
- Optional level shifter when the target voltage does not match RP2040 GPIO limits

## Wiring

| Signal source | RP2040 connection |
|---|---|
| Target UART TX | GPIO2 by default |
| Target GND | Pico GND |
| Target RX | Not required for read-only capture |

Firmware default constants live in `firmware/src/main.c`. Change them and rebuild when using another GPIO or sample configuration.

**Voltage safety:** RP2040 GPIO is 3.3 V logic and is not 5 V tolerant. Confirm the output voltage in the target's datasheet or measure it before connecting. Use an appropriate level shifter for 5 V UART output. Never connect mains or other high-energy signals.

## Build and flash

Install the Pico SDK and compiler according to the official SDK setup. Then run:

```sh
export PICO_SDK_PATH="$HOME/pico/pico-sdk"
cmake -S . -B build -DPICO_SDK_PATH="$PICO_SDK_PATH"
cmake --build build
```

Put the Pico into BOOTSEL mode, connect over USB, and copy the generated UF2 to the RPI-RP2 volume.

## Capture flow

1. Open the board's USB CDC serial interface in a terminal or host client.
2. Send `help\n` to inspect firmware commands.
3. Send `capture immediate\n` for an immediate sample window or `capture edge\n` to wait for a falling edge.
4. The firmware sends a binary ULAC packet. Do not send binary capture data through a terminal that assumes text.
5. Save the packet as a binary file and decode it using `host/logic_capture.py --input capture.bin --baud 115200 --csv output.csv --vcd output.vcd`.

The initial CLI is intentionally minimal. A production host client should frame the serial stream, distinguish textual status from the binary packet, and handle partial USB reads.

## First bench test

Start with a known 3.3 V UART transmitter at 9,600 or 115,200 baud, sending a repeating byte such as 0x55. Check that the resulting decoded bytes and waveform transitions match the source. Repeat at multiple rates and log any lost, corrupted, or incomplete captures.
