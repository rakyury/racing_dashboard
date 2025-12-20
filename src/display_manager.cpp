#include "display_manager.h"

#include <algorithm>
#include <iostream>

#include "signal_bus.h"

namespace firmware {

void DisplayManager::register_screen(Screen screen) { screens_.push_back(std::move(screen)); }

void DisplayManager::set_default_screen(const std::string &id) { default_screen_id_ = id; }

void DisplayManager::register_condition(const LogicCondition &condition, const std::string &target_screen_id) {
    conditions_.push_back({condition, target_screen_id});
    std::sort(conditions_.begin(), conditions_.end(), [](const ConditionEntry &a, const ConditionEntry &b) {
        return a.condition.priority < b.condition.priority;
    });
}

void DisplayManager::tick(const SignalBus &bus, const ExternalInputManager &external_input) {
    if (external_input.current() != ExternalVideoSource::None) {
        if (auto overlay = overlay_widget_) overlay(bus);
        external_input.process_frame();
        return;
    }

    for (const auto &entry : conditions_) {
        if (entry.condition.predicate(bus)) {
            switch_to(entry.target_screen_id, bus);
            return;
        }
    }

    switch_to(default_screen_id_, bus);
}

void DisplayManager::set_overlay_widget(std::function<void(const SignalBus &)> widget) {
    overlay_widget_ = std::move(widget);
}

void DisplayManager::switch_to(const std::string &screen_id, const SignalBus &bus) {
    auto it = std::find_if(screens_.begin(), screens_.end(), [&](const Screen &s) { return s.id == screen_id; });
    if (it == screens_.end()) return;
    if (current_screen_ != screen_id) {
        current_screen_ = screen_id;
        std::cout << "[DISPLAY] Switched to screen: " << it->title << "\n";
    }
    it->render(bus);
}

} // namespace firmware
