cmake_minimum_required(VERSION 3.13)

# The Pico SDK import path is supplied either via PICO_SDK_PATH or the environment.
if (DEFINED ENV{PICO_SDK_PATH} AND NOT PICO_SDK_PATH)
    set(PICO_SDK_PATH $ENV{PICO_SDK_PATH})
endif()
if (NOT PICO_SDK_PATH)
    message(FATAL_ERROR "Set PICO_SDK_PATH to your local raspberrypi/pico-sdk checkout.")
endif()

include(${PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(rp2040_uart_logic_analyzer C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

pico_sdk_init()
add_subdirectory(firmware)
