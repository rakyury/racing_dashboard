#pragma once

#include <math.h>
#include <stdbool.h>

typedef struct {
    const char *id;
    double value;
    double alpha;
    double deadband;
} FilteredInput;

static inline void filtered_input_update(FilteredInput *f, double raw) {
    if (fabs(raw - f->value) < f->deadband) return;
    f->value = f->alpha * raw + (1.0 - f->alpha) * f->value;
}

typedef struct {
    const char *id;
    bool state;
    int stable_cycles;
    int threshold_cycles;
} DebouncedInput;

static inline void debounced_input_update(DebouncedInput *d, bool raw) {
    if (raw == d->state) {
        d->stable_cycles = 0;
        return;
    }
    d->stable_cycles++;
    if (d->stable_cycles >= d->threshold_cycles) {
        d->state = raw;
        d->stable_cycles = 0;
    }
}

