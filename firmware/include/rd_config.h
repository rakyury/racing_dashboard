/**
 * @file rd_config.h
 * @brief Racing Dashboard - Configuration Management
 *
 * JSON-based configuration storage and runtime management.
 */

#ifndef RD_CONFIG_H
#define RD_CONFIG_H

#include "rd_types.h"

// =============================================================================
// Configuration Limits
// =============================================================================

#define RD_CONFIG_MAX_SCREENS       10      // Maximum display screens
#define RD_CONFIG_MAX_WIDGETS       64      // Maximum widgets per screen
#define RD_CONFIG_MAX_CHANNELS      256     // Maximum data channels
#define RD_CONFIG_MAX_NAME_LEN      32      // Maximum name length
#define RD_CONFIG_MAX_PATH_LEN      64      // Maximum file path length

// Configuration file paths
#define RD_CONFIG_FILE_SYSTEM       "/config/system.json"
#define RD_CONFIG_FILE_CHANNELS     "/config/channels.json"
#define RD_CONFIG_FILE_SCREENS      "/config/screens.json"
#define RD_CONFIG_FILE_TRACKS       "/config/tracks.json"

// =============================================================================
// Widget Configuration
// =============================================================================

/**
 * @brief Widget types (must match Python configurator)
 */
typedef enum {
    RD_WIDGET_RPM_GAUGE = 0,
    RD_WIDGET_SPEEDOMETER,
    RD_WIDGET_TACHOMETER,
    RD_WIDGET_FUEL_GAUGE,
    RD_WIDGET_TEMP_GAUGE,
    RD_WIDGET_OIL_GAUGE,
    RD_WIDGET_PRESSURE_GAUGE,
    RD_WIDGET_BOOST_GAUGE,
    RD_WIDGET_WARNING_LIGHT,
    RD_WIDGET_LED_INDICATOR,
    RD_WIDGET_THROTTLE_BAR,
    RD_WIDGET_BRAKE_BAR,
    RD_WIDGET_AFR_BAR,
    RD_WIDGET_LAP_TIMER,
    RD_WIDGET_G_METER,
    RD_WIDGET_DELTA_DISPLAY,
    RD_WIDGET_SECTOR_TIMES,
    RD_WIDGET_BEST_LAP,
    RD_WIDGET_NUMERIC_DISPLAY,
    RD_WIDGET_TEXT,
    RD_WIDGET_IMAGE,
    RD_WIDGET_RECTANGLE,
    RD_WIDGET_LINE,
    RD_WIDGET_COUNT
} RD_WidgetType_t;

/**
 * @brief Widget configuration
 */
typedef struct {
    uint16_t id;                            // Widget ID
    RD_WidgetType_t type;                   // Widget type
    char name[RD_CONFIG_MAX_NAME_LEN];      // Widget name

    // Position and size
    int16_t x;
    int16_t y;
    uint16_t width;
    uint16_t height;

    // Data binding
    uint16_t channel_id;                    // Primary data channel
    uint16_t channel_id_2;                  // Secondary channel (e.g., for delta)

    // Display properties
    uint32_t color_fg;                      // Foreground color
    uint32_t color_bg;                      // Background color
    uint32_t color_warning;                 // Warning color
    uint32_t color_danger;                  // Danger color

    // Value range
    float min_value;
    float max_value;
    float warning_low;
    float warning_high;
    float danger_low;
    float danger_high;

    // Format
    uint8_t decimals;                       // Decimal places
    bool show_units;                        // Show units
    bool show_label;                        // Show label

    // Type-specific
    union {
        struct {
            uint16_t redline;               // Redline RPM
            uint8_t shift_lights;           // Number of shift lights
        } rpm;
        struct {
            bool show_delta;                // Show delta time
            bool auto_reset;                // Auto reset on crossing
        } lap_timer;
        struct {
            char format[16];                // Printf format string
        } numeric;
        struct {
            char text[64];                  // Static text
            uint8_t font_size;              // Font size
        } text;
        struct {
            char path[RD_CONFIG_MAX_PATH_LEN]; // Image path
        } image;
    } specific;

    bool visible;                           // Widget visible
    bool enabled;                           // Widget enabled
} RD_WidgetConfig_t;

/**
 * @brief Screen configuration
 */
typedef struct {
    uint16_t id;                            // Screen ID
    char name[RD_CONFIG_MAX_NAME_LEN];      // Screen name
    uint32_t bg_color;                      // Background color
    char bg_image[RD_CONFIG_MAX_PATH_LEN];  // Background image path

    RD_WidgetConfig_t widgets[RD_CONFIG_MAX_WIDGETS];
    uint8_t widget_count;

    bool enabled;
} RD_ScreenConfig_t;

// =============================================================================
// System Configuration
// =============================================================================

/**
 * @brief System configuration
 */
typedef struct {
    // Display
    uint8_t brightness;                     // Display brightness (0-100)
    uint8_t screen_timeout;                 // Screen timeout in seconds (0 = disabled)
    bool auto_brightness;                   // Auto brightness control
    uint8_t default_screen;                 // Default screen index

    // CAN
    struct {
        bool enabled;
        uint32_t baudrate;
        bool fd_enabled;
    } can1;

    struct {
        bool enabled;
        uint32_t baudrate;
        bool fd_enabled;
    } can2;

    // GPS
    struct {
        bool enabled;
        uint8_t update_rate;                // Update rate in Hz
        bool auto_track_detect;             // Auto detect track
    } gps;

    // Data logger
    struct {
        bool enabled;
        uint8_t log_rate;                   // Log rate in Hz
        bool auto_start;                    // Auto start logging
        uint32_t max_file_size_mb;          // Max file size in MB
    } logger;

    // WiFi
    struct {
        bool ap_enabled;
        char ap_ssid[32];
        char ap_password[32];
        uint8_t ap_channel;
    } wifi;

    // Units
    bool use_metric;                        // Use metric units
    bool use_24h;                           // Use 24-hour time

    // Version
    uint16_t config_version;
} RD_SystemConfig_t;

// =============================================================================
// Public API
// =============================================================================

/**
 * @brief Initialize configuration system
 * @return RD_OK on success
 */
RD_Error_t RD_Config_Init(void);

/**
 * @brief Deinitialize configuration system
 */
void RD_Config_Deinit(void);

/**
 * @brief Load all configuration from storage
 * @return RD_OK on success
 */
RD_Error_t RD_Config_LoadAll(void);

/**
 * @brief Save all configuration to storage
 * @return RD_OK on success
 */
RD_Error_t RD_Config_SaveAll(void);

/**
 * @brief Reset configuration to defaults
 */
void RD_Config_ResetToDefaults(void);

// System Config
/**
 * @brief Get system configuration
 * @return Pointer to system config
 */
RD_SystemConfig_t* RD_Config_GetSystem(void);

/**
 * @brief Save system configuration
 * @return RD_OK on success
 */
RD_Error_t RD_Config_SaveSystem(void);

/**
 * @brief Load system configuration
 * @return RD_OK on success
 */
RD_Error_t RD_Config_LoadSystem(void);

// Screen Config
/**
 * @brief Get screen configuration
 * @param screen_index Screen index
 * @return Pointer to screen config or NULL
 */
RD_ScreenConfig_t* RD_Config_GetScreen(uint8_t screen_index);

/**
 * @brief Get number of screens
 * @return Screen count
 */
uint8_t RD_Config_GetScreenCount(void);

/**
 * @brief Save screens configuration
 * @return RD_OK on success
 */
RD_Error_t RD_Config_SaveScreens(void);

/**
 * @brief Load screens configuration
 * @return RD_OK on success
 */
RD_Error_t RD_Config_LoadScreens(void);

// Channel Config
/**
 * @brief Save channels configuration
 * @return RD_OK on success
 */
RD_Error_t RD_Config_SaveChannels(void);

/**
 * @brief Load channels configuration
 * @return RD_OK on success
 */
RD_Error_t RD_Config_LoadChannels(void);

// =============================================================================
// Configuration Validation
// =============================================================================

/**
 * @brief Validate system configuration
 * @param config Configuration to validate
 * @return RD_OK if valid
 */
RD_Error_t RD_Config_ValidateSystem(const RD_SystemConfig_t *config);

/**
 * @brief Validate screen configuration
 * @param screen Screen to validate
 * @return RD_OK if valid
 */
RD_Error_t RD_Config_ValidateScreen(const RD_ScreenConfig_t *screen);

// =============================================================================
// Configuration Import/Export
// =============================================================================

/**
 * @brief Export configuration to JSON string
 * @param buffer Output buffer
 * @param buffer_size Buffer size
 * @return Number of bytes written or negative on error
 */
int RD_Config_ExportJSON(char *buffer, size_t buffer_size);

/**
 * @brief Import configuration from JSON string
 * @param json JSON string
 * @return RD_OK on success
 */
RD_Error_t RD_Config_ImportJSON(const char *json);

/**
 * @brief Get configuration checksum
 * @return CRC32 checksum
 */
uint32_t RD_Config_GetChecksum(void);

#endif // RD_CONFIG_H
