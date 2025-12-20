#pragma once

#include <stdbool.h>
#include <stddef.h>

#include "signal_bus.h"

typedef bool (*LogicEvalFn)(const SignalBus *);

typedef struct {
    char id[32];
    char description[96];
    LogicEvalFn eval;
    int priority;
    char target_screen[32];
} LogicRoute;

