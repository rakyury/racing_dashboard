#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define MAX_NUMERIC_SIGNALS 64
#define MAX_DIGITAL_SIGNALS 32

typedef struct {
    char name[32];
    double value;
    uint64_t timestamp_ms;
    bool has_value;
} NumericSignal;

typedef struct {
    char name[32];
    bool value;
    uint64_t timestamp_ms;
    bool has_value;
} DigitalSignal;

typedef struct {
    NumericSignal numeric[MAX_NUMERIC_SIGNALS];
    DigitalSignal digital[MAX_DIGITAL_SIGNALS];
    size_t numeric_count;
    size_t digital_count;
} SignalBus;

void signal_bus_init(SignalBus *bus);
void signal_bus_set_numeric(SignalBus *bus, const char *name, double value, uint64_t now_ms);
void signal_bus_set_digital(SignalBus *bus, const char *name, bool value, uint64_t now_ms);
bool signal_bus_get_numeric(const SignalBus *bus, const char *name, double *out_value);
bool signal_bus_get_digital(const SignalBus *bus, const char *name, bool *out_value);
uint64_t signal_bus_timestamp_numeric(const SignalBus *bus, const char *name);
uint64_t signal_bus_timestamp_digital(const SignalBus *bus, const char *name);

#ifdef __cplusplus
}
#endif

