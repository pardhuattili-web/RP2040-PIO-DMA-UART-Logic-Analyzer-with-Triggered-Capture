#include "capture.h"

#include "hardware/clocks.h"
#include "hardware/dma.h"
#include "hardware/pio.h"
#include "pico/stdlib.h"
#include "uart_sampler.pio.h"

#include <string.h>

static PIO capture_pio = pio0;
static uint capture_sm;
static int capture_dma = -1;
static uint capture_offset;
static uint capture_pin;
static uint32_t capture_rate;
static bool capture_ready;

bool capture_init(uint gpio_pin, uint32_t sample_rate_hz)
{
    pio_sm_config c;
    float divider;
    if (gpio_pin >= 30U || sample_rate_hz == 0U) return false;
    capture_pin = gpio_pin;
    if (!pio_can_add_program(capture_pio, &uart_sampler_program)) return false;
    capture_offset = pio_add_program(capture_pio, &uart_sampler_program);
    capture_sm = pio_claim_unused_sm(capture_pio, true);
    c = uart_sampler_program_get_default_config(capture_offset);
    sm_config_set_in_pins(&c, capture_pin);
    sm_config_set_in_shift(&c, true, true, 32);
    sm_config_set_fifo_join(&c, PIO_FIFO_JOIN_RX);
    divider = (float)clock_get_hz(clk_sys) / (float)sample_rate_hz;
    if (divider < 1.0f) divider = 1.0f;
    sm_config_set_clkdiv(&c, divider);
    capture_rate = (uint32_t)((float)clock_get_hz(clk_sys) / divider);
    pio_gpio_init(capture_pio, capture_pin);
    pio_sm_set_consecutive_pindirs(capture_pio, capture_sm, capture_pin, 1, false);
    pio_sm_init(capture_pio, capture_sm, capture_offset, &c);
    capture_dma = dma_claim_unused_channel(true);
    capture_ready = true;
    pio_sm_set_enabled(capture_pio, capture_sm, false);
    return true;
}

static bool wait_for_falling_edge(uint32_t timeout_ms)
{
    uint32_t start = to_ms_since_boot(get_absolute_time());
    bool previous = gpio_get(capture_pin);
    while ((uint32_t)(to_ms_since_boot(get_absolute_time()) - start) < timeout_ms) {
        bool current = gpio_get(capture_pin);
        if (previous && !current) return true;
        previous = current;
        tight_loop_contents();
    }
    return false;
}

bool capture_run(capture_result_t *result, uint32_t sample_count,
                 capture_trigger_t trigger, uint32_t pretrigger_samples)
{
    dma_channel_config dc;
    static uint32_t words[(CAPTURE_MAX_SAMPLES + 31U) / 32U];
    uint32_t words_needed;
    uint32_t copied = 0U;
    if (!capture_ready || result == NULL || sample_count == 0U ||
        sample_count > CAPTURE_MAX_SAMPLES || pretrigger_samples >= sample_count) return false;

    memset(result, 0, sizeof(*result));
    result->sample_rate_hz = capture_rate;
    result->gpio_pin = (uint8_t)capture_pin;
    result->trigger = trigger;
    // Version 1 gates start on a falling edge; it does not maintain a pre-trigger ring.
    (void)pretrigger_samples;
    if (trigger == CAPTURE_TRIGGER_FALLING_EDGE && !wait_for_falling_edge(5000U)) return false;

    pio_sm_set_enabled(capture_pio, capture_sm, false);
    pio_sm_clear_fifos(capture_pio, capture_sm);
    pio_sm_restart(capture_pio, capture_sm);

    dc = dma_channel_get_default_config((uint)capture_dma);
    channel_config_set_transfer_data_size(&dc, DMA_SIZE_32);
    channel_config_set_read_increment(&dc, false);
    channel_config_set_write_increment(&dc, true);
    channel_config_set_dreq(&dc, pio_get_dreq(capture_pio, capture_sm, false));

    words_needed = (sample_count + 31U) / 32U;
    dma_channel_configure((uint)capture_dma, &dc, words,
                          &capture_pio->rxf[capture_sm], words_needed, false);
    pio_sm_set_enabled(capture_pio, capture_sm, true);
    dma_start_channel_mask(1u << (uint)capture_dma);
    dma_channel_wait_for_finish_blocking((uint)capture_dma);
    pio_sm_set_enabled(capture_pio, capture_sm, false);

    for (uint32_t w = 0; w < words_needed && copied < sample_count; ++w) {
        for (uint32_t b = 0; b < 32U && copied < sample_count; ++b) {
            result->samples[copied++] = (uint8_t)((words[w] >> b) & 1U);
        }
    }
    result->sample_count = copied;
    result->trigger_index = 0U;
    return copied == sample_count;
}

void capture_deinit(void)
{
    if (!capture_ready) return;
    pio_sm_set_enabled(capture_pio, capture_sm, false);
    dma_channel_unclaim((uint)capture_dma);
    pio_sm_unclaim(capture_pio, capture_sm);
    pio_remove_program(capture_pio, &uart_sampler_program, capture_offset);
    capture_ready = false;
}
