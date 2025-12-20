#include "brightness_controller.h"

static double clamp(double v, double min, double max) {
    if (v < min) return min;
    if (v > max) return max;
    return v;
}

void brightness_init(BrightnessController *ctl) {
    ctl->current_percent = 40.0;
    ctl->manual_override = 0.0;
    ctl->has_override = false;
}

void brightness_set_manual(BrightnessController *ctl, double percent) {
    ctl->manual_override = clamp(percent, 5.0, 100.0);
    ctl->has_override = true;
    ctl->current_percent = ctl->manual_override;
}

void brightness_clear_manual(BrightnessController *ctl) { ctl->has_override = false; }

void brightness_update_from_lux(BrightnessController *ctl, double lux) {
    if (ctl->has_override) return;
    double pct = lux / 20000.0 * 100.0;
    ctl->current_percent = clamp(pct, 15.0, 100.0);
}

