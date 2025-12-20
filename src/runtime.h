#pragma once

#include <map>
#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "alerts.h"
#include "brightness_controller.h"
#include "data_logger.h"
#include "display_manager.h"
#include "external_video.h"
#include "health_monitor.h"
#include "logic.h"
#include "math_engine.h"
#include "screen.h"
#include "signal_bus.h"

namespace firmware {

struct RuntimeInputs {
    std::map<std::string, double> numeric;
    std::map<std::string, bool> digital;
    double ambient_lux{0.0};
    std::optional<double> brightness_override{};
    ExternalVideoSource external_source{ExternalVideoSource::None};
};

struct RuntimeProfile {
    std::string default_screen;
    std::vector<Screen> screens;
    std::vector<std::pair<LogicCondition, std::string>> routes;
    std::vector<Alert> alerts;
    std::vector<MathChannel> math_channels;
    std::vector<StaleSignalRule> health_rules;
};

class Runtime {
  public:
    Runtime();

    void load_profile(const RuntimeProfile &profile);
    void ingest(const RuntimeInputs &inputs);
    void step();

    DisplayManager &display() { return display_; }
    AlertManager &alerts() { return alert_manager_; }
    MathEngine &math() { return math_engine_; }
    HealthMonitor &health() { return health_monitor_; }
    BrightnessController &brightness_controller() { return brightness_controller_; }
    DataLogger &logger() { return logger_; }
    SignalBus &bus() { return bus_; }
    ExternalInputManager &external_input() { return external_input_; }

  private:
    SignalBus bus_{};
    DisplayManager display_{};
    AlertManager alert_manager_{};
    MathEngine math_engine_{};
    HealthMonitor health_monitor_{};
    BrightnessController brightness_controller_{};
    DataLogger logger_;
    ExternalInputManager external_input_{};
};

void demo_runtime();

} // namespace firmware
