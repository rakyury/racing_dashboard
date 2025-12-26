/**
 * @file rd_channel.h
 * @brief Racing Dashboard - Universal Channel Abstraction Layer
 *
 * Unified API for all physical and virtual I/O channels.
 * Based on PMU_30 channel system architecture.
 */

#ifndef RD_CHANNEL_H
#define RD_CHANNEL_H

#include "rd_types.h"

// =============================================================================
// Channel Configuration
// =============================================================================

/**
 * @brief Analog Input Channel Configuration
 */
typedef struct {
    RD_AnalogInputType_t input_type;    // Input type
    float scale;                        // Scale factor
    float offset;                       // Offset
    float filter_alpha;                 // Low-pass filter coefficient (0-1)
    uint16_t min_raw;                   // Minimum raw ADC value
    uint16_t max_raw;                   // Maximum raw ADC value
    float min_value;                    // Minimum scaled value
    float max_value;                    // Maximum scaled value
    // Thermistor specific
    float thermistor_beta;              // Beta coefficient
    float thermistor_r25;               // Resistance at 25C
    float thermistor_pullup;            // Pullup resistor value
} RD_AnalogInputConfig_t;

/**
 * @brief Digital Input Channel Configuration
 */
typedef struct {
    RD_DigitalInputType_t input_type;   // Input type
    bool inverted;                      // Invert logic
    uint16_t debounce_ms;               // Debounce time in ms
    // Frequency specific
    float pulses_per_unit;              // Pulses per revolution/meter/etc
    float min_frequency_hz;             // Minimum valid frequency
    float max_frequency_hz;             // Maximum valid frequency
} RD_DigitalInputConfig_t;

/**
 * @brief CAN RX Channel Configuration
 */
typedef struct {
    uint32_t message_id;                // CAN message ID
    uint8_t start_bit;                  // Start bit position
    uint8_t bit_length;                 // Number of bits
    RD_CAN_DataType_t data_type;        // Data type
    RD_CAN_ByteOrder_t byte_order;      // Byte order
    float scale;                        // Scale factor
    float offset;                       // Offset
    uint16_t timeout_ms;                // Timeout
    RD_CAN_TimeoutBehavior_t timeout_behavior;
    float default_value;                // Default value on timeout
} RD_CAN_RxConfig_t;

/**
 * @brief Logic Function Channel Configuration
 */
typedef struct {
    RD_LogicOperation_t operation;      // Logic operation
    uint16_t input_channels[4];         // Input channel IDs (up to 4)
    uint8_t input_count;                // Number of inputs
    float parameters[4];                // Operation parameters
} RD_LogicConfig_t;

/**
 * @brief Channel Definition
 */
typedef struct {
    uint16_t id;                        // Channel ID
    char name[32];                      // Channel name
    char units[8];                      // Units string
    RD_ChannelType_t type;              // Channel type
    uint8_t decimals;                   // Display decimal places
    bool enabled;                       // Channel enabled

    // Type-specific configuration (union to save memory)
    union {
        RD_AnalogInputConfig_t analog;
        RD_DigitalInputConfig_t digital;
        RD_CAN_RxConfig_t can_rx;
        RD_LogicConfig_t logic;
    } config;
} RD_ChannelDef_t;

/**
 * @brief Runtime channel data
 */
typedef struct {
    RD_ChannelValue_t value;            // Current value
    float raw_value;                    // Unfiltered raw value
    uint32_t update_count;              // Update counter
    uint32_t error_count;               // Error counter
} RD_ChannelData_t;

// =============================================================================
// Public API
// =============================================================================

/**
 * @brief Initialize channel system
 * @return RD_OK on success
 */
RD_Error_t RD_Channel_Init(void);

/**
 * @brief Deinitialize channel system
 */
void RD_Channel_Deinit(void);

/**
 * @brief Register a channel definition
 * @param def Channel definition
 * @return RD_OK on success
 */
RD_Error_t RD_Channel_Register(const RD_ChannelDef_t *def);

/**
 * @brief Unregister a channel
 * @param channel_id Channel ID to unregister
 * @return RD_OK on success
 */
RD_Error_t RD_Channel_Unregister(uint16_t channel_id);

/**
 * @brief Get channel value
 * @param channel_id Channel ID
 * @return Current value (NaN if invalid)
 */
float RD_Channel_GetValue(uint16_t channel_id);

/**
 * @brief Get channel value with metadata
 * @param channel_id Channel ID
 * @param value Output value structure
 * @return RD_OK on success
 */
RD_Error_t RD_Channel_GetValueEx(uint16_t channel_id, RD_ChannelValue_t *value);

/**
 * @brief Set channel value (for writable channels)
 * @param channel_id Channel ID
 * @param value Value to set
 * @return RD_OK on success
 */
RD_Error_t RD_Channel_SetValue(uint16_t channel_id, float value);

/**
 * @brief Update channel from raw input
 * @param channel_id Channel ID
 * @param raw_value Raw input value
 * @return RD_OK on success
 */
RD_Error_t RD_Channel_UpdateRaw(uint16_t channel_id, uint32_t raw_value);

/**
 * @brief Check if channel exists
 * @param channel_id Channel ID
 * @return true if channel exists
 */
bool RD_Channel_Exists(uint16_t channel_id);

/**
 * @brief Check if channel value is valid
 * @param channel_id Channel ID
 * @return true if value is valid
 */
bool RD_Channel_IsValid(uint16_t channel_id);

/**
 * @brief Get channel definition
 * @param channel_id Channel ID
 * @return Pointer to definition or NULL
 */
const RD_ChannelDef_t* RD_Channel_GetDef(uint16_t channel_id);

/**
 * @brief Get channel name
 * @param channel_id Channel ID
 * @return Channel name or "Unknown"
 */
const char* RD_Channel_GetName(uint16_t channel_id);

/**
 * @brief Get channel units
 * @param channel_id Channel ID
 * @return Units string or empty string
 */
const char* RD_Channel_GetUnits(uint16_t channel_id);

/**
 * @brief Find channel by name
 * @param name Channel name
 * @return Channel ID or 0xFFFF if not found
 */
uint16_t RD_Channel_FindByName(const char *name);

/**
 * @brief Process all channels (called from main loop)
 * @param delta_ms Time since last call in ms
 */
void RD_Channel_Process(uint32_t delta_ms);

/**
 * @brief Get number of registered channels
 * @return Channel count
 */
uint16_t RD_Channel_GetCount(void);

/**
 * @brief Iterate over all channels
 * @param callback Callback function (return false to stop iteration)
 * @param user_data User data passed to callback
 */
void RD_Channel_ForEach(bool (*callback)(const RD_ChannelDef_t *def, void *user_data), void *user_data);

// =============================================================================
// System Channels (Pre-defined)
// =============================================================================

// System channel IDs
#define RD_CH_SYSTEM_VOLTAGE        900     // Battery/supply voltage
#define RD_CH_SYSTEM_TEMPERATURE    901     // MCU temperature
#define RD_CH_SYSTEM_UPTIME         902     // System uptime (seconds)
#define RD_CH_SYSTEM_FREE_MEMORY    903     // Free heap memory
#define RD_CH_SYSTEM_CPU_LOAD       904     // CPU load percentage
#define RD_CH_SYSTEM_CAN1_STATUS    905     // CAN1 bus status
#define RD_CH_SYSTEM_CAN2_STATUS    906     // CAN2 bus status
#define RD_CH_SYSTEM_GPS_STATUS     907     // GPS status
#define RD_CH_SYSTEM_SD_STATUS      908     // SD card status
#define RD_CH_SYSTEM_LOGGING_STATUS 909     // Data logging status

// GPS channel IDs
#define RD_CH_GPS_LATITUDE          500
#define RD_CH_GPS_LONGITUDE         501
#define RD_CH_GPS_ALTITUDE          502
#define RD_CH_GPS_SPEED             503
#define RD_CH_GPS_HEADING           504
#define RD_CH_GPS_SATELLITES        505
#define RD_CH_GPS_HDOP              506

// Lap timer channel IDs
#define RD_CH_LAP_CURRENT_TIME      550
#define RD_CH_LAP_LAST_TIME         551
#define RD_CH_LAP_BEST_TIME         552
#define RD_CH_LAP_DELTA             553
#define RD_CH_LAP_NUMBER            554
#define RD_CH_LAP_SECTOR            555
#define RD_CH_LAP_SECTOR1           556
#define RD_CH_LAP_SECTOR2           557
#define RD_CH_LAP_SECTOR3           558
#define RD_CH_LAP_PREDICTED         559

// Common ECU channels (typical CAN mapping)
#define RD_CH_ENGINE_RPM            100
#define RD_CH_VEHICLE_SPEED         101
#define RD_CH_THROTTLE_POSITION     102
#define RD_CH_COOLANT_TEMP          103
#define RD_CH_OIL_TEMP              104
#define RD_CH_OIL_PRESSURE          105
#define RD_CH_FUEL_PRESSURE         106
#define RD_CH_BOOST_PRESSURE        107
#define RD_CH_AFR                   108
#define RD_CH_IGNITION_ADVANCE      109
#define RD_CH_GEAR                  110
#define RD_CH_FUEL_LEVEL            111
#define RD_CH_BATTERY_VOLTAGE       112
#define RD_CH_IAT                   113
#define RD_CH_MAP                   114
#define RD_CH_EGT_1                 115
#define RD_CH_EGT_2                 116
#define RD_CH_BRAKE_PRESSURE        117
#define RD_CH_STEERING_ANGLE        118
#define RD_CH_WHEEL_SPEED_FL        119
#define RD_CH_WHEEL_SPEED_FR        120
#define RD_CH_WHEEL_SPEED_RL        121
#define RD_CH_WHEEL_SPEED_RR        122
#define RD_CH_G_LATERAL             123
#define RD_CH_G_LONGITUDINAL        124
#define RD_CH_YAW_RATE              125

#endif // RD_CHANNEL_H
