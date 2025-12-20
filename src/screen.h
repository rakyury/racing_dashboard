#pragma once

#include "signal_bus.h"

typedef void (*ScreenRenderFn)(const SignalBus *);

typedef struct {
    char id[32];
    char title[64];
    ScreenRenderFn render;
} Screen;

