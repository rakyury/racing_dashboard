#include "runtime.h"

#include <stdio.h>
#include <string.h>
#include <sys/time.h>

#include "filters.h"

static uint64_t now_ms(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (uint64_t)tv.tv_sec * 1000ULL + (uint64_t)(tv.tv_usec / 1000ULL);
}

void runtime_init(Runtime *rt) {
    signal_bus_init(&rt->bus);
    display_manager_init(&rt->display);
    alert_manager_init(&rt->alerts);
    math_engine_init(&rt->math_engine);
    health_monitor_init(&rt->health_monitor);
    brightness_init(&rt->brightness);
    data_logger_init(&rt->logger);
    external_input_init(&rt->external);
}

void runtime_load_profile(Runtime *rt, const RuntimeProfile *profile) {
    for (size_t i = 0; i < profile->screen_count; ++i) display_register_screen(&rt->display, &profile->screens[i]);
    display_set_default(&rt->display, profile->default_screen);

    for (size_t i = 0; i < profile->route_count; ++i) display_register_route(&rt->display, &profile->routes[i]);
    for (size_t i = 0; i < profile->alert_count; ++i) alert_manager_register(&rt->alerts, &profile->alerts[i]);
    for (size_t i = 0; i < profile->math_count; ++i) math_engine_register(&rt->math_engine, &profile->math[i]);
    for (size_t i = 0; i < profile->health_count; ++i) health_monitor_register(&rt->health_monitor, &profile->health[i]);
}

void runtime_ingest(Runtime *rt, const char *name, double value, uint64_t now, bool is_digital) {
    if (is_digital) {
        signal_bus_set_digital(&rt->bus, name, value > 0.5, now);
    } else {
        signal_bus_set_numeric(&rt->bus, name, value, now);
    }
}

void runtime_set_brightness(Runtime *rt, double lux, bool has_manual, double manual_percent) {
    if (has_manual) {
        brightness_set_manual(&rt->brightness, manual_percent);
    } else {
        brightness_clear_manual(&rt->brightness);
        brightness_update_from_lux(&rt->brightness, lux);
    }
}

void runtime_set_external(Runtime *rt, ExternalVideoSource source) { external_input_set_source(&rt->external, source); }

static void overlay_render(const SignalBus *bus) {
    double rpm = 0.0;
    signal_bus_get_numeric(bus, "rpm", &rpm);
    double shift = 0.0;
    signal_bus_get_numeric(bus, "shift_light", &shift);
    printf("[OVERLAY] RPM %.0f shift %.0f%%\n", rpm, shift * 100.0);
}

void runtime_step(Runtime *rt, uint64_t now) {
    math_engine_evaluate(&rt->math_engine, &rt->bus, now);
    alert_manager_evaluate(&rt->alerts, &rt->bus);
    health_monitor_evaluate(&rt->health_monitor, &rt->bus, &rt->logger, &rt->alerts, now);
    display_tick(&rt->display, &rt->bus);
    if (rt->external.source != EXTERNAL_NONE) {
        printf("[VIDEO] external source: %s\n", external_input_label(rt->external.source));
    }
}

// ---- Demo helpers ----

static bool cond_pit(const SignalBus *bus) {
    bool pit = false;
    signal_bus_get_digital(bus, "pit_limiter", &pit);
    return pit;
}

static bool cond_hot(const SignalBus *bus) {
    double t = 0.0;
    if (!signal_bus_get_numeric(bus, "coolant_temp", &t)) return false;
    return t > 112.0;
}

static bool cond_low_oil(const SignalBus *bus) {
    double p = 0.0;
    if (!signal_bus_get_numeric(bus, "oil_pressure", &p)) return false;
    return p < 1.5;
}

static void render_touchgfx_main(const SignalBus *bus) {
    double rpm = 0, speed = 0, coolant = 0, oil = 0, batt = 0, boost = 0, thr = 0;
    signal_bus_get_numeric(bus, "rpm", &rpm);
    signal_bus_get_numeric(bus, "speed_kph", &speed);
    signal_bus_get_numeric(bus, "coolant_temp", &coolant);
    signal_bus_get_numeric(bus, "oil_temp", &oil);
    signal_bus_get_numeric(bus, "battery_voltage", &batt);
    signal_bus_get_numeric(bus, "boost_kpa", &boost);
    signal_bus_get_numeric(bus, "throttle", &thr);
    printf("  RPM %.0f | Speed %.1f | Coolant %.1f | OilT %.1f | Batt %.1f | Boost %.1f | Thr %.0f%%\n", rpm, speed,
           coolant, oil, batt, boost, thr);
}

static void render_touchgfx_warning(const SignalBus *bus) {
    double oilp = 0, fuelp = 0, coolant = 0, oilt = 0;
    signal_bus_get_numeric(bus, "oil_pressure", &oilp);
    signal_bus_get_numeric(bus, "fuel_pressure", &fuelp);
    signal_bus_get_numeric(bus, "coolant_temp", &coolant);
    signal_bus_get_numeric(bus, "oil_temp", &oilt);
    printf("  OilP %.2f | FuelP %.2f | Coolant %.1f | OilT %.1f\n", oilp, fuelp, coolant, oilt);
}

static void render_touchgfx_race(const SignalBus *bus) {
    double rpm = 0, shift = 0, boost = 0, thr = 0;
    signal_bus_get_numeric(bus, "rpm", &rpm);
    signal_bus_get_numeric(bus, "shift_light", &shift);
    signal_bus_get_numeric(bus, "boost_kpa", &boost);
    signal_bus_get_numeric(bus, "throttle", &thr);
    printf("  Race: RPM %.0f | Shift %.0f%% | Boost %.1f | Thr %.0f%%\n", rpm, shift * 100.0, boost, thr);
}

static double math_speed(const SignalBus *bus) {
    double rpm = 0, gear = 0;
    if (!signal_bus_get_numeric(bus, "rpm", &rpm) || !signal_bus_get_numeric(bus, "gear_ratio", &gear) || gear == 0) return 0;
    return (rpm / gear) * 0.0021;
}

static double math_shift(const SignalBus *bus) {
    double rpm = 0;
    signal_bus_get_numeric(bus, "rpm", &rpm);
    double level = (rpm - 6200.0) / 2600.0;
    if (level < 0) level = 0;
    if (level > 1) level = 1;
    return level;
}

static double math_afr_error(const SignalBus *bus) {
    double cur = 0, tgt = 0;
    if (!signal_bus_get_numeric(bus, "lambda_current", &cur) || !signal_bus_get_numeric(bus, "lambda_target", &tgt)) return 0;
    return cur - tgt;
}

static RuntimeProfile build_touchgfx_profile(void) {
    RuntimeProfile p = {0};
    strncpy(p.default_screen, "main", sizeof(p.default_screen) - 1);

    Screen main = {"main", "TouchGFX Main", render_touchgfx_main};
    Screen warn = {"warning", "Warnings", render_touchgfx_warning};
    Screen race = {"race", "Race", render_touchgfx_race};
    p.screens[p.screen_count++] = main;
    p.screens[p.screen_count++] = warn;
    p.screens[p.screen_count++] = race;

    LogicRoute route_pit = {"pit", "Pit limiter", cond_pit, 5, "race"};
    LogicRoute route_hot = {"hot", "Coolant hot", cond_hot, 3, "warning"};
    LogicRoute route_oil = {"oil", "Oil low", cond_low_oil, 4, "warning"};
    p.routes[p.route_count++] = route_pit;
    p.routes[p.route_count++] = route_hot;
    p.routes[p.route_count++] = route_oil;

    Alert coolant = {"coolant_high", "Coolant temperature high", "coolant_temp", 112.0, ALERT_WARNING, true, false};
    Alert oilp = {"oil_pressure_low", "Oil pressure critical", "oil_pressure", 1.5, ALERT_CRITICAL, false, false};
    Alert battery = {"battery_low", "Battery voltage low", "battery_voltage", 12.0, ALERT_WARNING, false, false};
    Alert afr = {"afr_lean", "AFR lean vs target", "afr_error", 0.2, ALERT_WARNING, true, false};
    Alert rpm = {"rpm_limit", "Engine overrev", "rpm", 8500.0, ALERT_WARNING, true, false};
    p.alerts[p.alert_count++] = coolant;
    p.alerts[p.alert_count++] = oilp;
    p.alerts[p.alert_count++] = battery;
    p.alerts[p.alert_count++] = afr;
    p.alerts[p.alert_count++] = rpm;

    MathChannel speed = {"speed_kph", math_speed};
    MathChannel shift = {"shift_light", math_shift};
    MathChannel afr_err = {"afr_error", math_afr_error};
    p.math[p.math_count++] = speed;
    p.math[p.math_count++] = shift;
    p.math[p.math_count++] = afr_err;

    StaleSignalRule rpm_rule = {"rpm_stale", "rpm", 1500, ALERT_CRITICAL};
    StaleSignalRule coolant_rule = {"coolant_stale", "coolant_temp", 2500, ALERT_WARNING};
    p.health[p.health_count++] = rpm_rule;
    p.health[p.health_count++] = coolant_rule;

    return p;
}

// LVGL variation keeps same logic but different screen titles and order
static void render_lvgl_cluster(const SignalBus *bus) {
    double rpm = 0, boost = 0, throttle = 0, batt = 0;
    signal_bus_get_numeric(bus, "rpm", &rpm);
    signal_bus_get_numeric(bus, "boost_kpa", &boost);
    signal_bus_get_numeric(bus, "throttle", &throttle);
    signal_bus_get_numeric(bus, "battery_voltage", &batt);
    printf("  LVGL cluster -> RPM %.0f | Boost %.1f | Throttle %.0f%% | Batt %.1f\n", rpm, boost, throttle, batt);
}

static void render_lvgl_health(const SignalBus *bus) {
    double oilp = 0, fuelp = 0;
    signal_bus_get_numeric(bus, "oil_pressure", &oilp);
    signal_bus_get_numeric(bus, "fuel_pressure", &fuelp);
    printf("  LVGL health -> OilP %.2f | FuelP %.2f\n", oilp, fuelp);
}

static RuntimeProfile build_lvgl_profile(void) {
    RuntimeProfile p = {0};
    strncpy(p.default_screen, "cluster", sizeof(p.default_screen) - 1);
    Screen cluster = {"cluster", "LVGL Cluster", render_lvgl_cluster};
    Screen health = {"health", "LVGL Health", render_lvgl_health};
    p.screens[p.screen_count++] = cluster;
    p.screens[p.screen_count++] = health;

    LogicRoute route_oil = {"oil", "Oil low", cond_low_oil, 2, "health"};
    p.routes[p.route_count++] = route_oil;

    p.alerts[p.alert_count++] = (Alert){"oil_pressure_low", "Oil pressure critical", "oil_pressure", 1.5, ALERT_CRITICAL, false, false};
    p.alerts[p.alert_count++] = (Alert){"coolant_high", "Coolant temperature high", "coolant_temp", 112.0, ALERT_WARNING, true, false};
    p.math[p.math_count++] = (MathChannel){"shift_light", math_shift};
    p.math[p.math_count++] = (MathChannel){"afr_error", math_afr_error};
    p.health[p.health_count++] = (StaleSignalRule){"rpm_stale", "rpm", 1500, ALERT_CRITICAL};

    return p;
}

static void seed_base_signals(Runtime *rt, uint64_t now) {
    FilteredInput throttle = {"throttle", 0.0, 0.35, 0.5};
    filtered_input_update(&throttle, 30.0);
    filtered_input_update(&throttle, 42.0);

    runtime_ingest(rt, "rpm", 5200, now, false);
    runtime_ingest(rt, "coolant_temp", 92.0, now, false);
    runtime_ingest(rt, "gear_ratio", 3.2, now, false);
    runtime_ingest(rt, "oil_pressure", 2.6, now, false);
    runtime_ingest(rt, "fuel_pressure", 4.2, now, false);
    runtime_ingest(rt, "boost_kpa", 120.0, now, false);
    runtime_ingest(rt, "lambda_current", 0.94, now, false);
    runtime_ingest(rt, "lambda_target", 0.92, now, false);
    runtime_ingest(rt, "battery_voltage", 12.9, now, false);
    runtime_ingest(rt, "oil_temp", 102.0, now, false);
    runtime_ingest(rt, "ambient_temp", 27.0, now, false);
    runtime_ingest(rt, "throttle", throttle.value, now, false);
    runtime_ingest(rt, "pit_limiter", 0, now, true);
}

static void demo_sequence(Runtime *rt, const char *label) {
    uint64_t start = now_ms();
    printf("\n=== %s demo ===\n", label);
    seed_base_signals(rt, start);
    runtime_set_brightness(rt, 18000.0, false, 0);
    runtime_step(rt, start);
    data_logger_record(&rt->logger, "frame: base");

    uint64_t t1 = start + 200;
    runtime_ingest(rt, "rpm", 8450, t1, false);
    runtime_ingest(rt, "oil_pressure", 1.3, t1, false);
    runtime_ingest(rt, "boost_kpa", 185.0, t1, false);
    runtime_ingest(rt, "lambda_current", 1.02, t1, false);
    runtime_ingest(rt, "lambda_target", 0.9, t1, false);
    runtime_ingest(rt, "fuel_pressure", 3.0, t1, false);
    runtime_ingest(rt, "throttle", 98.0, t1, false);
    runtime_ingest(rt, "pit_limiter", 1, t1, true);
    runtime_set_brightness(rt, 0, true, 40.0);
    runtime_step(rt, t1);
    data_logger_record(&rt->logger, "frame: lap attack");

    uint64_t t2 = t1 + 100;
    runtime_set_external(rt, EXTERNAL_HDMI);
    runtime_step(rt, t2);
    data_logger_record(&rt->logger, "video: HDMI");

    uint64_t t3 = t2 + 100;
    runtime_set_external(rt, EXTERNAL_CARPLAY);
    runtime_step(rt, t3);
    data_logger_record(&rt->logger, "video: CarPlay");

    printf("[BRIGHTNESS] %.1f%%\n", rt->brightness.current_percent);
    data_logger_flush(&rt->logger);
}

void demo_touchgfx(Runtime *rt, uint64_t now) {
    (void)now;
    RuntimeProfile p = build_touchgfx_profile();
    runtime_load_profile(rt, &p);
    display_set_overlay(&rt->display, overlay_render);
    demo_sequence(rt, "TouchGFX");
}

void demo_lvgl(Runtime *rt, uint64_t now) {
    (void)now;
    RuntimeProfile p = build_lvgl_profile();
    runtime_load_profile(rt, &p);
    display_set_overlay(&rt->display, overlay_render);
    demo_sequence(rt, "LVGL");
}

