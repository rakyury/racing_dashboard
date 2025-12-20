#pragma once

#include <stddef.h>
#include <stdint.h>

#include "alerts.h"
#include "data_logger.h"
#include "signal_bus.h"

typedef struct {
    char id[32];
    char signal[32];
    uint64_t max_age_ms;
    AlertSeverity severity;
} StaleSignalRule;

typedef struct {
    StaleSignalRule rules[16];
    size_t count;
} HealthMonitor;

void health_monitor_init(HealthMonitor *monitor);
void health_monitor_register(HealthMonitor *monitor, const StaleSignalRule *rule);
void health_monitor_evaluate(HealthMonitor *monitor, const SignalBus *bus, DataLogger *logger, AlertManager *alerts, uint64_t now_ms);

