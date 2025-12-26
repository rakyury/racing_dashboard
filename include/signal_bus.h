#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @file signal_bus.h
 * @brief Signal bus for pub/sub telemetry data
 *
 * Simple signal bus implementation for compatibility
 */

#define MAX_SIGNALS 64

typedef struct {
    char name[32];
    float value;
    uint64_t timestamp_ms;
    bool is_digital;
    bool is_valid;
} Signal;

typedef struct {
    Signal signals[MAX_SIGNALS];
    size_t count;
} SignalBus;

void signal_bus_init(SignalBus *bus);
bool signal_bus_publish(SignalBus *bus, const char *name, float value, uint64_t timestamp_ms, bool is_digital);
bool signal_bus_get(const SignalBus *bus, const char *name, float *value);

#ifdef __cplusplus
}
#endif
