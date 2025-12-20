#pragma once

#include <chrono>
#include <map>
#include <optional>
#include <string>

namespace firmware {

struct SignalBus {
    struct TimedNumeric {
        double value{0.0};
        std::chrono::steady_clock::time_point timestamp;
    };

    struct TimedDigital {
        bool value{false};
        std::chrono::steady_clock::time_point timestamp;
    };

    std::map<std::string, TimedNumeric> numeric_signals;
    std::map<std::string, TimedDigital> digital_signals;

    void set_numeric(const std::string &name, double value);
    void set_digital(const std::string &name, bool value);

    std::optional<double> get_numeric(const std::string &name) const;
    bool get_digital(const std::string &name) const;
    bool is_stale_numeric(const std::string &name, std::chrono::milliseconds max_age) const;
};

} // namespace firmware
