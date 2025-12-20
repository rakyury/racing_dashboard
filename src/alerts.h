#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "signal_bus.h"

typedef enum {
    ALERT_INFO = 0,
    ALERT_WARNING = 1,
    ALERT_CRITICAL = 2
} AlertSeverity;

typedef struct {
    char id[32];
    char message[96];
    char signal[32];
    double threshold;
    AlertSeverity severity;
    bool greater_than;
    bool active;
} Alert;

typedef struct {
    Alert alerts[32];
    size_t count;
} AlertManager;

void alert_manager_init(AlertManager *mgr);
void alert_manager_register(AlertManager *mgr, const Alert *alert);
void alert_manager_evaluate(AlertManager *mgr, const SignalBus *bus);

