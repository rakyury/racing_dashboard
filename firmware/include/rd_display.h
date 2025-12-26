/**
 * @file rd_display.h
 * @brief Racing Dashboard - Display Interface
 *
 * LVGL-based display driver with double buffering and DMA support.
 */

#ifndef RD_DISPLAY_H
#define RD_DISPLAY_H

#include "rd_types.h"

// =============================================================================
// Display Configuration
// =============================================================================

// Default display parameters (customize for your hardware)
#define RD_DISPLAY_WIDTH        800
#define RD_DISPLAY_HEIGHT       480
#define RD_DISPLAY_COLOR_DEPTH  16      // RGB565
#define RD_DISPLAY_DPI          150

// Display orientation
typedef enum {
    RD_DISPLAY_ROTATION_0 = 0,
    RD_DISPLAY_ROTATION_90,
    RD_DISPLAY_ROTATION_180,
    RD_DISPLAY_ROTATION_270,
} RD_Display_Rotation_t;

// Display type
typedef enum {
    RD_DISPLAY_TYPE_IPS = 0,            // IPS LCD
    RD_DISPLAY_TYPE_TN,                 // TN LCD
    RD_DISPLAY_TYPE_OLED,               // OLED
    RD_DISPLAY_TYPE_AMOLED,             // AMOLED
} RD_Display_Type_t;

// =============================================================================
// Display Configuration Structure
// =============================================================================

/**
 * @brief Display hardware configuration
 */
typedef struct {
    uint16_t width;                     // Display width in pixels
    uint16_t height;                    // Display height in pixels
    uint8_t color_depth;                // Color depth (16 or 24)
    RD_Display_Rotation_t rotation;     // Display rotation
    RD_Display_Type_t type;             // Display type
    uint8_t brightness;                 // Initial brightness (0-100)
    bool use_dma;                       // Use DMA for transfers
    bool double_buffer;                 // Enable double buffering
} RD_Display_Config_t;

/**
 * @brief Display status
 */
typedef struct {
    bool initialized;                   // Display initialized
    bool powered;                       // Display powered on
    uint8_t brightness;                 // Current brightness
    uint32_t fps;                       // Current frames per second
    uint32_t frame_count;               // Total frames rendered
    uint32_t render_time_us;            // Last render time
} RD_Display_Status_t;

// =============================================================================
// Color Utilities
// =============================================================================

// RGB565 color from components
#define RD_RGB565(r, g, b) (((r & 0xF8) << 8) | ((g & 0xFC) << 3) | ((b & 0xF8) >> 3))

// Common colors (RGB565)
#define RD_COLOR_BLACK          0x0000
#define RD_COLOR_WHITE          0xFFFF
#define RD_COLOR_RED            0xF800
#define RD_COLOR_GREEN          0x07E0
#define RD_COLOR_BLUE           0x001F
#define RD_COLOR_YELLOW         0xFFE0
#define RD_COLOR_CYAN           0x07FF
#define RD_COLOR_MAGENTA        0xF81F
#define RD_COLOR_ORANGE         0xFC00
#define RD_COLOR_GRAY           0x7BEF
#define RD_COLOR_DARK_GRAY      0x39E7
#define RD_COLOR_LIGHT_GRAY     0xC618

// Racing colors
#define RD_COLOR_RACING_RED     0xD800
#define RD_COLOR_RACING_GREEN   0x0600
#define RD_COLOR_RACING_BLUE    0x001D
#define RD_COLOR_WARNING        0xFBE0
#define RD_COLOR_DANGER         0xF800
#define RD_COLOR_OK             0x07E0

// =============================================================================
// Public API
// =============================================================================

/**
 * @brief Initialize display
 * @param config Display configuration
 * @return RD_OK on success
 */
RD_Error_t RD_Display_Init(const RD_Display_Config_t *config);

/**
 * @brief Deinitialize display
 */
void RD_Display_Deinit(void);

/**
 * @brief Power on display
 * @return RD_OK on success
 */
RD_Error_t RD_Display_PowerOn(void);

/**
 * @brief Power off display
 */
void RD_Display_PowerOff(void);

/**
 * @brief Set display brightness
 * @param brightness Brightness level (0-100)
 * @return RD_OK on success
 */
RD_Error_t RD_Display_SetBrightness(uint8_t brightness);

/**
 * @brief Get current brightness
 * @return Current brightness (0-100)
 */
uint8_t RD_Display_GetBrightness(void);

/**
 * @brief Set display rotation
 * @param rotation Rotation setting
 * @return RD_OK on success
 */
RD_Error_t RD_Display_SetRotation(RD_Display_Rotation_t rotation);

/**
 * @brief Get display width
 * @return Width in pixels
 */
uint16_t RD_Display_GetWidth(void);

/**
 * @brief Get display height
 * @return Height in pixels
 */
uint16_t RD_Display_GetHeight(void);

/**
 * @brief Get display status
 * @param status Output status structure
 * @return RD_OK on success
 */
RD_Error_t RD_Display_GetStatus(RD_Display_Status_t *status);

/**
 * @brief Flush display buffer (call from LVGL flush callback)
 * @param x1 Left coordinate
 * @param y1 Top coordinate
 * @param x2 Right coordinate
 * @param y2 Bottom coordinate
 * @param color_p Color buffer
 */
void RD_Display_Flush(int32_t x1, int32_t y1, int32_t x2, int32_t y2, uint16_t *color_p);

/**
 * @brief Wait for flush to complete
 */
void RD_Display_WaitFlush(void);

/**
 * @brief Check if display is ready for next flush
 * @return true if ready
 */
bool RD_Display_IsReady(void);

// =============================================================================
// LVGL Integration
// =============================================================================

/**
 * @brief Initialize LVGL library
 * @return RD_OK on success
 */
RD_Error_t RD_Display_LVGL_Init(void);

/**
 * @brief LVGL tick handler (call from timer interrupt)
 * @param ms Milliseconds since last call
 */
void RD_Display_LVGL_Tick(uint32_t ms);

/**
 * @brief LVGL task handler (call from main loop)
 */
void RD_Display_LVGL_Handler(void);

/**
 * @brief Get LVGL display object
 * @return LVGL display driver pointer
 */
void* RD_Display_GetLVGL(void);

// =============================================================================
// Touch Input (if available)
// =============================================================================

/**
 * @brief Touch point structure
 */
typedef struct {
    int16_t x;                          // X coordinate
    int16_t y;                          // Y coordinate
    bool pressed;                       // Touch pressed
} RD_Touch_Point_t;

/**
 * @brief Initialize touch controller
 * @return RD_OK on success
 */
RD_Error_t RD_Touch_Init(void);

/**
 * @brief Read touch point
 * @param point Output touch point
 * @return RD_OK if touch detected
 */
RD_Error_t RD_Touch_Read(RD_Touch_Point_t *point);

/**
 * @brief Calibrate touch
 * @return RD_OK on success
 */
RD_Error_t RD_Touch_Calibrate(void);

// =============================================================================
// Backlight Control
// =============================================================================

/**
 * @brief Set backlight PWM frequency
 * @param freq_hz Frequency in Hz
 */
void RD_Backlight_SetFrequency(uint32_t freq_hz);

/**
 * @brief Enable automatic brightness control
 * @param enabled Enable state
 * @param ambient_channel ADC channel for ambient light sensor
 */
void RD_Backlight_SetAuto(bool enabled, uint8_t ambient_channel);

/**
 * @brief Set brightness limits for auto mode
 * @param min_brightness Minimum brightness (0-100)
 * @param max_brightness Maximum brightness (0-100)
 */
void RD_Backlight_SetAutoLimits(uint8_t min_brightness, uint8_t max_brightness);

#endif // RD_DISPLAY_H
