#pragma once

#include <stddef.h>

#include "logic.h"
#include "screen.h"
#include "signal_bus.h"

typedef struct {
    Screen screens[16];
    size_t screen_count;
    LogicRoute routes[32];
    size_t route_count;
    char current[32];
    ScreenRenderFn overlay;
} DisplayManager;

void display_manager_init(DisplayManager *mgr);
void display_register_screen(DisplayManager *mgr, const Screen *screen);
void display_set_default(DisplayManager *mgr, const char *screen_id);
void display_register_route(DisplayManager *mgr, const LogicRoute *route);
void display_set_overlay(DisplayManager *mgr, ScreenRenderFn overlay);
void display_tick(DisplayManager *mgr, const SignalBus *bus);

