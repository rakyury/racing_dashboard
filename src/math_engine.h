#pragma once

#include <stddef.h>

#include "signal_bus.h"

typedef double (*MathEvalFn)(const SignalBus *);

typedef struct {
    char id[32];
    MathEvalFn eval;
} MathChannel;

typedef struct {
    MathChannel channels[32];
    size_t count;
} MathEngine;

void math_engine_init(MathEngine *engine);
void math_engine_register(MathEngine *engine, const MathChannel *channel);
void math_engine_evaluate(MathEngine *engine, SignalBus *bus, uint64_t now_ms);

