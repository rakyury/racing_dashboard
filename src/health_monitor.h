#pragma once

#include <chrono>
#include <set>
#include <string>
#include <vector>

#include "alerts.h"
#include "data_logger.h"
#include "signal_bus.h"

namespace firmware {

struct StaleSignalRule {
    std::string id;
    std::string signal_name;
    std::chrono::milliseconds max_age{500};
    AlertSeverity severity{AlertSeverity::Warning};
};

class HealthMonitor {
  public:
    void register_rule(StaleSignalRule rule);
    void evaluate(const SignalBus &bus, AlertManager &alerts, DataLogger &logger) const;

  private:
    std::vector<StaleSignalRule> rules_{};
    mutable std::set<std::string> issued_alerts_{};
};

} // namespace firmware
