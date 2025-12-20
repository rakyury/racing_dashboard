#pragma once

#include <functional>
#include <string>

namespace firmware {

struct SignalBus;

struct Screen {
    std::string id;
    std::string title;
    std::function<void(const SignalBus &)> render;
};

} // namespace firmware
