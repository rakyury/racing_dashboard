#pragma once

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    double current_percent;
    double manual_override;
    bool has_override;
} BrightnessController;

void brightness_init(BrightnessController *ctl);
void brightness_set_manual(BrightnessController *ctl, double percent);
void brightness_clear_manual(BrightnessController *ctl);
void brightness_update_from_lux(BrightnessController *ctl, double lux);

