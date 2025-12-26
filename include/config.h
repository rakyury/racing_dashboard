#pragma once

// Racing Dashboard - Global Configuration
// Target: STM32H7B3 + RVT70HSSNWN00 Display

// ============================================================================
// Display Configuration
// ============================================================================
#ifndef DISPLAY_WIDTH
#define DISPLAY_WIDTH 1024
#endif

#ifndef DISPLAY_HEIGHT
#define DISPLAY_HEIGHT 600
#endif

#define DISPLAY_DPI 150
#define DISPLAY_REFRESH_RATE 60
#define DISPLAY_BRIGHTNESS_MAX 700  // RVT70HSSNWN00 max nits

// ============================================================================
// Hardware Pins (STM32H7B3)
// ============================================================================
// LTDC (Display Controller)
#define LTDC_HSYNC_PIN PE15
#define LTDC_VSYNC_PIN PE13
#define LTDC_CLK_PIN PE14
#define LTDC_DE_PIN PE12

// Touch Controller (I2C)
#define TOUCH_I2C_SDA PB7
#define TOUCH_I2C_SCL PB6
#define TOUCH_INT_PIN PH2

// CAN Bus
#define CAN1_RX_PIN PA11
#define CAN1_TX_PIN PA12
#define CAN2_RX_PIN PB5
#define CAN2_TX_PIN PB13

// GPS (UART)
#define GPS_UART_RX PD2
#define GPS_UART_TX PC12
#define GPS_PPS_PIN PG6

// SD Card (SDMMC)
#define SD_D0_PIN PC8
#define SD_D1_PIN PC9
#define SD_D2_PIN PC10
#define SD_D3_PIN PC11
#define SD_CLK_PIN PC12
#define SD_CMD_PIN PD2

// Backlight PWM
#define BACKLIGHT_PWM_PIN PA0
#define BACKLIGHT_PWM_CHANNEL TIM2
#define BACKLIGHT_PWM_FREQ 10000  // 10 kHz

// Ambient Light Sensor (I2C)
#define ALS_I2C_ADDR 0x10

// ============================================================================
// Signal Bus Configuration
// ============================================================================
#define SIGNAL_BUS_MAX_NUMERIC 64
#define SIGNAL_BUS_MAX_DIGITAL 32
#define SIGNAL_BUS_STALE_THRESHOLD_MS 500

// ============================================================================
// CAN Configuration
// ============================================================================
#define CAN_BAUDRATE 500000
#define CAN_FD_BAUDRATE 5000000
#define CAN_RX_QUEUE_SIZE 256
#define CAN_TX_QUEUE_SIZE 128

// ============================================================================
// GPS Configuration
// ============================================================================
#define GPS_BAUDRATE 115200
#define GPS_UPDATE_RATE_HZ 25

// ============================================================================
// Data Logger Configuration
// ============================================================================
#define LOGGER_BUFFER_SIZE_KB 128
#define LOGGER_SAMPLE_RATE_HZ 200
#define LOGGER_MAX_FILE_SIZE_MB 100
#define LOGGER_ROTATION_ENABLED true

// ============================================================================
// Performance Settings
// ============================================================================
#define MAIN_LOOP_FREQUENCY_HZ 60
#define CAN_POLL_FREQUENCY_HZ 200
#define ADC_SAMPLE_FREQUENCY_HZ 1000

// ============================================================================
// Memory Configuration
// ============================================================================
#define FRAMEBUFFER_SIZE (DISPLAY_WIDTH * DISPLAY_HEIGHT * 3)  // RGB888
#define SDRAM_BASE_ADDRESS 0xD0000000
#define SDRAM_SIZE (32 * 1024 * 1024)  // 32 MB

// ============================================================================
// Feature Flags
// ============================================================================
#ifndef ENABLE_ADVANCED_LOGGING
#define ENABLE_ADVANCED_LOGGING 1
#endif

#ifndef ENABLE_LAP_TIMER
#define ENABLE_LAP_TIMER 1
#endif

#ifndef ENABLE_CAN_SECURITY
#define ENABLE_CAN_SECURITY 1
#endif

#ifndef ENABLE_CAMERA_MANAGER
#define ENABLE_CAMERA_MANAGER 1
#endif

#ifndef ENABLE_VOICE_ALERTS
#define ENABLE_VOICE_ALERTS 1
#endif

#define ENABLE_OTA_UPDATES 1
#define ENABLE_WIFI_CONFIG 1
#define ENABLE_AUTO_BRIGHTNESS 1
#define ENABLE_THEME_MANAGER 1

// ============================================================================
// Debug Settings
// ============================================================================
#ifndef DEBUG_SERIAL_BAUDRATE
#define DEBUG_SERIAL_BAUDRATE 115200
#endif

#ifdef DEBUG
#define DEBUG_LOG_LEVEL 3  // 0=None, 1=Error, 2=Warning, 3=Info, 4=Verbose
#else
#define DEBUG_LOG_LEVEL 1
#endif

// ============================================================================
// Version Information
// ============================================================================
#define FIRMWARE_VERSION_MAJOR 2
#define FIRMWARE_VERSION_MINOR 0
#define FIRMWARE_VERSION_PATCH 0
#define FIRMWARE_BUILD_DATE __DATE__
#define FIRMWARE_BUILD_TIME __TIME__
