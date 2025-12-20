#pragma once

#include <algorithm>
#include <optional>

namespace firmware {

class BrightnessController {
  public:
    void set_manual_override(std::optional<double> percent) { manual_ = percent; }

    void update_from_lux(double lux) {
        if (manual_) return;
        double normalized = std::clamp(lux / max_lux_reference_, 0.0, 1.0);
        current_percent_ = min_percent_ + (max_percent_ - min_percent_) * normalized;
    }

    double current_percent() const { return manual_.value_or(current_percent_); }

  private:
    double min_percent_{10.0};
    double max_percent_{100.0};
    double max_lux_reference_{25000.0};
    double current_percent_{60.0};
    std::optional<double> manual_{};
};

} // namespace firmware
