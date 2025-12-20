#include "runtime.h"

#include <chrono>
#include <iostream>

#include "filters.h"
#include "touchgfx_widgets.h"

namespace firmware {

Runtime::Runtime() : logger_(256) {}

void Runtime::load_profile(const RuntimeProfile &profile) {
    for (const auto &screen : profile.screens) {
        display_.register_screen(screen);
    }
    display_.set_default_screen(profile.default_screen);

    for (const auto &route : profile.routes) {
        display_.register_condition(route.first, route.second);
    }

    for (const auto &alert : profile.alerts) {
        alert_manager_.register_alert(alert);
    }

    for (const auto &math : profile.math_channels) {
        math_engine_.register_channel(math);
    }

    for (const auto &rule : profile.health_rules) {
        health_monitor_.register_rule(rule);
    }
}

void Runtime::ingest(const RuntimeInputs &inputs) {
    for (const auto &[name, value] : inputs.numeric) {
        bus_.set_numeric(name, value);
    }
    for (const auto &[name, value] : inputs.digital) {
        bus_.set_digital(name, value);
    }

    brightness_controller_.set_manual_override(inputs.brightness_override);
    brightness_controller_.update_from_lux(inputs.ambient_lux);
    external_input_.set_source(inputs.external_source);
}

void Runtime::step() {
    math_engine_.evaluate(bus_);
    alert_manager_.evaluate(bus_);
    health_monitor_.evaluate(bus_, alert_manager_, logger_);
    display_.tick(bus_, external_input_);
}

namespace {

TouchGFXPalette motec_palette() { return TouchGFXPalette{}; }

std::vector<Screen> build_touchgfx_screens(const TouchGFXPalette &palette) {
    std::vector<Screen> screens;

    screens.push_back(TouchGFXScreen("main", "Main", {
                                         std::make_shared<RadialGauge>("rpm", "RPM", " rpm", 0, 9000),
                                         std::make_shared<RadialGauge>("speed_kph", "Speed", " km/h", 0, 320),
                                         std::make_shared<StatusPill>("coolant_temp", "Coolant", "C", 105, 120),
                                         std::make_shared<StatusPill>("oil_temp", "Oil", "C", 120, 135),
                                         std::make_shared<LinearBar>("battery_voltage", "Battery", "V", 14.4),
                                         std::make_shared<LinearBar>("boost_kpa", "Boost", "kPa", 220),
                                         std::make_shared<LinearBar>("throttle", "Throttle", "%", 100),
                                         std::make_shared<MixtureGraph>("lambda_current", "lambda_target"),
                                     }).to_runtime_screen(palette));

    screens.push_back(TouchGFXScreen("warning", "Warning", {
                                         std::make_shared<StatusPill>("oil_pressure", "Oil P", "bar", 1.8, 1.2),
                                         std::make_shared<StatusPill>("fuel_pressure", "Fuel P", "bar", 3.4, 2.8),
                                         std::make_shared<StatusPill>("coolant_temp", "Coolant", "C", 108, 118),
                                         std::make_shared<StatusPill>("oil_temp", "Oil T", "C", 125, 140),
                                         std::make_shared<MixtureGraph>("lambda_current", "lambda_target"),
                                     }).to_runtime_screen(palette));

    screens.push_back(TouchGFXScreen("race", "Race", {
                                         std::make_shared<RadialGauge>("rpm", "RPM", " rpm", 0, 9000),
                                         std::make_shared<LinearBar>("shift_light_level", "Shift", "%", 1.0),
                                         std::make_shared<LinearBar>("boost_kpa", "Boost", "kPa", 240),
                                         std::make_shared<LinearBar>("throttle", "Throttle", "%", 100),
                                         std::make_shared<MixtureGraph>("lambda_current", "lambda_target"),
                                     }).to_runtime_screen(palette));

    return screens;
}

RuntimeProfile build_demo_profile(const TouchGFXPalette &palette) {
    RuntimeProfile profile{};
    profile.default_screen = "main";
    profile.screens = build_touchgfx_screens(palette);
    profile.routes = {
        {{"pit", "Pit limiter active", [](const SignalBus &s) { return s.get_digital("pit_limiter"); }, 5}, "race"},
        {{"overheat", "Coolant > 112C", [](const SignalBus &s) {
             auto t = s.get_numeric("coolant_temp");
             return t && *t > 112.0;
         }},
         "warning"},
        {{"oil_low", "Oil pressure low", [](const SignalBus &s) {
             auto p = s.get_numeric("oil_pressure");
             return p && *p < 1.5;
         },
         1},
         "warning"},
        {{"startup", "Show startup", [](const SignalBus &) { return true; }, 100}, "main"}};

    profile.alerts = {{"coolant_high", "Coolant temperature high", "coolant_temp", 112.0, AlertSeverity::Warning, true},
                      {"oil_pressure_low", "Oil pressure critical", "oil_pressure", 1.5, AlertSeverity::Critical, true},
                      {"battery_low", "Battery voltage low", "battery_voltage", 12.0, AlertSeverity::Warning, false},
                      {"afr_lean", "AFR lean vs target", "afr_error", 0.2, AlertSeverity::Warning, false},
                      {"rpm_limit", "Engine overrev", "rpm", 8500.0, AlertSeverity::Warning, false}};

    profile.math_channels = {{"speed_kph", [](const SignalBus &s) {
                                 auto rpm = s.get_numeric("rpm");
                                 auto gear = s.get_numeric("gear_ratio");
                                 if (!rpm || !gear) return 0.0;
                                 return (*rpm / *gear) * 0.0021;
                             }},
                            {"shift_light_level", [](const SignalBus &s) {
                                 auto rpm = s.get_numeric("rpm");
                                 if (!rpm) return 0.0;
                                 return std::clamp((*rpm - 6200.0) / 2600.0, 0.0, 1.0);
                             }},
                            {"afr_error", [](const SignalBus &s) {
                                 auto cur = s.get_numeric("lambda_current");
                                 auto tgt = s.get_numeric("lambda_target");
                                 if (!cur || !tgt) return 0.0;
                                 return *cur - *tgt;
                             }}};

    profile.health_rules = {{"rpm_stale", "rpm", std::chrono::milliseconds(1500), AlertSeverity::Critical},
                           {"coolant_stale", "coolant_temp", std::chrono::milliseconds(2500), AlertSeverity::Warning},
                           {"lambda_stale", "lambda_current", std::chrono::milliseconds(1200), AlertSeverity::Warning}};

    return profile;
}

RuntimeInputs base_inputs() {
    FilteredInput throttle{"throttle", 0.0, 0.35, 0.5};
    throttle.update(30.0);
    throttle.update(42.0);

    return RuntimeInputs{.numeric = {{"rpm", 5200},
                                     {"coolant_temp", 92.0},
                                     {"gear_ratio", 3.2},
                                     {"oil_pressure", 2.6},
                                     {"fuel_pressure", 4.2},
                                     {"boost_kpa", 120.0},
                                     {"lambda_current", 0.94},
                                     {"lambda_target", 0.92},
                                     {"battery_voltage", 12.9},
                                     {"oil_temp", 102.0},
                                     {"ambient_temp", 27.0},
                                     {"throttle", throttle.value}},
                        .digital = {{"pit_limiter", false}},
                        .ambient_lux = 18000.0};
}

} // namespace

void demo_runtime() {
    Runtime runtime;
    auto palette = motec_palette();
    auto profile = build_demo_profile(palette);

    runtime.load_profile(profile);
    runtime.display().set_overlay_widget([](const SignalBus &bus) {
        auto rpm = bus.get_numeric("rpm").value_or(0.0);
        auto shift = bus.get_numeric("shift_light_level").value_or(0.0);
        std::cout << "Render overlay: shift lights " << shift * 100 << "% | rpm " << rpm << "\n";
    });

    runtime.logger().record("boot: TouchGFX demo runtime started");
    runtime.logger().record("display: default " + profile.default_screen);

    auto base = base_inputs();
    runtime.ingest(base);
    runtime.step();
    runtime.logger().record("render: base frame");

    DebouncedInput pit_button{"pit", false, 0, 2};
    pit_button.update(true);
    pit_button.update(true);

    RuntimeInputs lap_attack = base;
    lap_attack.numeric["rpm"] = 8450;
    lap_attack.numeric["oil_pressure"] = 1.3;
    lap_attack.numeric["boost_kpa"] = 185.0;
    lap_attack.numeric["lambda_current"] = 1.02;
    lap_attack.numeric["lambda_target"] = 0.9;
    lap_attack.numeric["fuel_pressure"] = 3.0;
    lap_attack.numeric["throttle"] = 98.0;
    lap_attack.digital["pit_limiter"] = pit_button.state;
    lap_attack.brightness_override = 40.0;
    runtime.ingest(lap_attack);
    runtime.step();
    runtime.logger().record("render: lap attack frame");

    RuntimeInputs video_mode = lap_attack;
    video_mode.external_source = ExternalVideoSource::HDMI;
    runtime.ingest(video_mode);
    runtime.step();
    runtime.logger().record("external video: HDMI active");

    RuntimeInputs carplay = video_mode;
    carplay.external_source = ExternalVideoSource::CarPlay;
    runtime.ingest(carplay);
    runtime.step();
    runtime.logger().record("external video: CarPlay active");

    std::cout << "[BRIGHTNESS] backlight=" << runtime.brightness_controller().current_percent() << "%\n";
    runtime.logger().flush();
}

} // namespace firmware
