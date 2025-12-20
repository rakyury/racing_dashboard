#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "alerts.h"
#include "brightness_controller.h"
#include "data_logger.h"
#include "display_manager.h"
#include "external_video.h"
#include "health_monitor.h"
#include "logic.h"
#include "math_engine.h"
#include "signal_bus.h"

typedef struct {
    char default_screen[32];
    Screen screens[16];
    size_t screen_count;
    LogicRoute routes[32];
    size_t route_count;
    Alert alerts[32];
    size_t alert_count;
    MathChannel math[32];
    size_t math_count;
    StaleSignalRule health[16];
    size_t health_count;
} RuntimeProfile;

typedef struct {
    SignalBus bus;
    DisplayManager display;
    AlertManager alerts;
    MathEngine math_engine;
    HealthMonitor health_monitor;
    BrightnessController brightness;
    DataLogger logger;
    ExternalInputManager external;
} Runtime;

void runtime_init(Runtime *rt);
void runtime_load_profile(Runtime *rt, const RuntimeProfile *profile);
void runtime_ingest(Runtime *rt, const char *name, double value, uint64_t now_ms, bool is_digital);
void runtime_set_brightness(Runtime *rt, double lux, bool has_manual, double manual_percent);
void runtime_set_external(Runtime *rt, ExternalVideoSource source);
void runtime_step(Runtime *rt, uint64_t now_ms);

void demo_touchgfx(Runtime *rt, uint64_t now_ms);
void demo_lvgl(Runtime *rt, uint64_t now_ms);

