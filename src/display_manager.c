#include "display_manager.h"

#include <stdio.h>
#include <string.h>

void display_manager_init(DisplayManager *mgr) {
    mgr->screen_count = 0;
    mgr->route_count = 0;
    mgr->current[0] = '\0';
    mgr->overlay = NULL;
}

void display_register_screen(DisplayManager *mgr, const Screen *screen) {
    if (mgr->screen_count >= 16) return;
    mgr->screens[mgr->screen_count++] = *screen;
}

void display_set_default(DisplayManager *mgr, const char *screen_id) {
    strncpy(mgr->current, screen_id, sizeof(mgr->current) - 1);
    mgr->current[sizeof(mgr->current) - 1] = '\0';
}

void display_register_route(DisplayManager *mgr, const LogicRoute *route) {
    if (mgr->route_count >= 32) return;
    mgr->routes[mgr->route_count++] = *route;
}

void display_set_overlay(DisplayManager *mgr, ScreenRenderFn overlay) { mgr->overlay = overlay; }

static const Screen *find_screen(const DisplayManager *mgr, const char *id) {
    for (size_t i = 0; i < mgr->screen_count; ++i) {
        if (strcmp(mgr->screens[i].id, id) == 0) return &mgr->screens[i];
    }
    return NULL;
}

void display_tick(DisplayManager *mgr, const SignalBus *bus) {
    // evaluate routes by priority highest first
    int best_priority = -2147483647;
    const char *selected = mgr->current;
    for (size_t i = 0; i < mgr->route_count; ++i) {
        const LogicRoute *route = &mgr->routes[i];
        if (route->eval && route->eval(bus) && route->priority >= best_priority) {
            best_priority = route->priority;
            selected = route->target_screen;
        }
    }

    strncpy(mgr->current, selected, sizeof(mgr->current) - 1);
    mgr->current[sizeof(mgr->current) - 1] = '\0';

    const Screen *screen = find_screen(mgr, mgr->current);
    if (screen && screen->render) {
        printf("[DISPLAY] %s (%s)\n", screen->title, screen->id);
        screen->render(bus);
    }
    if (mgr->overlay) mgr->overlay(bus);
}

