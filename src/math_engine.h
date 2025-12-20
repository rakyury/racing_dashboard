#pragma once

#include <functional>
#include <string>
#include <vector>

#include "signal_bus.h"

namespace firmware {

struct MathChannel {
    std::string id;
    std::function<double(const SignalBus &)> compute;
};

class MathEngine {
  public:
    void register_channel(MathChannel channel);
    void evaluate(SignalBus &bus) const;

  private:
    std::vector<MathChannel> channels_{};
};

} // namespace firmware
