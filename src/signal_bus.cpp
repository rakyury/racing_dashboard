#include "signal_bus.h"

#include <chrono>

namespace firmware {

void SignalBus::set_numeric(const std::string &name, double value) {
    numeric_signals[name] = {value, std::chrono::steady_clock::now()};
}

void SignalBus::set_digital(const std::string &name, bool value) {
    digital_signals[name] = {value, std::chrono::steady_clock::now()};
}

std::optional<double> SignalBus::get_numeric(const std::string &name) const {
    auto it = numeric_signals.find(name);
    if (it == numeric_signals.end()) return std::nullopt;
    return it->second.value;
}

bool SignalBus::get_digital(const std::string &name) const {
    auto it = digital_signals.find(name);
    return it != digital_signals.end() && it->second.value;
}

bool SignalBus::is_stale_numeric(const std::string &name, std::chrono::milliseconds max_age) const {
    auto it = numeric_signals.find(name);
    if (it == numeric_signals.end()) return true;
    return (std::chrono::steady_clock::now() - it->second.timestamp) > max_age;
}

} // namespace firmware
