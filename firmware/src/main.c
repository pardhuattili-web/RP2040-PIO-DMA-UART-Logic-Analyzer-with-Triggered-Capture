#include "capture.h"

#include "pico/stdlib.h"
#include "tusb.h"

#include <stdio.h>
#include <string.h>

#define UART_CAPTURE_GPIO 2U
#define DEFAULT_SAMPLE_RATE_HZ 1000000U
#define DEFAULT_SAMPLE_COUNT 2048U

typedef struct __attribute__((packed)) {
    char magic[4];            // "ULAC"
    uint8_t version;          // 1
    uint8_t flags;            // bit 0 = edge trigger
    uint8_t gpio_pin;
    uint8_t reserved;
    uint32_t sample_rate_hz;
    uint32_t sample_count;
    uint32_t trigger_index;
} capture_packet_header_t;

static capture_result_t capture_result;

static void send_capture(void)
{
    capture_packet_header_t header = {
        .magic = {'U','L','A','C'},
        .version = 1,
        .flags = (uint8_t)(capture_result.trigger == CAPTURE_TRIGGER_FALLING_EDGE),
        .gpio_pin = capture_result.gpio_pin,
        .reserved = 0,
        .sample_rate_hz = capture_result.sample_rate_hz,
        .sample_count = capture_result.sample_count,
        .trigger_index = capture_result.trigger_index
    };
    tud_cdc_write(&header, sizeof(header));
    tud_cdc_write(capture_result.samples, capture_result.sample_count);
    tud_cdc_write_flush();
}

int main(void)
{
    stdio_init_all();
    sleep_ms(1200);
    if (!capture_init(UART_CAPTURE_GPIO, DEFAULT_SAMPLE_RATE_HZ)) {
        printf("ERR capture_init\r\n");
        while (true) tight_loop_contents();
    }

    printf("RP2040 UART Logic Analyzer v1\r\n");
    printf("Commands: capture [immediate|edge], help\r\n");
    while (true) {
        tud_task();
        if (tud_cdc_available()) {
            char command[64] = {0};
            uint32_t n = tud_cdc_read(command, sizeof(command)-1);
            command[n] = '\0';
            if (strncmp(command, "help", 4) == 0) {
                printf("capture immediate | capture edge\r\n");
            } else if (strncmp(command, "capture edge", 12) == 0) {
                if (capture_run(&capture_result, DEFAULT_SAMPLE_COUNT,
                                CAPTURE_TRIGGER_FALLING_EDGE, 0U)) {
                    send_capture();
                } else {
                    printf("ERR edge trigger timeout or capture failure\r\n");
                }
            } else if (strncmp(command, "capture", 7) == 0) {
                if (capture_run(&capture_result, DEFAULT_SAMPLE_COUNT,
                                CAPTURE_TRIGGER_IMMEDIATE, 0U)) {
                    send_capture();
                } else {
                    printf("ERR capture failure\r\n");
                }
            } else if (command[0] != '\0') {
                printf("ERR unknown command\r\n");
            }
        }
        tight_loop_contents();
    }
}
