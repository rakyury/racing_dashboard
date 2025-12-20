#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @file theme_manager.h
 * @brief Theme and color management system with day/night modes
 *
 * Supports multiple color themes optimized for different racing conditions
 * - Motec Dark (default): Professional dark theme
 * - AIM Sport Light: High-contrast light theme for bright conditions
 * - Rally High-Contrast: Maximum visibility for harsh environments
 * - Night Mode: Red-accent theme to preserve night vision
 * - Endurance: Low-brightness blue theme for long races
 */

// ============================================================================
// Color Definitions
// ============================================================================

typedef struct {
    uint8_t r;
    uint8_t g;
    uint8_t b;
    uint8_t a;  // Alpha channel (0=transparent, 255=opaque)
} Color;

// Helper macros for color creation
#define RGB(r, g, b) ((Color){(r), (g), (b), 255})
#define RGBA(r, g, b, a) ((Color){(r), (g), (b), (a)})
#define HEX_TO_RGB(hex) RGB(((hex) >> 16) & 0xFF, ((hex) >> 8) & 0xFF, (hex) & 0xFF)

// Convert to 16-bit RGB565
#define COLOR_TO_RGB565(c) ((uint16_t)(((c.r & 0xF8) << 8) | ((c.g & 0xFC) << 3) | (c.b >> 3)))

// Convert to 32-bit ARGB8888
#define COLOR_TO_ARGB8888(c) ((uint32_t)((c.a << 24) | (c.r << 16) | (c.g << 8) | c.b))

// ============================================================================
// Theme Structure
// ============================================================================

typedef struct {
    char name[32];              // Theme display name
    char description[64];       // Brief description

    // Base colors
    Color background;           // Primary background
    Color background_secondary; // Secondary backgrounds, cards
    Color surface;              // Elevated surfaces, panels

    // Accent colors
    Color accent;               // Primary accent (shift lights, highlights)
    Color accent_secondary;     // Secondary accent

    // Status colors
    Color success;              // OK, normal range
    Color warning;              // Warning threshold
    Color critical;             // Critical alert, danger
    Color info;                 // Informational elements

    // Text colors
    Color text_primary;         // Main text
    Color text_secondary;       // Secondary text, labels
    Color text_disabled;        // Disabled elements
    Color text_on_accent;       // Text on accent backgrounds

    // UI elements
    Color border;               // Borders, dividers
    Color shadow;               // Shadows, overlays
    Color overlay;              // Modal overlays

    // Gauge-specific colors
    Color rpm_normal;           // RPM gauge (normal range)
    Color rpm_warning;          // RPM gauge (approaching redline)
    Color rpm_redline;          // RPM gauge (redline)
    Color shift_indicator;      // Shift light color

    // Graph colors
    Color graph_line1;          // Primary graph line
    Color graph_line2;          // Secondary graph line
    Color graph_grid;           // Graph grid lines

    // Advanced settings
    float brightness_multiplier; // Global brightness adjustment (0.0-2.0)
    uint8_t contrast;           // Contrast level (0-100)
    uint8_t saturation;         // Color saturation (0-100)
    bool anti_glare_mode;       // Reduce bright whites for sunny conditions
} Theme;

// ============================================================================
// Theme Manager
// ============================================================================

#define MAX_THEMES 16

typedef enum {
    THEME_MOTEC_DARK = 0,
    THEME_AIM_SPORT_LIGHT,
    THEME_RALLY_HIGH_CONTRAST,
    THEME_NIGHT_MODE,
    THEME_ENDURANCE,
    THEME_CUSTOM_1,
    THEME_CUSTOM_2,
    THEME_CUSTOM_3
} ThemePreset;

typedef struct {
    Theme themes[MAX_THEMES];
    size_t theme_count;
    size_t active_theme_idx;

    // Auto night mode
    bool auto_night_mode_enabled;
    uint8_t night_mode_start_hour;  // 0-23
    uint8_t night_mode_end_hour;    // 0-23
    size_t day_theme_idx;
    size_t night_theme_idx;

    // Auto brightness sync
    bool sync_brightness_with_als;  // Adjust theme brightness based on ambient light
} ThemeManager;

// ============================================================================
// Public API
// ============================================================================

/**
 * @brief Initialize theme manager with default themes
 * @param tm ThemeManager instance
 */
void theme_manager_init(ThemeManager *tm);

/**
 * @brief Get active theme
 * @param tm ThemeManager instance
 * @return Pointer to active theme (never NULL)
 */
const Theme* theme_manager_get_active(const ThemeManager *tm);

/**
 * @brief Set active theme by index
 * @param tm ThemeManager instance
 * @param theme_idx Theme index (0-based)
 * @return true if successfully changed
 */
bool theme_manager_set_active(ThemeManager *tm, size_t theme_idx);

/**
 * @brief Set active theme by preset
 * @param tm ThemeManager instance
 * @param preset Theme preset identifier
 * @return true if successfully changed
 */
bool theme_manager_set_preset(ThemeManager *tm, ThemePreset preset);

/**
 * @brief Add custom theme
 * @param tm ThemeManager instance
 * @param theme Theme to add
 * @return Index of added theme, or -1 if full
 */
int theme_manager_add_custom(ThemeManager *tm, const Theme *theme);

/**
 * @brief Get theme by index
 * @param tm ThemeManager instance
 * @param idx Theme index
 * @return Pointer to theme, or NULL if invalid index
 */
const Theme* theme_manager_get_theme(const ThemeManager *tm, size_t idx);

/**
 * @brief Get number of available themes
 * @param tm ThemeManager instance
 * @return Number of themes
 */
size_t theme_manager_get_count(const ThemeManager *tm);

/**
 * @brief Enable/disable auto night mode
 * @param tm ThemeManager instance
 * @param enabled Enable auto night mode
 * @param start_hour Night mode start hour (0-23)
 * @param end_hour Night mode end hour (0-23)
 * @param day_theme Theme index for day
 * @param night_theme Theme index for night
 */
void theme_manager_set_auto_night_mode(ThemeManager *tm, bool enabled,
                                       uint8_t start_hour, uint8_t end_hour,
                                       size_t day_theme, size_t night_theme);

/**
 * @brief Update theme based on current time (for auto night mode)
 * @param tm ThemeManager instance
 * @param current_hour Current hour (0-23)
 */
void theme_manager_update_auto_night_mode(ThemeManager *tm, uint8_t current_hour);

/**
 * @brief Adjust theme brightness based on ambient light
 * @param tm ThemeManager instance
 * @param lux Ambient light level in lux
 */
void theme_manager_adjust_brightness(ThemeManager *tm, float lux);

/**
 * @brief Clone theme for customization
 * @param dst Destination theme
 * @param src Source theme
 */
void theme_clone(Theme *dst, const Theme *src);

/**
 * @brief Apply brightness multiplier to theme
 * @param theme Theme to modify
 * @param multiplier Brightness multiplier (0.0-2.0)
 */
void theme_apply_brightness(Theme *theme, float multiplier);

/**
 * @brief Apply contrast adjustment to theme
 * @param theme Theme to modify
 * @param contrast Contrast level (0-100, 50=normal)
 */
void theme_apply_contrast(Theme *theme, uint8_t contrast);

/**
 * @brief Interpolate between two colors
 * @param c1 First color
 * @param c2 Second color
 * @param t Interpolation factor (0.0-1.0)
 * @return Interpolated color
 */
Color color_lerp(Color c1, Color c2, float t);

/**
 * @brief Darken color by percentage
 * @param c Color to darken
 * @param percent Percentage to darken (0-100)
 * @return Darkened color
 */
Color color_darken(Color c, uint8_t percent);

/**
 * @brief Lighten color by percentage
 * @param c Color to lighten
 * @param percent Percentage to lighten (0-100)
 * @return Lightened color
 */
Color color_lighten(Color c, uint8_t percent);

/**
 * @brief Adjust color alpha
 * @param c Color to modify
 * @param alpha New alpha value (0-255)
 * @return Color with new alpha
 */
Color color_with_alpha(Color c, uint8_t alpha);

// ============================================================================
// Predefined Themes
// ============================================================================

extern const Theme THEME_PRESET_MOTEC_DARK;
extern const Theme THEME_PRESET_AIM_LIGHT;
extern const Theme THEME_PRESET_RALLY_HC;
extern const Theme THEME_PRESET_NIGHT;
extern const Theme THEME_PRESET_ENDURANCE;

#ifdef __cplusplus
}
#endif
