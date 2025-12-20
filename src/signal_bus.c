#include "signal_bus.h"

#include <string.h>

static size_t find_numeric(const SignalBus *bus, const char *name) {
    for (size_t i = 0; i < bus->numeric_count; ++i) {
        if (strcmp(bus->numeric[i].name, name) == 0) return i;
    }
    return SIZE_MAX;
}

static size_t find_digital(const SignalBus *bus, const char *name) {
    for (size_t i = 0; i < bus->digital_count; ++i) {
        if (strcmp(bus->digital[i].name, name) == 0) return i;
    }
    return SIZE_MAX;
}

void signal_bus_init(SignalBus *bus) {
    bus->numeric_count = 0;
    bus->digital_count = 0;
}

void signal_bus_set_numeric(SignalBus *bus, const char *name, double value, uint64_t now_ms) {
    size_t idx = find_numeric(bus, name);
    if (idx == SIZE_MAX) {
        if (bus->numeric_count >= MAX_NUMERIC_SIGNALS) return;
        idx = bus->numeric_count++;
        strncpy(bus->numeric[idx].name, name, sizeof(bus->numeric[idx].name) - 1);
        bus->numeric[idx].name[sizeof(bus->numeric[idx].name) - 1] = '\0';
    }
    bus->numeric[idx].value = value;
    bus->numeric[idx].timestamp_ms = now_ms;
    bus->numeric[idx].has_value = true;
}

void signal_bus_set_digital(SignalBus *bus, const char *name, bool value, uint64_t now_ms) {
    size_t idx = find_digital(bus, name);
    if (idx == SIZE_MAX) {
        if (bus->digital_count >= MAX_DIGITAL_SIGNALS) return;
        idx = bus->digital_count++;
        strncpy(bus->digital[idx].name, name, sizeof(bus->digital[idx].name) - 1);
        bus->digital[idx].name[sizeof(bus->digital[idx].name) - 1] = '\0';
    }
    bus->digital[idx].value = value;
    bus->digital[idx].timestamp_ms = now_ms;
    bus->digital[idx].has_value = true;
}

bool signal_bus_get_numeric(const SignalBus *bus, const char *name, double *out_value) {
    size_t idx = find_numeric(bus, name);
    if (idx == SIZE_MAX || !bus->numeric[idx].has_value) return false;
    if (out_value) *out_value = bus->numeric[idx].value;
    return true;
}

bool signal_bus_get_digital(const SignalBus *bus, const char *name, bool *out_value) {
    size_t idx = find_digital(bus, name);
    if (idx == SIZE_MAX || !bus->digital[idx].has_value) return false;
    if (out_value) *out_value = bus->digital[idx].value;
    return true;
}

uint64_t signal_bus_timestamp_numeric(const SignalBus *bus, const char *name) {
    size_t idx = find_numeric(bus, name);
    if (idx == SIZE_MAX) return 0;
    return bus->numeric[idx].timestamp_ms;
}

uint64_t signal_bus_timestamp_digital(const SignalBus *bus, const char *name) {
    size_t idx = find_digital(bus, name);
    if (idx == SIZE_MAX) return 0;
    return bus->digital[idx].timestamp_ms;
}

