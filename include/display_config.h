#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @file display_config.h
 * @brief Display configuration and responsive layout management
 *
 * Supports multiple display profiles with automatic widget scaling
 * Target: RVT70HSSNWN00 (1024x600) with fallback to other resolutions
 */

// ============================================================================
// Display Profile Types
// ============================================================================

typedef enum {
    DISPLAY_PROFILE_1024x600_STANDARD,  // RVT70HSSNWN00 (primary)
    DISPLAY_PROFILE_1280x480_ULTRAWIDE, // Original spec
    DISPLAY_PROFILE_800x480_COMPACT,    // 5" displays
    DISPLAY_PROFILE_480x320_MINIMAL,    // 3.5" displays
    DISPLAY_PROFILE_CUSTOM
} DisplayProfile;

typedef enum {
    DISPLAY_ORIENTATION_LANDSCAPE,      // 0°
    DISPLAY_ORIENTATION_PORTRAIT,       // 90°
    DISPLAY_ORIENTATION_LANDSCAPE_INV,  // 180°
    DISPLAY_ORIENTATION_PORTRAIT_INV    // 270°
} DisplayOrientation;

// ============================================================================
// Layout Configuration
// ============================================================================

typedef struct {
    // Grid system for responsive layout
    uint8_t grid_columns;          // Number of columns (typically 12 or 24)
    uint8_t grid_rows;             // Number of rows (typically 8 or 12)
    uint16_t gutter_size;          // Spacing between widgets (px)

    // Widget sizes (optimized for current resolution)
    uint16_t rpm_gauge_diameter;   // Main RPM gauge size
    uint16_t status_pill_width;    // Width of status indicators
    uint16_t status_pill_height;   // Height of status indicators
    uint16_t shift_light_height;   // Shift indicator bar height
    uint16_t alert_ribbon_height;  // Alert banner height

    // Font scaling
    float font_scale_factor;       // Multiplier for base font sizes
    uint8_t font_size_tiny;        // 8-12px
    uint8_t font_size_small;       // 12-16px
    uint8_t font_size_medium;      // 16-24px
    uint8_t font_size_large;       // 24-36px
    uint8_t font_size_huge;        // 48-72px

    // Touch targets
    uint16_t min_touch_target;     // Minimum button size (44-48px recommended)

    // Margins and padding
    uint16_t screen_margin_x;      // Left/right screen margins
    uint16_t screen_margin_y;      // Top/bottom screen margins
    uint16_t widget_padding;       // Internal widget padding
} LayoutConfig;

// ============================================================================
// Display Hardware Configuration
// ============================================================================

typedef struct {
    uint16_t width;                // Horizontal resolution
    uint16_t height;               // Vertical resolution
    uint8_t bits_per_pixel;        // Color depth (16/24/32)
    uint16_t dpi;                  // Dots per inch
    float aspect_ratio;            // Width/height ratio
    uint16_t max_brightness_nits;  // Maximum display brightness

    // Timing parameters (for LTDC configuration)
    uint16_t hsync;
    uint16_t hbp;                  // Horizontal back porch
    uint16_t hfp;                  // Horizontal front porch
    uint16_t vsync;
    uint16_t vbp;                  // Vertical back porch
    uint16_t vfp;                  // Vertical front porch
    uint32_t pixel_clock_khz;      // Pixel clock frequency

    DisplayOrientation orientation;
    LayoutConfig layout;
} DisplayConfig;

// ============================================================================
// Predefined Display Configurations
// ============================================================================

// RVT70HSSNWN00: 7" 1024x600 IPS (Primary target)
extern const DisplayConfig DISPLAY_CONFIG_RVT70;

// Original spec: 7" 1280x480 Ultra-wide
extern const DisplayConfig DISPLAY_CONFIG_ULTRAWIDE;

// Compact: 5" 800x480
extern const DisplayConfig DISPLAY_CONFIG_COMPACT;

// Minimal: 3.5" 480x320
extern const DisplayConfig DISPLAY_CONFIG_MINIMAL;

// ============================================================================
// Public API
// ============================================================================

/**
 * @brief Initialize display configuration system
 * @param profile Display profile to use
 * @return Pointer to active configuration
 */
const DisplayConfig* display_config_init(DisplayProfile profile);

/**
 * @brief Get current display configuration
 * @return Pointer to active configuration
 */
const DisplayConfig* display_config_get_current(void);

/**
 * @brief Change display profile at runtime
 * @param profile New display profile
 * @return true if successfully changed
 */
bool display_config_set_profile(DisplayProfile profile);

/**
 * @brief Set custom display configuration
 * @param config Custom configuration parameters
 * @return true if successfully applied
 */
bool display_config_set_custom(const DisplayConfig *config);

/**
 * @brief Get orientation setting
 * @return Current display orientation
 */
DisplayOrientation display_config_get_orientation(void);

/**
 * @brief Set display orientation
 * @param orientation New orientation (0°, 90°, 180°, 270°)
 * @return true if successfully changed
 */
bool display_config_set_orientation(DisplayOrientation orientation);

/**
 * @brief Calculate scaled widget dimensions
 * @param base_width Base width at 1920x1080 reference
 * @param base_height Base height at 1920x1080 reference
 * @param out_width Calculated width for current display
 * @param out_height Calculated height for current display
 */
void display_config_scale_widget(uint16_t base_width, uint16_t base_height,
                                 uint16_t *out_width, uint16_t *out_height);

/**
 * @brief Get grid cell position
 * @param col Column index (0-based)
 * @param row Row index (0-based)
 * @param out_x X coordinate in pixels
 * @param out_y Y coordinate in pixels
 */
void display_config_grid_to_pixels(uint8_t col, uint8_t row,
                                   uint16_t *out_x, uint16_t *out_y);

/**
 * @brief Get grid cell size
 * @param out_width Cell width in pixels
 * @param out_height Cell height in pixels
 */
void display_config_get_cell_size(uint16_t *out_width, uint16_t *out_height);

/**
 * @brief Check if point is within display bounds
 * @param x X coordinate
 * @param y Y coordinate
 * @return true if point is valid
 */
bool display_config_is_point_valid(uint16_t x, uint16_t y);

/**
 * @brief Get safe area (excluding margins)
 * @param out_x Starting X coordinate
 * @param out_y Starting Y coordinate
 * @param out_width Safe area width
 * @param out_height Safe area height
 */
void display_config_get_safe_area(uint16_t *out_x, uint16_t *out_y,
                                  uint16_t *out_width, uint16_t *out_height);

#ifdef __cplusplus
}
#endif
