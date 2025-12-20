#include "theme_manager.h"
#include <string.h>
#include <math.h>

// ============================================================================
// Helper Functions
// ============================================================================

static uint8_t clamp_uint8(int value) {
    if (value < 0) return 0;
    if (value > 255) return 255;
    return (uint8_t)value;
}

static float clamp_float(float value, float min, float max) {
    if (value < min) return min;
    if (value > max) return max;
    return value;
}

// ============================================================================
// Predefined Theme: Motec Dark (Professional)
// ============================================================================

const Theme THEME_PRESET_MOTEC_DARK = {
    .name = "Motec Dark",
    .description = "Professional dark theme inspired by Motec displays",

    .background = HEX_TO_RGB(0x0c0f12),
    .background_secondary = HEX_TO_RGB(0x161a1f),
    .surface = HEX_TO_RGB(0x1e2429),

    .accent = HEX_TO_RGB(0xff4300),           // Orange
    .accent_secondary = HEX_TO_RGB(0xff6b35),

    .success = HEX_TO_RGB(0x3ddc97),          // Green
    .warning = HEX_TO_RGB(0xffb703),          // Yellow
    .critical = HEX_TO_RGB(0xff3366),         // Red
    .info = HEX_TO_RGB(0x00b4d8),             // Cyan

    .text_primary = HEX_TO_RGB(0xf0f3f7),
    .text_secondary = HEX_TO_RGB(0x8b95a1),
    .text_disabled = HEX_TO_RGB(0x4a5461),
    .text_on_accent = HEX_TO_RGB(0xffffff),

    .border = HEX_TO_RGB(0x2d3540),
    .shadow = RGBA(0, 0, 0, 128),
    .overlay = RGBA(0, 0, 0, 200),

    .rpm_normal = HEX_TO_RGB(0x00b4d8),
    .rpm_warning = HEX_TO_RGB(0xffb703),
    .rpm_redline = HEX_TO_RGB(0xff3366),
    .shift_indicator = HEX_TO_RGB(0xff4300),

    .graph_line1 = HEX_TO_RGB(0x3ddc97),
    .graph_line2 = HEX_TO_RGB(0x00b4d8),
    .graph_grid = HEX_TO_RGB(0x1e2429),

    .brightness_multiplier = 1.0f,
    .contrast = 50,
    .saturation = 85,
    .anti_glare_mode = false
};

// ============================================================================
// Predefined Theme: AIM Sport Light
// ============================================================================

const Theme THEME_PRESET_AIM_LIGHT = {
    .name = "AIM Sport Light",
    .description = "High-contrast light theme for bright conditions",

    .background = HEX_TO_RGB(0xf5f7fa),
    .background_secondary = HEX_TO_RGB(0xe8ecf1),
    .surface = HEX_TO_RGB(0xffffff),

    .accent = HEX_TO_RGB(0xd62828),           // Red
    .accent_secondary = HEX_TO_RGB(0xf77f00),

    .success = HEX_TO_RGB(0x2d6a4f),
    .warning = HEX_TO_RGB(0xf77f00),
    .critical = HEX_TO_RGB(0xd62828),
    .info = HEX_TO_RGB(0x0077b6),

    .text_primary = HEX_TO_RGB(0x1a1d23),
    .text_secondary = HEX_TO_RGB(0x5a5f6b),
    .text_disabled = HEX_TO_RGB(0xadb5bd),
    .text_on_accent = HEX_TO_RGB(0xffffff),

    .border = HEX_TO_RGB(0xdce1e8),
    .shadow = RGBA(0, 0, 0, 40),
    .overlay = RGBA(255, 255, 255, 220),

    .rpm_normal = HEX_TO_RGB(0x0077b6),
    .rpm_warning = HEX_TO_RGB(0xf77f00),
    .rpm_redline = HEX_TO_RGB(0xd62828),
    .shift_indicator = HEX_TO_RGB(0xd62828),

    .graph_line1 = HEX_TO_RGB(0x2d6a4f),
    .graph_line2 = HEX_TO_RGB(0x0077b6),
    .graph_grid = HEX_TO_RGB(0xe8ecf1),

    .brightness_multiplier = 1.2f,
    .contrast = 65,
    .saturation = 75,
    .anti_glare_mode = true
};

// ============================================================================
// Predefined Theme: Rally High-Contrast
// ============================================================================

const Theme THEME_PRESET_RALLY_HC = {
    .name = "Rally HC",
    .description = "Maximum contrast for harsh outdoor conditions",

    .background = HEX_TO_RGB(0x000000),
    .background_secondary = HEX_TO_RGB(0x1a1a1a),
    .surface = HEX_TO_RGB(0x262626),

    .accent = HEX_TO_RGB(0xffff00),           // Pure yellow
    .accent_secondary = HEX_TO_RGB(0xffa500),

    .success = HEX_TO_RGB(0x00ff00),          // Pure green
    .warning = HEX_TO_RGB(0xffff00),          // Pure yellow
    .critical = HEX_TO_RGB(0xff0000),         // Pure red
    .info = HEX_TO_RGB(0x00ffff),             // Pure cyan

    .text_primary = HEX_TO_RGB(0xffffff),
    .text_secondary = HEX_TO_RGB(0xcccccc),
    .text_disabled = HEX_TO_RGB(0x666666),
    .text_on_accent = HEX_TO_RGB(0x000000),

    .border = HEX_TO_RGB(0x4d4d4d),
    .shadow = RGBA(0, 0, 0, 180),
    .overlay = RGBA(0, 0, 0, 230),

    .rpm_normal = HEX_TO_RGB(0x00ff00),
    .rpm_warning = HEX_TO_RGB(0xffff00),
    .rpm_redline = HEX_TO_RGB(0xff0000),
    .shift_indicator = HEX_TO_RGB(0xffff00),

    .graph_line1 = HEX_TO_RGB(0x00ff00),
    .graph_line2 = HEX_TO_RGB(0x00ffff),
    .graph_grid = HEX_TO_RGB(0x333333),

    .brightness_multiplier = 1.5f,
    .contrast = 100,
    .saturation = 100,
    .anti_glare_mode = false
};

// ============================================================================
// Predefined Theme: Night Mode
// ============================================================================

const Theme THEME_PRESET_NIGHT = {
    .name = "Night Mode",
    .description = "Red-accent theme to preserve night vision",

    .background = HEX_TO_RGB(0x0a0000),
    .background_secondary = HEX_TO_RGB(0x160000),
    .surface = HEX_TO_RGB(0x220000),

    .accent = HEX_TO_RGB(0xff0000),           // Red only
    .accent_secondary = HEX_TO_RGB(0xcc0000),

    .success = HEX_TO_RGB(0x4d0000),
    .warning = HEX_TO_RGB(0x990000),
    .critical = HEX_TO_RGB(0xff3300),
    .info = HEX_TO_RGB(0x660000),

    .text_primary = HEX_TO_RGB(0xff6666),
    .text_secondary = HEX_TO_RGB(0x994444),
    .text_disabled = HEX_TO_RGB(0x442222),
    .text_on_accent = HEX_TO_RGB(0xffffff),

    .border = HEX_TO_RGB(0x330000),
    .shadow = RGBA(0, 0, 0, 150),
    .overlay = RGBA(10, 0, 0, 200),

    .rpm_normal = HEX_TO_RGB(0x660000),
    .rpm_warning = HEX_TO_RGB(0xaa0000),
    .rpm_redline = HEX_TO_RGB(0xff0000),
    .shift_indicator = HEX_TO_RGB(0xff3300),

    .graph_line1 = HEX_TO_RGB(0xff3333),
    .graph_line2 = HEX_TO_RGB(0xcc2222),
    .graph_grid = HEX_TO_RGB(0x220000),

    .brightness_multiplier = 0.4f,
    .contrast = 45,
    .saturation = 60,
    .anti_glare_mode = false
};

// ============================================================================
// Predefined Theme: Endurance
// ============================================================================

const Theme THEME_PRESET_ENDURANCE = {
    .name = "Endurance",
    .description = "Low-brightness blue theme for long races",

    .background = HEX_TO_RGB(0x000a1a),
    .background_secondary = HEX_TO_RGB(0x001529),
    .surface = HEX_TO_RGB(0x002140),

    .accent = HEX_TO_RGB(0x0096c7),           // Blue
    .accent_secondary = HEX_TO_RGB(0x00b4d8),

    .success = HEX_TO_RGB(0x06d6a0),
    .warning = HEX_TO_RGB(0xffb703),
    .critical = HEX_TO_RGB(0xff006e),
    .info = HEX_TO_RGB(0x4cc9f0),

    .text_primary = HEX_TO_RGB(0xcaf0f8),
    .text_secondary = HEX_TO_RGB(0x7d98a1),
    .text_disabled = HEX_TO_RGB(0x3d5a68),
    .text_on_accent = HEX_TO_RGB(0xffffff),

    .border = HEX_TO_RGB(0x003554),
    .shadow = RGBA(0, 0, 0, 120),
    .overlay = RGBA(0, 10, 26, 210),

    .rpm_normal = HEX_TO_RGB(0x00b4d8),
    .rpm_warning = HEX_TO_RGB(0x90e0ef),
    .rpm_redline = HEX_TO_RGB(0xff006e),
    .shift_indicator = HEX_TO_RGB(0x4cc9f0),

    .graph_line1 = HEX_TO_RGB(0x06d6a0),
    .graph_line2 = HEX_TO_RGB(0x4cc9f0),
    .graph_grid = HEX_TO_RGB(0x002140),

    .brightness_multiplier = 0.7f,
    .contrast = 40,
    .saturation = 70,
    .anti_glare_mode = false
};

// ============================================================================
// Theme Manager Implementation
// ============================================================================

void theme_manager_init(ThemeManager *tm) {
    memset(tm, 0, sizeof(ThemeManager));

    // Load predefined themes
    tm->themes[THEME_MOTEC_DARK] = THEME_PRESET_MOTEC_DARK;
    tm->themes[THEME_AIM_SPORT_LIGHT] = THEME_PRESET_AIM_LIGHT;
    tm->themes[THEME_RALLY_HIGH_CONTRAST] = THEME_PRESET_RALLY_HC;
    tm->themes[THEME_NIGHT_MODE] = THEME_PRESET_NIGHT;
    tm->themes[THEME_ENDURANCE] = THEME_PRESET_ENDURANCE;

    tm->theme_count = 5;
    tm->active_theme_idx = THEME_MOTEC_DARK;

    // Default auto night mode settings
    tm->auto_night_mode_enabled = false;
    tm->night_mode_start_hour = 20;  // 8 PM
    tm->night_mode_end_hour = 6;     // 6 AM
    tm->day_theme_idx = THEME_MOTEC_DARK;
    tm->night_theme_idx = THEME_NIGHT_MODE;

    tm->sync_brightness_with_als = true;
}

const Theme* theme_manager_get_active(const ThemeManager *tm) {
    return &tm->themes[tm->active_theme_idx];
}

bool theme_manager_set_active(ThemeManager *tm, size_t theme_idx) {
    if (theme_idx >= tm->theme_count) {
        return false;
    }

    tm->active_theme_idx = theme_idx;
    return true;
}

bool theme_manager_set_preset(ThemeManager *tm, ThemePreset preset) {
    return theme_manager_set_active(tm, (size_t)preset);
}

int theme_manager_add_custom(ThemeManager *tm, const Theme *theme) {
    if (tm->theme_count >= MAX_THEMES || theme == NULL) {
        return -1;
    }

    memcpy(&tm->themes[tm->theme_count], theme, sizeof(Theme));
    return (int)(tm->theme_count++);
}

const Theme* theme_manager_get_theme(const ThemeManager *tm, size_t idx) {
    if (idx >= tm->theme_count) {
        return NULL;
    }
    return &tm->themes[idx];
}

size_t theme_manager_get_count(const ThemeManager *tm) {
    return tm->theme_count;
}

void theme_manager_set_auto_night_mode(ThemeManager *tm, bool enabled,
                                       uint8_t start_hour, uint8_t end_hour,
                                       size_t day_theme, size_t night_theme) {
    tm->auto_night_mode_enabled = enabled;
    tm->night_mode_start_hour = start_hour % 24;
    tm->night_mode_end_hour = end_hour % 24;

    if (day_theme < tm->theme_count) {
        tm->day_theme_idx = day_theme;
    }

    if (night_theme < tm->theme_count) {
        tm->night_theme_idx = night_theme;
    }
}

void theme_manager_update_auto_night_mode(ThemeManager *tm, uint8_t current_hour) {
    if (!tm->auto_night_mode_enabled) {
        return;
    }

    current_hour = current_hour % 24;
    bool is_night_time;

    if (tm->night_mode_start_hour < tm->night_mode_end_hour) {
        // Normal case (e.g., 6 AM to 8 PM)
        is_night_time = (current_hour < tm->night_mode_end_hour ||
                        current_hour >= tm->night_mode_start_hour);
    } else {
        // Wrapped case (e.g., 8 PM to 6 AM)
        is_night_time = (current_hour >= tm->night_mode_start_hour &&
                        current_hour < tm->night_mode_end_hour);
    }

    size_t target_theme = is_night_time ? tm->night_theme_idx : tm->day_theme_idx;

    if (tm->active_theme_idx != target_theme) {
        theme_manager_set_active(tm, target_theme);
    }
}

void theme_manager_adjust_brightness(ThemeManager *tm, float lux) {
    if (!tm->sync_brightness_with_als) {
        return;
    }

    // Logarithmic mapping: 0.1 lux (dark) to 100000 lux (bright sunlight)
    // Result: 0.3 (very dim) to 1.5 (very bright)
    float brightness_multiplier;

    if (lux < 1.0f) {
        brightness_multiplier = 0.3f;
    } else if (lux > 10000.0f) {
        brightness_multiplier = 1.5f;
    } else {
        // Logarithmic scale
        brightness_multiplier = 0.3f + (logf(lux) / logf(10000.0f)) * 1.2f;
    }

    brightness_multiplier = clamp_float(brightness_multiplier, 0.3f, 1.5f);

    // Apply to active theme
    tm->themes[tm->active_theme_idx].brightness_multiplier = brightness_multiplier;
}

// ============================================================================
// Color Utilities
// ============================================================================

void theme_clone(Theme *dst, const Theme *src) {
    if (dst && src) {
        memcpy(dst, src, sizeof(Theme));
    }
}

void theme_apply_brightness(Theme *theme, float multiplier) {
    multiplier = clamp_float(multiplier, 0.0f, 2.0f);
    theme->brightness_multiplier = multiplier;
}

void theme_apply_contrast(Theme *theme, uint8_t contrast) {
    theme->contrast = (contrast > 100) ? 100 : contrast;
}

Color color_lerp(Color c1, Color c2, float t) {
    t = clamp_float(t, 0.0f, 1.0f);
    return (Color){
        .r = clamp_uint8((int)(c1.r + (c2.r - c1.r) * t)),
        .g = clamp_uint8((int)(c1.g + (c2.g - c1.g) * t)),
        .b = clamp_uint8((int)(c1.b + (c2.b - c1.b) * t)),
        .a = clamp_uint8((int)(c1.a + (c2.a - c1.a) * t))
    };
}

Color color_darken(Color c, uint8_t percent) {
    if (percent > 100) percent = 100;
    float factor = 1.0f - (percent / 100.0f);

    return (Color){
        .r = clamp_uint8((int)(c.r * factor)),
        .g = clamp_uint8((int)(c.g * factor)),
        .b = clamp_uint8((int)(c.b * factor)),
        .a = c.a
    };
}

Color color_lighten(Color c, uint8_t percent) {
    if (percent > 100) percent = 100;
    float factor = percent / 100.0f;

    return (Color){
        .r = clamp_uint8((int)(c.r + (255 - c.r) * factor)),
        .g = clamp_uint8((int)(c.g + (255 - c.g) * factor)),
        .b = clamp_uint8((int)(c.b + (255 - c.b) * factor)),
        .a = c.a
    };
}

Color color_with_alpha(Color c, uint8_t alpha) {
    c.a = alpha;
    return c;
}
