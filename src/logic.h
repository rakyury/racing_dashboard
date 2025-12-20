#pragma once

#include <functional>
#include <string>

namespace firmware {

struct SignalBus;

struct LogicCondition {
    std::string id;
    std::string description;
    std::function<bool(const SignalBus &)> predicate;
    int priority{100}; // lower value = higher priority
};

} // namespace firmware
