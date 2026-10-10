add_executable(uart_logic_analyzer
    src/main.c
    src/capture.c
)
pico_generate_pio_header(uart_logic_analyzer ${CMAKE_CURRENT_LIST_DIR}/pio/uart_sampler.pio)

target_include_directories(uart_logic_analyzer PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}/src
)
target_link_libraries(uart_logic_analyzer
    pico_stdlib
    hardware_pio
    hardware_dma
    hardware_clocks
    tinyusb_device
    tinyusb_board
)
pico_enable_stdio_usb(uart_logic_analyzer 0)
pico_enable_stdio_uart(uart_logic_analyzer 0)
pico_add_extra_outputs(uart_logic_analyzer)
