/**
 * @file rd_types.h
 * @brief Racing Dashboard - Core Type Definitions
 *
 * Central type definitions used throughout the firmware.
 * Based on PMU_30 architecture.
 */

#ifndef RD_TYPES_H
#define RD_TYPES_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

// =============================================================================
// Version Information
// =============================================================================

#define RD_VERSION_MAJOR    1
#define RD_VERSION_MINOR    0
#define RD_VERSION_PATCH    0
#define RD_VERSION_STRING   "1.0.0"

// =============================================================================
// Channel System - ID Ranges
// =============================================================================

// Physical Inputs (0-99)
#define RD_CHANNEL_ANALOG_INPUT_START      0
#define RD_CHANNEL_ANALOG_INPUT_END        19
#define RD_CHANNEL_DIGITAL_INPUT_START     20
#define RD_CHANNEL_DIGITAL_INPUT_END       39

// CAN Signals (100-299)
#define RD_CHANNEL_CAN_RX_START            100
#define RD_CHANNEL_CAN_RX_END              199
#define RD_CHANNEL_CAN_TX_START            200
#define RD_CHANNEL_CAN_TX_END              249

// Virtual/Calculated (300-499)
#define RD_CHANNEL_VIRTUAL_START           300
#define RD_CHANNEL_VIRTUAL_END             499

// GPS Data (500-549)
#define RD_CHANNEL_GPS_START               500
#define RD_CHANNEL_GPS_END                 549

// Lap Timer (550-599)
#define RD_CHANNEL_LAP_TIMER_START         550
#define RD_CHANNEL_LAP_TIMER_END           599

// System Channels (900-999)
#define RD_CHANNEL_SYSTEM_START            900
#define RD_CHANNEL_SYSTEM_END              999

// =============================================================================
// Channel Types
// =============================================================================

typedef enum {
    RD_CHANNEL_TYPE_NONE = 0,

    // Physical Inputs
    RD_CHANNEL_TYPE_ANALOG_INPUT,       // ADC input (0-5V, 0-12V, etc.)
    RD_CHANNEL_TYPE_DIGITAL_INPUT,      // Digital input (switch, button)
    RD_CHANNEL_TYPE_FREQUENCY_INPUT,    // Frequency/RPM input

    // CAN Bus
    RD_CHANNEL_TYPE_CAN_RX,             // CAN receive signal
    RD_CHANNEL_TYPE_CAN_TX,             // CAN transmit signal

    // GPS
    RD_CHANNEL_TYPE_GPS,                // GPS data channel

    // Virtual/Calculated
    RD_CHANNEL_TYPE_LOGIC,              // Logic function result
    RD_CHANNEL_TYPE_TABLE_2D,           // 2D lookup table
    RD_CHANNEL_TYPE_FILTER,             // Filtered value
    RD_CHANNEL_TYPE_TIMER,              // Virtual timer
    RD_CHANNEL_TYPE_COUNTER,            // Counter

    // Lap Timer
    RD_CHANNEL_TYPE_LAP_TIME,           // Lap time data
    RD_CHANNEL_TYPE_SECTOR_TIME,        // Sector time
    RD_CHANNEL_TYPE_DELTA,              // Delta time

    // System
    RD_CHANNEL_TYPE_SYSTEM,             // System data (voltage, temp, etc.)

    RD_CHANNEL_TYPE_COUNT
} RD_ChannelType_t;

// =============================================================================
// Analog Input Types
// =============================================================================

typedef enum {
    RD_ANALOG_INPUT_0_5V = 0,           // 0-5V range
    RD_ANALOG_INPUT_0_12V,              // 0-12V range (with divider)
    RD_ANALOG_INPUT_THERMISTOR,         // NTC thermistor
    RD_ANALOG_INPUT_PRESSURE_0_5,       // 0.5-4.5V pressure sensor
    RD_ANALOG_INPUT_LINEAR,             // Linear position sensor
    RD_ANALOG_INPUT_CUSTOM              // Custom calibration
} RD_AnalogInputType_t;

// =============================================================================
// Digital Input Types
// =============================================================================

typedef enum {
    RD_DIGITAL_INPUT_ACTIVE_HIGH = 0,   // Active when HIGH
    RD_DIGITAL_INPUT_ACTIVE_LOW,        // Active when LOW (with pullup)
    RD_DIGITAL_INPUT_FREQUENCY,         // Frequency measurement
    RD_DIGITAL_INPUT_PULSE_COUNT        // Pulse counting
} RD_DigitalInputType_t;

// =============================================================================
// CAN Data Types
// =============================================================================

typedef enum {
    RD_CAN_DATA_UNSIGNED = 0,           // Unsigned integer
    RD_CAN_DATA_SIGNED,                 // Signed integer (2's complement)
    RD_CAN_DATA_FLOAT,                  // IEEE 754 float
    RD_CAN_DATA_BCD                     // BCD encoded
} RD_CAN_DataType_t;

typedef enum {
    RD_CAN_BYTE_ORDER_LITTLE = 0,       // Intel byte order
    RD_CAN_BYTE_ORDER_BIG               // Motorola byte order
} RD_CAN_ByteOrder_t;

typedef enum {
    RD_CAN_TIMEOUT_HOLD_LAST = 0,       // Keep last value on timeout
    RD_CAN_TIMEOUT_USE_DEFAULT,         // Use default value
    RD_CAN_TIMEOUT_SET_ZERO             // Set to zero
} RD_CAN_TimeoutBehavior_t;

// =============================================================================
// GPS Data Types
// =============================================================================

typedef enum {
    RD_GPS_LATITUDE = 0,
    RD_GPS_LONGITUDE,
    RD_GPS_ALTITUDE,
    RD_GPS_SPEED,
    RD_GPS_HEADING,
    RD_GPS_SATELLITES,
    RD_GPS_HDOP,
    RD_GPS_FIX_QUALITY,
    RD_GPS_UTC_TIME
} RD_GPS_DataType_t;

// =============================================================================
// Logic Operations
// =============================================================================

typedef enum {
    RD_LOGIC_OP_ADD = 0,
    RD_LOGIC_OP_SUBTRACT,
    RD_LOGIC_OP_MULTIPLY,
    RD_LOGIC_OP_DIVIDE,
    RD_LOGIC_OP_MIN,
    RD_LOGIC_OP_MAX,
    RD_LOGIC_OP_AVERAGE,
    RD_LOGIC_OP_ABS,
    RD_LOGIC_OP_CLAMP,
    RD_LOGIC_OP_SCALE,
    RD_LOGIC_OP_MAP,
    // Comparison
    RD_LOGIC_OP_GREATER,
    RD_LOGIC_OP_LESS,
    RD_LOGIC_OP_EQUAL,
    RD_LOGIC_OP_NOT_EQUAL,
    RD_LOGIC_OP_IN_RANGE,
    // Boolean
    RD_LOGIC_OP_AND,
    RD_LOGIC_OP_OR,
    RD_LOGIC_OP_NOT,
    RD_LOGIC_OP_XOR,
    // Filters
    RD_LOGIC_OP_MOVING_AVG,
    RD_LOGIC_OP_LOW_PASS,
    RD_LOGIC_OP_RATE_OF_CHANGE,
    // Special
    RD_LOGIC_OP_CONDITIONAL,
    RD_LOGIC_OP_HYSTERESIS,
    RD_LOGIC_OP_DEBOUNCE,

    RD_LOGIC_OP_COUNT
} RD_LogicOperation_t;

// =============================================================================
// Display Types
// =============================================================================

typedef enum {
    RD_DISPLAY_PROFILE_1024x600 = 0,
    RD_DISPLAY_PROFILE_1280x480,
    RD_DISPLAY_PROFILE_800x480,
    RD_DISPLAY_PROFILE_480x320,
    RD_DISPLAY_PROFILE_CUSTOM
} RD_DisplayProfile_t;

typedef enum {
    RD_DISPLAY_ORIENTATION_LANDSCAPE = 0,
    RD_DISPLAY_ORIENTATION_PORTRAIT,
    RD_DISPLAY_ORIENTATION_LANDSCAPE_INV,
    RD_DISPLAY_ORIENTATION_PORTRAIT_INV
} RD_DisplayOrientation_t;

// =============================================================================
// Theme Types
// =============================================================================

typedef enum {
    RD_THEME_MOTEC_DARK = 0,
    RD_THEME_MOTEC_LIGHT,
    RD_THEME_ECUMASTER_DARK,
    RD_THEME_ECUMASTER_BLUE,
    RD_THEME_HALTECH_IQ3,
    RD_THEME_HALTECH_PRO,
    RD_THEME_NIGHT_MODE,
    RD_THEME_CUSTOM
} RD_ThemePreset_t;

// =============================================================================
// Error Codes
// =============================================================================

typedef enum {
    RD_OK = 0,
    RD_ERROR_INVALID_PARAM,
    RD_ERROR_NOT_INITIALIZED,
    RD_ERROR_TIMEOUT,
    RD_ERROR_BUSY,
    RD_ERROR_NO_MEMORY,
    RD_ERROR_NOT_FOUND,
    RD_ERROR_CAN_ERROR,
    RD_ERROR_GPS_ERROR,
    RD_ERROR_DISPLAY_ERROR,
    RD_ERROR_STORAGE_ERROR,
    RD_ERROR_CONFIG_ERROR
} RD_Error_t;

// =============================================================================
// Common Structures
// =============================================================================

/**
 * @brief Channel value with metadata
 */
typedef struct {
    float value;                        // Current value
    uint32_t timestamp_ms;              // Last update timestamp
    uint8_t quality;                    // Signal quality (0-100)
    bool valid;                         // Value is valid
} RD_ChannelValue_t;

/**
 * @brief GPS Position
 */
typedef struct {
    double latitude;                    // Degrees
    double longitude;                   // Degrees
    float altitude;                     // Meters
    float speed;                        // km/h
    float heading;                      // Degrees
    uint8_t satellites;                 // Number of satellites
    float hdop;                         // Horizontal dilution
    uint8_t fix_quality;                // 0=None, 1=GPS, 2=DGPS
    uint32_t utc_time;                  // HHMMSS
    uint32_t utc_date;                  // DDMMYY
    bool valid;
} RD_GPS_Position_t;

/**
 * @brief Lap Timer Data
 */
typedef struct {
    uint32_t current_lap_time_ms;       // Current lap time
    uint32_t last_lap_time_ms;          // Previous lap time
    uint32_t best_lap_time_ms;          // Best lap time
    int32_t delta_ms;                   // Delta to best lap
    uint16_t lap_number;                // Current lap number
    uint8_t current_sector;             // Current sector (1-based)
    uint32_t sector_times_ms[10];       // Sector times (max 10)
    bool lap_valid;                     // Current lap is valid
} RD_LapData_t;

/**
 * @brief CAN Message Definition
 */
typedef struct {
    uint32_t id;                        // CAN ID
    uint8_t dlc;                        // Data length code
    bool is_extended;                   // Extended ID
    bool is_fd;                         // CAN FD frame
    uint16_t timeout_ms;                // Timeout in ms (0 = no timeout)
    RD_CAN_TimeoutBehavior_t timeout_behavior;
} RD_CAN_MessageDef_t;

/**
 * @brief CAN Signal Definition
 */
typedef struct {
    uint16_t channel_id;                // Target channel ID
    uint8_t start_bit;                  // Start bit position
    uint8_t bit_length;                 // Number of bits
    RD_CAN_DataType_t data_type;        // Data type
    RD_CAN_ByteOrder_t byte_order;      // Byte order
    float scale;                        // Scale factor
    float offset;                       // Offset
    float min_value;                    // Minimum valid value
    float max_value;                    // Maximum valid value
} RD_CAN_SignalDef_t;

// =============================================================================
// Configuration Limits
// =============================================================================

#define RD_MAX_CHANNELS             1024
#define RD_MAX_CAN_MESSAGES         128
#define RD_MAX_CAN_SIGNALS          256
#define RD_MAX_ANALOG_INPUTS        20
#define RD_MAX_DIGITAL_INPUTS       20
#define RD_MAX_LOGIC_FUNCTIONS      100
#define RD_MAX_SCREENS              10
#define RD_MAX_WIDGETS_PER_SCREEN   50
#define RD_MAX_SECTORS              10
#define RD_MAX_TRACKS               50

// =============================================================================
// Task Priorities (FreeRTOS)
// =============================================================================

#define RD_TASK_PRIORITY_CRITICAL   (configMAX_PRIORITIES - 1)
#define RD_TASK_PRIORITY_HIGH       (configMAX_PRIORITIES - 2)
#define RD_TASK_PRIORITY_MEDIUM     (configMAX_PRIORITIES - 3)
#define RD_TASK_PRIORITY_LOW        (configMAX_PRIORITIES - 4)
#define RD_TASK_PRIORITY_IDLE       1

// Task stack sizes (words)
#define RD_TASK_STACK_CONTROL       512
#define RD_TASK_STACK_CAN           512
#define RD_TASK_STACK_GPS           384
#define RD_TASK_STACK_DISPLAY       1024
#define RD_TASK_STACK_LOGGING       512
#define RD_TASK_STACK_UI            256

#endif // RD_TYPES_H
