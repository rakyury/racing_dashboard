#pragma once

#include <cmath>
#include <string>

namespace firmware {

struct FilteredInput {
    std::string id;
    double value{0.0};
    double alpha{0.2};
    double deadband{0.0};

    void update(double raw) {
        if (std::abs(raw - value) < deadband) return;
        value = alpha * raw + (1.0 - alpha) * value;
    }
};

struct DebouncedInput {
    std::string id;
    bool state{false};
    int stable_cycles{0};
    int threshold_cycles{3};

    void update(bool raw) {
        if (raw == state) {
            stable_cycles = 0;
            return;
        }
        stable_cycles++;
        if (stable_cycles >= threshold_cycles) {
            state = raw;
            stable_cycles = 0;
        }
    }
};

} // namespace firmware
