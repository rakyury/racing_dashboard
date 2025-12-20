#include <algorithm>
#include <functional>
#include <iostream>
#include <map>
#include <optional>
#include <string>
#include <utility>
#include <vector>

// Simplified runtime skeleton for the racing dash firmware.
// Features demonstrated:
//  - logic conditions with expression callbacks
//  - screen switching based on logical rules and prioritized fallbacks
//  - alerting with latching behavior
//  - HDMI / external video overlay pipeline hooks
//  - placeholders for CarPlay / Android Auto session negotiation

namespace firmware {

struct SignalBus {
    std::map<std::string, double> numeric_signals;
    std::map<std::string, bool> digital_signals;

    void set_numeric(const std::string &name, double value) {
        numeric_signals[name] = value;
    }

    void set_digital(const std::string &name, bool value) {
        digital_signals[name] = value;
    }

    std::optional<double> get_numeric(const std::string &name) const {
        auto it = numeric_signals.find(name);
        if (it == numeric_signals.end()) return std::nullopt;
        return it->second;
    }

    bool get_digital(const std::string &name) const {
        auto it = digital_signals.find(name);
        return it != digital_signals.end() && it->second;
    }
};

struct LogicCondition {
    std::string id;
    std::string description;
    std::function<bool(const SignalBus &)> predicate;
};

struct Screen {
    std::string id;
    std::string title;
    std::function<void()> render;
};

struct Alert {
    std::string id;
    std::string message;
    std::string channel;
    double threshold;
    bool latch_until_ack{true};
};

class AlertManager {
  public:
    void register_alert(Alert alert) { alerts_.push_back(std::move(alert)); }

    void evaluate(const SignalBus &bus) {
        for (const auto &alert : alerts_) {
            auto value = bus.get_numeric(alert.channel);
            if (value && *value >= alert.threshold) {
                active_alerts_.insert(alert.id);
                std::cout << "[ALERT] " << alert.message << " (" << *value << ")\n";
            } else if (!alert.latch_until_ack) {
                active_alerts_.erase(alert.id);
            }
        }
    }

    void acknowledge(const std::string &alert_id) { active_alerts_.erase(alert_id); }

  private:
    std::vector<Alert> alerts_{};
    std::map<std::string, bool> active_alerts_{};
};

enum class ExternalVideoSource {
    None,
    HDMI,
    CarPlay,
    AndroidAuto,
};

class ExternalInputManager {
  public:
    void set_source(ExternalVideoSource source) {
        source_ = source;
        std::cout << "External source set to " << source_to_string(source_) << "\n";
    }

    ExternalVideoSource current() const { return source_; }

    void process_frame() const {
        if (source_ == ExternalVideoSource::None) return;
        std::cout << "[VIDEO] Rendering external frame from " << source_to_string(source_) << " with overlay\n";
    }

    void negotiate_carplay_session() {
        // Placeholder for MFi/CarPlay session negotiation.
        set_source(ExternalVideoSource::CarPlay);
    }

    void negotiate_android_auto_session() {
        // Placeholder for Android Open Accessory + projection negotiation.
        set_source(ExternalVideoSource::AndroidAuto);
    }

  private:
    static std::string source_to_string(ExternalVideoSource source) {
        switch (source) {
        case ExternalVideoSource::HDMI:
            return "HDMI";
        case ExternalVideoSource::CarPlay:
            return "CarPlay";
        case ExternalVideoSource::AndroidAuto:
            return "AndroidAuto";
        default:
            return "None";
        }
    }

    ExternalVideoSource source_{ExternalVideoSource::None};
};

class DisplayManager {
  public:
    void register_screen(Screen screen) { screens_.push_back(std::move(screen)); }

    void set_default_screen(const std::string &id) { default_screen_id_ = id; }

    void register_condition(const LogicCondition &condition, const std::string &target_screen_id) {
        conditions_.push_back({condition, target_screen_id});
    }

    void tick(const SignalBus &bus, const ExternalInputManager &external_input) {
        if (external_input.current() != ExternalVideoSource::None) {
            if (auto overlay = overlay_widget_) overlay();
            external_input.process_frame();
            return;
        }

        for (const auto &entry : conditions_) {
            if (entry.condition.predicate(bus)) {
                switch_to(entry.target_screen_id);
                return;
            }
        }

        switch_to(default_screen_id_);
    }

    void set_overlay_widget(std::function<void()> widget) { overlay_widget_ = std::move(widget); }

  private:
    struct ConditionEntry {
        LogicCondition condition;
        std::string target_screen_id;
    };

    void switch_to(const std::string &screen_id) {
        auto it = std::find_if(screens_.begin(), screens_.end(), [&](const Screen &s) { return s.id == screen_id; });
        if (it == screens_.end()) return;
        if (current_screen_ != screen_id) {
            current_screen_ = screen_id;
            std::cout << "[DISPLAY] Switched to screen: " << it->title << "\n";
        }
        it->render();
    }

    std::vector<Screen> screens_{};
    std::vector<ConditionEntry> conditions_{};
    std::string current_screen_{};
    std::string default_screen_id_{};
    std::function<void()> overlay_widget_{};
};

void demo_runtime() {
    SignalBus bus;
    bus.set_numeric("rpm", 5200);
    bus.set_numeric("coolant_temp", 92.0);
    bus.set_digital("pit_limiter", false);

    AlertManager alert_manager;
    alert_manager.register_alert({"coolant_high", "Coolant temperature high", "coolant_temp", 110.0, true});
    alert_manager.register_alert({"rpm_limit", "Engine overrev", "rpm", 8500.0, false});

    ExternalInputManager external_input;

    DisplayManager display;
    display.register_screen({"main", "Main telemetry", [] { std::cout << "Render: main gauges\n"; }});
    display.register_screen({"race", "Race view", [] { std::cout << "Render: race overlay (lap, delta)\n"; }});
    display.register_screen({"warning", "Warning", [] { std::cout << "Render: warning banner\n"; }});
    display.set_default_screen("main");

    display.register_condition({"pit", "Pit limiter active", [](const SignalBus &s) { return s.get_digital("pit_limiter"); }}, "race");
    display.register_condition({"overheat", "Coolant > 110C", [](const SignalBus &s) {
                                  auto t = s.get_numeric("coolant_temp");
                                  return t && *t > 110.0;
                              }},
                              "warning");
    display.register_condition({"shift", "RPM > 7800", [](const SignalBus &s) {
                                  auto rpm = s.get_numeric("rpm");
                                  return rpm && *rpm > 7800.0;
                              }},
                              "race");

    display.set_overlay_widget([] { std::cout << "Render overlay: shift lights + alerts\n"; });

    // Normal rendering path
    alert_manager.evaluate(bus);
    display.tick(bus, external_input);

    // Trigger RPM-based screen switch and non-latching alert clearance
    bus.set_numeric("rpm", 8200);
    alert_manager.evaluate(bus);
    display.tick(bus, external_input);

    // Switch to HDMI passthrough with overlay for camera input
    external_input.set_source(ExternalVideoSource::HDMI);
    display.tick(bus, external_input);

    // Start a CarPlay session; overlays continue to render.
    external_input.negotiate_carplay_session();
    display.tick(bus, external_input);
}

} // namespace firmware

int main() {
    firmware::demo_runtime();
    return 0;
}
