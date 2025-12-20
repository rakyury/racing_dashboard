#include "health_monitor.h"

#include <limits>

namespace firmware {

void HealthMonitor::register_rule(StaleSignalRule rule) { rules_.push_back(std::move(rule)); }

void HealthMonitor::evaluate(const SignalBus &bus, AlertManager &alerts, DataLogger &logger) const {
    for (const auto &rule : rules_) {
        if (bus.is_stale_numeric(rule.signal_name, rule.max_age)) {
            logger.record("health: stale " + rule.signal_name);
            if (issued_alerts_.insert(rule.id).second) {
                alerts.register_alert({rule.id,
                                       "Signal stale: " + rule.signal_name,
                                       rule.signal_name,
                                       std::numeric_limits<double>::lowest(),
                                       rule.severity,
                                       false});
            }
        }
    }
}

} // namespace firmware
