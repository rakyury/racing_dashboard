#include "math_engine.h"

void math_engine_init(MathEngine *engine) { engine->count = 0; }

void math_engine_register(MathEngine *engine, const MathChannel *channel) {
    if (engine->count >= 32) return;
    engine->channels[engine->count++] = *channel;
}

void math_engine_evaluate(MathEngine *engine, SignalBus *bus, uint64_t now_ms) {
    for (size_t i = 0; i < engine->count; ++i) {
        const MathChannel *ch = &engine->channels[i];
        if (!ch->eval) continue;
        double value = ch->eval(bus);
        signal_bus_set_numeric(bus, ch->id, value, now_ms);
    }
}

