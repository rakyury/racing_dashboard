#include "display_config.h"
#include <string.h>
#include <math.h>

// ============================================================================
// Static Variables
// ============================================================================

static DisplayConfig current_config;
static DisplayProfile current_profile = DISPLAY_PROFILE_1024x600_STANDARD;

// ============================================================================
// Predefined Configurations
// ============================================================================

// RVT70HSSNWN00: 1024x600 @ 7" IPS
const DisplayConfig DISPLAY_CONFIG_RVT70 = {
    .width = 1024,
    .height = 600,
    .bits_per_pixel = 24,
    .dpi = 150,
    .aspect_ratio = 1024.0f / 600.0f,
    .max_brightness_nits = 700,

    // LTDC timing for RVT70HSSNWN00
    .hsync = 20,
    .hbp = 140,
    .hfp = 160,
    .vsync = 3,
    .vbp = 20,
    .vfp = 12,
    .pixel_clock_khz = 51200,  // ~51.2 MHz for 60Hz

    .orientation = DISPLAY_ORIENTATION_LANDSCAPE,

    .layout = {
        .grid_columns = 24,
        .grid_rows = 12,
        .gutter_size = 8,

        // Widget dimensions optimized for 1024x600
        .rpm_gauge_diameter = 280,
        .status_pill_width = 120,
        .status_pill_height = 48,
        .shift_light_height = 60,
        .alert_ribbon_height = 50,

        // Font scaling for readability at 7"
        .font_scale_factor = 1.0f,
        .font_size_tiny = 10,
        .font_size_small = 14,
        .font_size_medium = 20,
        .font_size_large = 32,
        .font_size_huge = 64,

        .min_touch_target = 48,

        .screen_margin_x = 16,
        .screen_margin_y = 12,
        .widget_padding = 8,
    }
};

// Original spec: 1280x480 Ultra-wide
const DisplayConfig DISPLAY_CONFIG_ULTRAWIDE = {
    .width = 1280,
    .height = 480,
    .bits_per_pixel = 24,
    .dpi = 140,
    .aspect_ratio = 1280.0f / 480.0f,
    .max_brightness_nits = 1000,

    .hsync = 10,
    .hbp = 80,
    .hfp = 70,
    .vsync = 3,
    .vbp = 13,
    .vfp = 10,
    .pixel_clock_khz = 40000,

    .orientation = DISPLAY_ORIENTATION_LANDSCAPE,

    .layout = {
        .grid_columns = 32,
        .grid_rows = 8,
        .gutter_size = 8,

        .rpm_gauge_diameter = 240,
        .status_pill_width = 100,
        .status_pill_height = 40,
        .shift_light_height = 50,
        .alert_ribbon_height = 45,

        .font_scale_factor = 0.9f,
        .font_size_tiny = 9,
        .font_size_small = 12,
        .font_size_medium = 18,
        .font_size_large = 28,
        .font_size_huge = 56,

        .min_touch_target = 44,

        .screen_margin_x = 12,
        .screen_margin_y = 8,
        .widget_padding = 6,
    }
};

// Compact: 800x480
const DisplayConfig DISPLAY_CONFIG_COMPACT = {
    .width = 800,
    .height = 480,
    .bits_per_pixel = 16,
    .dpi = 133,
    .aspect_ratio = 800.0f / 480.0f,
    .max_brightness_nits = 400,

    .hsync = 10,
    .hbp = 46,
    .hfp = 16,
    .vsync = 3,
    .vbp = 23,
    .vfp = 7,
    .pixel_clock_khz = 30000,

    .orientation = DISPLAY_ORIENTATION_LANDSCAPE,

    .layout = {
        .grid_columns = 16,
        .grid_rows = 8,
        .gutter_size = 6,

        .rpm_gauge_diameter = 200,
        .status_pill_width = 90,
        .status_pill_height = 36,
        .shift_light_height = 40,
        .alert_ribbon_height = 40,

        .font_scale_factor = 0.75f,
        .font_size_tiny = 8,
        .font_size_small = 10,
        .font_size_medium = 14,
        .font_size_large = 22,
        .font_size_huge = 42,

        .min_touch_target = 40,

        .screen_margin_x = 10,
        .screen_margin_y = 8,
        .widget_padding = 4,
    }
};

// Minimal: 480x320
const DisplayConfig DISPLAY_CONFIG_MINIMAL = {
    .width = 480,
    .height = 320,
    .bits_per_pixel = 16,
    .dpi = 115,
    .aspect_ratio = 480.0f / 320.0f,
    .max_brightness_nits = 300,

    .hsync = 10,
    .hbp = 43,
    .hfp = 8,
    .vsync = 3,
    .vbp = 12,
    .vfp = 4,
    .pixel_clock_khz = 15000,

    .orientation = DISPLAY_ORIENTATION_LANDSCAPE,

    .layout = {
        .grid_columns = 12,
        .grid_rows = 6,
        .gutter_size = 4,

        .rpm_gauge_diameter = 140,
        .status_pill_width = 70,
        .status_pill_height = 28,
        .shift_light_height = 30,
        .alert_ribbon_height = 32,

        .font_scale_factor = 0.55f,
        .font_size_tiny = 7,
        .font_size_small = 9,
        .font_size_medium = 12,
        .font_size_large = 18,
        .font_size_huge = 32,

        .min_touch_target = 36,

        .screen_margin_x = 8,
        .screen_margin_y = 6,
        .widget_padding = 3,
    }
};

// ============================================================================
// Public API Implementation
// ============================================================================

const DisplayConfig* display_config_init(DisplayProfile profile) {
    current_profile = profile;

    switch (profile) {
        case DISPLAY_PROFILE_1024x600_STANDARD:
            memcpy(&current_config, &DISPLAY_CONFIG_RVT70, sizeof(DisplayConfig));
            break;

        case DISPLAY_PROFILE_1280x480_ULTRAWIDE:
            memcpy(&current_config, &DISPLAY_CONFIG_ULTRAWIDE, sizeof(DisplayConfig));
            break;

        case DISPLAY_PROFILE_800x480_COMPACT:
            memcpy(&current_config, &DISPLAY_CONFIG_COMPACT, sizeof(DisplayConfig));
            break;

        case DISPLAY_PROFILE_480x320_MINIMAL:
            memcpy(&current_config, &DISPLAY_CONFIG_MINIMAL, sizeof(DisplayConfig));
            break;

        case DISPLAY_PROFILE_CUSTOM:
            // Keep existing custom config
            break;

        default:
            // Default to RVT70
            memcpy(&current_config, &DISPLAY_CONFIG_RVT70, sizeof(DisplayConfig));
            current_profile = DISPLAY_PROFILE_1024x600_STANDARD;
            break;
    }

    return &current_config;
}

const DisplayConfig* display_config_get_current(void) {
    return &current_config;
}

bool display_config_set_profile(DisplayProfile profile) {
    if (profile == current_profile && profile != DISPLAY_PROFILE_CUSTOM) {
        return true;  // Already set
    }

    display_config_init(profile);
    return true;
}

bool display_config_set_custom(const DisplayConfig *config) {
    if (config == NULL) {
        return false;
    }

    memcpy(&current_config, config, sizeof(DisplayConfig));
    current_profile = DISPLAY_PROFILE_CUSTOM;
    return true;
}

DisplayOrientation display_config_get_orientation(void) {
    return current_config.orientation;
}

bool display_config_set_orientation(DisplayOrientation orientation) {
    if (orientation > DISPLAY_ORIENTATION_PORTRAIT_INV) {
        return false;
    }

    current_config.orientation = orientation;

    // Swap width/height for portrait modes
    if (orientation == DISPLAY_ORIENTATION_PORTRAIT ||
        orientation == DISPLAY_ORIENTATION_PORTRAIT_INV) {
        uint16_t temp = current_config.width;
        current_config.width = current_config.height;
        current_config.height = temp;
        current_config.aspect_ratio = (float)current_config.width / current_config.height;

        // Swap grid dimensions
        uint8_t temp_grid = current_config.layout.grid_columns;
        current_config.layout.grid_columns = current_config.layout.grid_rows;
        current_config.layout.grid_rows = temp_grid;
    }

    return true;
}

void display_config_scale_widget(uint16_t base_width, uint16_t base_height,
                                 uint16_t *out_width, uint16_t *out_height) {
    // Reference resolution: 1920x1080 (Full HD)
    const float reference_width = 1920.0f;
    const float reference_height = 1080.0f;

    // Calculate scaling factors
    float scale_x = (float)current_config.width / reference_width;
    float scale_y = (float)current_config.height / reference_height;

    // Use minimum scale to maintain aspect ratio
    float scale = (scale_x < scale_y) ? scale_x : scale_y;

    // Apply font scaling factor
    scale *= current_config.layout.font_scale_factor;

    if (out_width) {
        *out_width = (uint16_t)roundf(base_width * scale);
    }

    if (out_height) {
        *out_height = (uint16_t)roundf(base_height * scale);
    }
}

void display_config_grid_to_pixels(uint8_t col, uint8_t row,
                                   uint16_t *out_x, uint16_t *out_y) {
    uint16_t cell_width, cell_height;
    display_config_get_cell_size(&cell_width, &cell_height);

    if (out_x) {
        *out_x = current_config.layout.screen_margin_x +
                 col * (cell_width + current_config.layout.gutter_size);
    }

    if (out_y) {
        *out_y = current_config.layout.screen_margin_y +
                 row * (cell_height + current_config.layout.gutter_size);
    }
}

void display_config_get_cell_size(uint16_t *out_width, uint16_t *out_height) {
    uint16_t usable_width = current_config.width -
                           (2 * current_config.layout.screen_margin_x) -
                           ((current_config.layout.grid_columns - 1) * current_config.layout.gutter_size);

    uint16_t usable_height = current_config.height -
                            (2 * current_config.layout.screen_margin_y) -
                            ((current_config.layout.grid_rows - 1) * current_config.layout.gutter_size);

    if (out_width) {
        *out_width = usable_width / current_config.layout.grid_columns;
    }

    if (out_height) {
        *out_height = usable_height / current_config.layout.grid_rows;
    }
}

bool display_config_is_point_valid(uint16_t x, uint16_t y) {
    return (x < current_config.width && y < current_config.height);
}

void display_config_get_safe_area(uint16_t *out_x, uint16_t *out_y,
                                  uint16_t *out_width, uint16_t *out_height) {
    if (out_x) {
        *out_x = current_config.layout.screen_margin_x;
    }

    if (out_y) {
        *out_y = current_config.layout.screen_margin_y;
    }

    if (out_width) {
        *out_width = current_config.width - (2 * current_config.layout.screen_margin_x);
    }

    if (out_height) {
        *out_height = current_config.height - (2 * current_config.layout.screen_margin_y);
    }
}
