#ifndef CAPTURE_H
#define CAPTURE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define CAPTURE_MAX_SAMPLES 4096U

typedef enum {
    CAPTURE_TRIGGER_IMMEDIATE = 0,
    CAPTURE_TRIGGER_FALLING_EDGE = 1
} capture_trigger_t;

typedef struct {
    uint32_t sample_rate_hz;
    uint32_t sample_count;
    uint32_t trigger_index;
    uint8_t gpio_pin;
    capture_trigger_t trigger;
    uint8_t samples[CAPTURE_MAX_SAMPLES];
} capture_result_t;

bool capture_init(uint gpio_pin, uint32_t sample_rate_hz);
bool capture_run(capture_result_t *result, uint32_t sample_count,
                 capture_trigger_t trigger, uint32_t pretrigger_samples);
void capture_deinit(void);

#endif
