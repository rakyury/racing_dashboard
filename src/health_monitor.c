#include "health_monitor.h"

#include <stdio.h>
#include <string.h>

void health_monitor_init(HealthMonitor *monitor) { monitor->count = 0; }

void health_monitor_register(HealthMonitor *monitor, const StaleSignalRule *rule) {
    if (monitor->count >= 16) return;
    monitor->rules[monitor->count++] = *rule;
}

void health_monitor_evaluate(HealthMonitor *monitor, const SignalBus *bus, DataLogger *logger, AlertManager *alerts,
                             uint64_t now_ms) {
    (void)alerts;
    for (size_t i = 0; i < monitor->count; ++i) {
        const StaleSignalRule *rule = &monitor->rules[i];
        uint64_t ts = signal_bus_timestamp_numeric(bus, rule->signal);
        if (ts == 0) continue;
        if (now_ms - ts > rule->max_age_ms) {
            char message[120];
            snprintf(message, sizeof(message), "health: %s stale (>%llu ms)", rule->signal, (unsigned long long)rule->max_age_ms);
            data_logger_record(logger, message);
        }
    }
}

