#pragma once

#include <functional>
#include <string>
#include <vector>

#include "external_video.h"
#include "logic.h"
#include "screen.h"

namespace firmware {

class DisplayManager {
  public:
    void register_screen(Screen screen);
    void set_default_screen(const std::string &id);
    void register_condition(const LogicCondition &condition, const std::string &target_screen_id);
    void tick(const SignalBus &bus, const ExternalInputManager &external_input);
    void set_overlay_widget(std::function<void(const SignalBus &)> widget);

  private:
    struct ConditionEntry {
        LogicCondition condition;
        std::string target_screen_id;
    };

    void switch_to(const std::string &screen_id, const SignalBus &bus);

    std::vector<Screen> screens_{};
    std::vector<ConditionEntry> conditions_{};
    std::string current_screen_{};
    std::string default_screen_id_{};
    std::function<void(const SignalBus &)> overlay_widget_{};
};

} // namespace firmware
