#include "signal_bus.h"
#include <string.h>

void signal_bus_init(SignalBus *bus) {
    if (!bus) return;
    memset(bus, 0, sizeof(SignalBus));
    bus->count = 0;
}

bool signal_bus_publish(SignalBus *bus, const char *name, float value,
                       uint64_t timestamp_ms, bool is_digital) {
    if (!bus || !name) return false;

    // Find existing signal or add new
    for (size_t i = 0; i < bus->count; i++) {
        if (strcmp(bus->signals[i].name, name) == 0) {
            bus->signals[i].value = value;
            bus->signals[i].timestamp_ms = timestamp_ms;
            bus->signals[i].is_digital = is_digital;
            bus->signals[i].is_valid = true;
            return true;
        }
    }

    // Add new signal
    if (bus->count < MAX_SIGNALS) {
        Signal *sig = &bus->signals[bus->count++];
        strncpy(sig->name, name, sizeof(sig->name) - 1);
        sig->value = value;
        sig->timestamp_ms = timestamp_ms;
        sig->is_digital = is_digital;
        sig->is_valid = true;
        return true;
    }

    return false;
}

bool signal_bus_get(const SignalBus *bus, const char *name, float *value) {
    if (!bus || !name || !value) return false;

    for (size_t i = 0; i < bus->count; i++) {
        if (strcmp(bus->signals[i].name, name) == 0 && bus->signals[i].is_valid) {
            *value = bus->signals[i].value;
            return true;
        }
    }

    return false;
}
