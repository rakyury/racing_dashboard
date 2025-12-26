/**
 * @file main.c
 * @brief Racing Dashboard - Main Application
 *
 * FreeRTOS-based main application with task management.
 */

#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "freertos/timers.h"

#include "rd_types.h"
#include "rd_channel.h"
#include "rd_config.h"
#include "rd_display.h"
#include "rd_can.h"
#include "rd_gps.h"
#include "rd_adc.h"
#include "rd_laptimer.h"

// =============================================================================
// Task Handles
// =============================================================================

static TaskHandle_t s_task_display = NULL;
static TaskHandle_t s_task_can = NULL;
static TaskHandle_t s_task_gps = NULL;
static TaskHandle_t s_task_inputs = NULL;
static TaskHandle_t s_task_laptimer = NULL;
static TaskHandle_t s_task_logger = NULL;

// =============================================================================
// Synchronization
// =============================================================================

static SemaphoreHandle_t s_mutex_channels = NULL;
static SemaphoreHandle_t s_mutex_config = NULL;

// =============================================================================
// System State
// =============================================================================

static struct {
    bool initialized;
    uint32_t uptime_seconds;
    uint32_t tick_ms;
    uint8_t current_screen;
    bool logging_active;
} s_system;

// =============================================================================
// Forward Declarations
// =============================================================================

static void task_display(void *pvParameters);
static void task_can(void *pvParameters);
static void task_gps(void *pvParameters);
static void task_inputs(void *pvParameters);
static void task_laptimer(void *pvParameters);
static void task_logger(void *pvParameters);

static void init_hardware(void);
static void init_peripherals(void);
static void register_system_channels(void);

// =============================================================================
// Timer Callbacks
// =============================================================================

static void uptime_timer_callback(TimerHandle_t xTimer)
{
    (void)xTimer;
    s_system.uptime_seconds++;

    // Update system channel
    RD_Channel_SetValue(RD_CH_SYSTEM_UPTIME, (float)s_system.uptime_seconds);
}

// =============================================================================
// Main Entry Point
// =============================================================================

int main(void)
{
    // Initialize system state
    memset(&s_system, 0, sizeof(s_system));

    // Initialize hardware (clocks, GPIO, etc.)
    init_hardware();

    // Create synchronization primitives
    s_mutex_channels = xSemaphoreCreateMutex();
    s_mutex_config = xSemaphoreCreateMutex();

    if (!s_mutex_channels || !s_mutex_config) {
        // Fatal error - halt
        while (1) {}
    }

    // Initialize core subsystems
    RD_Channel_Init();
    RD_Config_Init();

    // Load configuration from storage
    if (RD_Config_LoadAll() != RD_OK) {
        // Use defaults if load fails
        RD_Config_ResetToDefaults();
    }

    // Register system channels
    register_system_channels();

    // Initialize peripherals based on configuration
    init_peripherals();

    // Create uptime timer (1 second period)
    TimerHandle_t uptime_timer = xTimerCreate(
        "uptime",
        pdMS_TO_TICKS(1000),
        pdTRUE,  // Auto-reload
        NULL,
        uptime_timer_callback
    );

    if (uptime_timer) {
        xTimerStart(uptime_timer, 0);
    }

    // Create tasks
    xTaskCreate(
        task_display,
        "display",
        RD_STACK_DISPLAY,
        NULL,
        RD_PRIO_DISPLAY,
        &s_task_display
    );

    xTaskCreate(
        task_can,
        "can",
        RD_STACK_CAN,
        NULL,
        RD_PRIO_CAN,
        &s_task_can
    );

    xTaskCreate(
        task_gps,
        "gps",
        RD_STACK_GPS,
        NULL,
        RD_PRIO_GPS,
        &s_task_gps
    );

    xTaskCreate(
        task_inputs,
        "inputs",
        RD_STACK_INPUTS,
        NULL,
        RD_PRIO_INPUTS,
        &s_task_inputs
    );

    xTaskCreate(
        task_laptimer,
        "laptimer",
        RD_STACK_LAPTIMER,
        NULL,
        RD_PRIO_LAPTIMER,
        &s_task_laptimer
    );

    xTaskCreate(
        task_logger,
        "logger",
        RD_STACK_LOGGER,
        NULL,
        RD_PRIO_LOGGER,
        &s_task_logger
    );

    s_system.initialized = true;

    // Start scheduler
    vTaskStartScheduler();

    // Should never reach here
    while (1) {}

    return 0;
}

// =============================================================================
// Display Task
// =============================================================================

static void task_display(void *pvParameters)
{
    (void)pvParameters;

    // Initialize display
    RD_Display_Config_t display_cfg = {
        .width = RD_DISPLAY_WIDTH,
        .height = RD_DISPLAY_HEIGHT,
        .color_depth = RD_DISPLAY_COLOR_DEPTH,
        .rotation = RD_DISPLAY_ROTATION_0,
        .brightness = RD_Config_GetSystem()->brightness,
        .use_dma = true,
        .double_buffer = true,
    };

    RD_Display_Init(&display_cfg);
    RD_Display_LVGL_Init();
    RD_Display_PowerOn();

    // Main display loop
    TickType_t last_wake = xTaskGetTickCount();

    while (1) {
        // Process LVGL
        RD_Display_LVGL_Handler();

        // Update display at ~60 FPS
        vTaskDelayUntil(&last_wake, pdMS_TO_TICKS(16));
    }
}

// =============================================================================
// CAN Task
// =============================================================================

static void can_rx_callback(RD_CAN_Interface_t iface, const RD_CAN_Message_t *msg, void *user_data)
{
    (void)user_data;
    (void)iface;

    // Process received CAN message
    // This would typically update channels based on DBC/configuration

    // Example: Extract RPM from a typical ECU message
    if (msg->id == 0x360) {  // Example ECU broadcast ID
        float rpm = RD_CAN_ExtractSignal(msg, 0, 16, RD_CAN_BIG_ENDIAN,
                                         RD_CAN_UNSIGNED, 1.0f, 0.0f);
        RD_Channel_SetValue(RD_CH_ENGINE_RPM, rpm);
    }
}

static void task_can(void *pvParameters)
{
    (void)pvParameters;

    RD_SystemConfig_t *sys_cfg = RD_Config_GetSystem();

    // Initialize CAN1
    if (sys_cfg->can1.enabled) {
        RD_CAN_Config_t can_cfg = {
            .speed = RD_CAN_SPEED_500K,
            .fd_enabled = sys_cfg->can1.fd_enabled,
            .auto_retransmit = true,
        };

        RD_CAN_Init(RD_CAN_1, &can_cfg);
        RD_CAN_RegisterCallback(RD_CAN_1, can_rx_callback, NULL);

        // Add default filter (accept all)
        RD_CAN_Filter_t filter = {
            .id = 0,
            .mask = 0,
            .extended = false,
            .enabled = true,
        };
        RD_CAN_AddFilter(RD_CAN_1, &filter);
        RD_CAN_Start(RD_CAN_1);
    }

    // Initialize CAN2
    if (sys_cfg->can2.enabled) {
        RD_CAN_Config_t can_cfg = {
            .speed = RD_CAN_SPEED_500K,
            .fd_enabled = sys_cfg->can2.fd_enabled,
            .auto_retransmit = true,
        };

        RD_CAN_Init(RD_CAN_2, &can_cfg);
        RD_CAN_RegisterCallback(RD_CAN_2, can_rx_callback, NULL);
        RD_CAN_Start(RD_CAN_2);
    }

    // Update CAN status channels
    RD_Channel_SetValue(RD_CH_SYSTEM_CAN1_STATUS, sys_cfg->can1.enabled ? 1.0f : 0.0f);
    RD_Channel_SetValue(RD_CH_SYSTEM_CAN2_STATUS, sys_cfg->can2.enabled ? 1.0f : 0.0f);

    // Main CAN processing loop
    TickType_t last_wake = xTaskGetTickCount();

    while (1) {
        RD_CAN_Process();
        RD_Channel_Process(10);  // Process logic channels

        vTaskDelayUntil(&last_wake, pdMS_TO_TICKS(10));  // 100 Hz
    }
}

// =============================================================================
// GPS Task
// =============================================================================

static void gps_callback(const RD_GPS_Data_t *data, void *user_data)
{
    (void)user_data;

    // Update GPS channels
    if (data->fix_valid) {
        RD_Channel_SetValue(RD_CH_GPS_LATITUDE, (float)data->position.latitude);
        RD_Channel_SetValue(RD_CH_GPS_LONGITUDE, (float)data->position.longitude);
        RD_Channel_SetValue(RD_CH_GPS_ALTITUDE, data->position.altitude);
        RD_Channel_SetValue(RD_CH_GPS_SPEED, data->velocity.speed * 3.6f);  // Convert to km/h
        RD_Channel_SetValue(RD_CH_GPS_HEADING, data->velocity.heading);
    }
    RD_Channel_SetValue(RD_CH_GPS_SATELLITES, (float)data->satellites_used);
    RD_Channel_SetValue(RD_CH_GPS_HDOP, data->accuracy.hdop);
}

static void task_gps(void *pvParameters)
{
    (void)pvParameters;

    RD_SystemConfig_t *sys_cfg = RD_Config_GetSystem();

    if (!sys_cfg->gps.enabled) {
        // GPS disabled - suspend task
        RD_Channel_SetValue(RD_CH_SYSTEM_GPS_STATUS, 0.0f);
        vTaskSuspend(NULL);
    }

    // Initialize GPS
    RD_GPS_Config_t gps_cfg = {
        .type = RD_GPS_TYPE_UBLOX,
        .update_rate = sys_cfg->gps.update_rate,
        .baudrate = 115200,
        .uart_num = 2,
        .enable_sbas = true,
        .enable_galileo = true,
        .enable_glonass = true,
    };

    RD_GPS_Init(&gps_cfg);
    RD_GPS_RegisterCallback(gps_callback, NULL);

    RD_Channel_SetValue(RD_CH_SYSTEM_GPS_STATUS, 1.0f);

    // Main GPS processing loop
    TickType_t last_wake = xTaskGetTickCount();

    while (1) {
        RD_GPS_Process();

        // Update status
        RD_Channel_SetValue(RD_CH_SYSTEM_GPS_STATUS,
                           RD_GPS_HasFix() ? 2.0f : 1.0f);

        vTaskDelayUntil(&last_wake, pdMS_TO_TICKS(50));  // 20 Hz
    }
}

// =============================================================================
// Inputs Task (ADC and Digital)
// =============================================================================

static void task_inputs(void *pvParameters)
{
    (void)pvParameters;

    // Initialize ADC
    RD_ADC_Config_t adc_cfg = {
        .sample_rate_hz = 1000,
        .oversample_bits = 2,
        .use_dma = true,
    };
    RD_ADC_Init(&adc_cfg);
    RD_ADC_Start();

    // Initialize digital inputs
    RD_DIN_Config_t din_cfg = {
        .enable_pull_up = true,
        .capture_both_edges = true,
    };
    RD_DIN_Init(&din_cfg);

    // Main input processing loop
    TickType_t last_wake = xTaskGetTickCount();

    while (1) {
        // Read ADC values
        for (int ch = 0; ch < RD_ADC_CH_COUNT; ch++) {
            uint16_t raw = RD_ADC_GetAveraged((RD_ADC_Channel_t)ch);
            // Update corresponding channel (if configured)
            // This would be driven by channel configuration
        }

        // Read system values
        float mcu_temp = RD_ADC_GetMCUTemperature();
        RD_Channel_SetValue(RD_CH_SYSTEM_TEMPERATURE, mcu_temp);

        float vref = RD_ADC_GetVrefint();
        RD_Channel_SetValue(RD_CH_SYSTEM_VOLTAGE, vref * 3.3f / 1.21f);  // Approximate

        // Update free memory
        RD_Channel_SetValue(RD_CH_SYSTEM_FREE_MEMORY,
                           (float)xPortGetFreeHeapSize());

        vTaskDelayUntil(&last_wake, pdMS_TO_TICKS(10));  // 100 Hz
    }
}

// =============================================================================
// Lap Timer Task
// =============================================================================

static void lap_callback(const RD_LapData_t *lap, void *user_data)
{
    (void)user_data;

    // Update lap channels
    RD_Channel_SetValue(RD_CH_LAP_LAST_TIME, (float)lap->lap_time_ms / 1000.0f);

    if (lap->best_lap) {
        RD_Channel_SetValue(RD_CH_LAP_BEST_TIME, (float)lap->lap_time_ms / 1000.0f);
    }
}

static void task_laptimer(void *pvParameters)
{
    (void)pvParameters;

    RD_LapTimer_Init();
    RD_LapTimer_SetLapCallback(lap_callback, NULL);

    RD_SystemConfig_t *sys_cfg = RD_Config_GetSystem();

    // Auto-detect track if enabled
    if (sys_cfg->gps.auto_track_detect) {
        // Would load tracks and auto-detect here
    }

    // Main lap timer processing loop
    TickType_t last_wake = xTaskGetTickCount();

    while (1) {
        // Get current GPS data
        RD_GPS_Data_t gps_data;
        if (RD_GPS_GetData(&gps_data) == RD_OK && gps_data.fix_valid) {
            RD_LapTimer_Process(
                gps_data.position.latitude,
                gps_data.position.longitude,
                gps_data.velocity.speed,
                gps_data.velocity.heading
            );
        }

        // Update lap channels
        RD_LapTimer_Status_t status;
        if (RD_LapTimer_GetStatus(&status) == RD_OK) {
            RD_Channel_SetValue(RD_CH_LAP_CURRENT_TIME,
                               (float)status.current_lap_time_ms / 1000.0f);
            RD_Channel_SetValue(RD_CH_LAP_DELTA,
                               (float)status.delta_ms / 1000.0f);
            RD_Channel_SetValue(RD_CH_LAP_NUMBER,
                               (float)status.lap_number);
            RD_Channel_SetValue(RD_CH_LAP_SECTOR,
                               (float)status.current_sector);
            RD_Channel_SetValue(RD_CH_LAP_PREDICTED,
                               (float)status.predicted_lap_ms / 1000.0f);
        }

        vTaskDelayUntil(&last_wake, pdMS_TO_TICKS(50));  // 20 Hz
    }
}

// =============================================================================
// Logger Task
// =============================================================================

static void task_logger(void *pvParameters)
{
    (void)pvParameters;

    RD_SystemConfig_t *sys_cfg = RD_Config_GetSystem();

    if (!sys_cfg->logger.enabled) {
        RD_Channel_SetValue(RD_CH_SYSTEM_LOGGING_STATUS, 0.0f);
        vTaskSuspend(NULL);
    }

    RD_Channel_SetValue(RD_CH_SYSTEM_LOGGING_STATUS, 1.0f);

    // Main logger loop
    TickType_t last_wake = xTaskGetTickCount();
    uint32_t log_period_ms = 1000 / sys_cfg->logger.log_rate;

    while (1) {
        if (s_system.logging_active) {
            // Log all enabled channels to SD card
            // Implementation would write to CSV/binary format

            RD_Channel_SetValue(RD_CH_SYSTEM_LOGGING_STATUS, 2.0f);  // Recording
        }

        vTaskDelayUntil(&last_wake, pdMS_TO_TICKS(log_period_ms));
    }
}

// =============================================================================
// Hardware Initialization
// =============================================================================

static void init_hardware(void)
{
    // Platform-specific hardware initialization
    // - System clocks (480MHz for STM32H743)
    // - GPIO configuration
    // - Interrupt priorities
    // - Memory protection

    // This would be implemented per-platform
}

static void init_peripherals(void)
{
    // Initialize peripherals based on configuration
    // - UART for GPS
    // - SPI for display
    // - I2C for sensors
    // - SDMMC for SD card

    // This would be implemented per-platform
}

// =============================================================================
// System Channels Registration
// =============================================================================

static void register_system_channels(void)
{
    // Register system monitoring channels
    static const RD_ChannelDef_t system_channels[] = {
        {
            .id = RD_CH_SYSTEM_VOLTAGE,
            .name = "System Voltage",
            .units = "V",
            .type = RD_CH_TYPE_SYSTEM,
            .decimals = 1,
            .enabled = true,
        },
        {
            .id = RD_CH_SYSTEM_TEMPERATURE,
            .name = "MCU Temperature",
            .units = "°C",
            .type = RD_CH_TYPE_SYSTEM,
            .decimals = 1,
            .enabled = true,
        },
        {
            .id = RD_CH_SYSTEM_UPTIME,
            .name = "Uptime",
            .units = "s",
            .type = RD_CH_TYPE_SYSTEM,
            .decimals = 0,
            .enabled = true,
        },
        {
            .id = RD_CH_SYSTEM_FREE_MEMORY,
            .name = "Free Memory",
            .units = "B",
            .type = RD_CH_TYPE_SYSTEM,
            .decimals = 0,
            .enabled = true,
        },
        {
            .id = RD_CH_SYSTEM_CAN1_STATUS,
            .name = "CAN1 Status",
            .units = "",
            .type = RD_CH_TYPE_SYSTEM,
            .decimals = 0,
            .enabled = true,
        },
        {
            .id = RD_CH_SYSTEM_CAN2_STATUS,
            .name = "CAN2 Status",
            .units = "",
            .type = RD_CH_TYPE_SYSTEM,
            .decimals = 0,
            .enabled = true,
        },
        {
            .id = RD_CH_SYSTEM_GPS_STATUS,
            .name = "GPS Status",
            .units = "",
            .type = RD_CH_TYPE_SYSTEM,
            .decimals = 0,
            .enabled = true,
        },
        {
            .id = RD_CH_SYSTEM_LOGGING_STATUS,
            .name = "Logging Status",
            .units = "",
            .type = RD_CH_TYPE_SYSTEM,
            .decimals = 0,
            .enabled = true,
        },
    };

    // Register GPS channels
    static const RD_ChannelDef_t gps_channels[] = {
        { .id = RD_CH_GPS_LATITUDE, .name = "GPS Latitude", .units = "°", .type = RD_CH_TYPE_GPS, .decimals = 6, .enabled = true },
        { .id = RD_CH_GPS_LONGITUDE, .name = "GPS Longitude", .units = "°", .type = RD_CH_TYPE_GPS, .decimals = 6, .enabled = true },
        { .id = RD_CH_GPS_ALTITUDE, .name = "GPS Altitude", .units = "m", .type = RD_CH_TYPE_GPS, .decimals = 1, .enabled = true },
        { .id = RD_CH_GPS_SPEED, .name = "GPS Speed", .units = "km/h", .type = RD_CH_TYPE_GPS, .decimals = 1, .enabled = true },
        { .id = RD_CH_GPS_HEADING, .name = "GPS Heading", .units = "°", .type = RD_CH_TYPE_GPS, .decimals = 1, .enabled = true },
        { .id = RD_CH_GPS_SATELLITES, .name = "GPS Satellites", .units = "", .type = RD_CH_TYPE_GPS, .decimals = 0, .enabled = true },
        { .id = RD_CH_GPS_HDOP, .name = "GPS HDOP", .units = "", .type = RD_CH_TYPE_GPS, .decimals = 1, .enabled = true },
    };

    // Register Lap Timer channels
    static const RD_ChannelDef_t lap_channels[] = {
        { .id = RD_CH_LAP_CURRENT_TIME, .name = "Current Lap Time", .units = "s", .type = RD_CH_TYPE_LAPTIMER, .decimals = 3, .enabled = true },
        { .id = RD_CH_LAP_LAST_TIME, .name = "Last Lap Time", .units = "s", .type = RD_CH_TYPE_LAPTIMER, .decimals = 3, .enabled = true },
        { .id = RD_CH_LAP_BEST_TIME, .name = "Best Lap Time", .units = "s", .type = RD_CH_TYPE_LAPTIMER, .decimals = 3, .enabled = true },
        { .id = RD_CH_LAP_DELTA, .name = "Delta", .units = "s", .type = RD_CH_TYPE_LAPTIMER, .decimals = 3, .enabled = true },
        { .id = RD_CH_LAP_NUMBER, .name = "Lap Number", .units = "", .type = RD_CH_TYPE_LAPTIMER, .decimals = 0, .enabled = true },
        { .id = RD_CH_LAP_SECTOR, .name = "Current Sector", .units = "", .type = RD_CH_TYPE_LAPTIMER, .decimals = 0, .enabled = true },
        { .id = RD_CH_LAP_PREDICTED, .name = "Predicted Lap", .units = "s", .type = RD_CH_TYPE_LAPTIMER, .decimals = 3, .enabled = true },
    };

    // Register all channels
    for (size_t i = 0; i < sizeof(system_channels) / sizeof(system_channels[0]); i++) {
        RD_Channel_Register(&system_channels[i]);
    }

    for (size_t i = 0; i < sizeof(gps_channels) / sizeof(gps_channels[0]); i++) {
        RD_Channel_Register(&gps_channels[i]);
    }

    for (size_t i = 0; i < sizeof(lap_channels) / sizeof(lap_channels[0]); i++) {
        RD_Channel_Register(&lap_channels[i]);
    }
}
