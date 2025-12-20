#include "math_engine.h"

namespace firmware {

void MathEngine::register_channel(MathChannel channel) { channels_.push_back(std::move(channel)); }

void MathEngine::evaluate(SignalBus &bus) const {
    for (const auto &ch : channels_) {
        bus.set_numeric(ch.id, ch.compute(bus));
    }
}

} // namespace firmware
