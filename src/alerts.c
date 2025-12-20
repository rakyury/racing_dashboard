#include "alerts.h"

#include <stdio.h>
#include <string.h>

void alert_manager_init(AlertManager *mgr) { mgr->count = 0; }

void alert_manager_register(AlertManager *mgr, const Alert *alert) {
    if (mgr->count >= 32) return;
    mgr->alerts[mgr->count++] = *alert;
}

void alert_manager_evaluate(AlertManager *mgr, const SignalBus *bus) {
    for (size_t i = 0; i < mgr->count; ++i) {
        Alert *alert = &mgr->alerts[i];
        double value;
        if (!signal_bus_get_numeric(bus, alert->signal, &value)) continue;
        bool condition = alert->greater_than ? (value > alert->threshold) : (value < alert->threshold);
        if (condition && !alert->active) {
            printf("[ALERT] %s (%s)\n", alert->message, alert->id);
        }
        alert->active = condition;
    }
}

