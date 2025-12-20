#pragma once

#include <set>
#include <string>
#include <vector>

namespace firmware {

struct SignalBus;

enum class AlertSeverity { Info, Warning, Critical };

struct Alert {
    std::string id;
    std::string message;
    std::string channel;
    double threshold;
    AlertSeverity severity{AlertSeverity::Warning};
    bool latch_until_ack{true};
};

class AlertManager {
  public:
    void register_alert(Alert alert);
    void evaluate(const SignalBus &bus);
    void acknowledge(const std::string &alert_id);

  private:
    static std::string severity_to_string(AlertSeverity sev);

    std::vector<Alert> alerts_{};
    std::set<std::string> active_alerts_{};
};

} // namespace firmware
