#include "alerts.h"

#include "signal_bus.h"

#include <iostream>

namespace firmware {

void AlertManager::register_alert(Alert alert) { alerts_.push_back(std::move(alert)); }

void AlertManager::evaluate(const SignalBus &bus) {
    for (const auto &alert : alerts_) {
        auto value = bus.get_numeric(alert.channel);
        if (value && *value >= alert.threshold) {
            active_alerts_.insert(alert.id);
            std::cout << "[ALERT] (" << severity_to_string(alert.severity) << ") " << alert.message
                      << " (" << *value << ")\n";
        } else if (!alert.latch_until_ack) {
            active_alerts_.erase(alert.id);
        }
    }
}

void AlertManager::acknowledge(const std::string &alert_id) { active_alerts_.erase(alert_id); }

std::string AlertManager::severity_to_string(AlertSeverity sev) {
    switch (sev) {
    case AlertSeverity::Info:
        return "info";
    case AlertSeverity::Warning:
        return "warn";
    case AlertSeverity::Critical:
        return "crit";
    }
    return "unknown";
}

} // namespace firmware
