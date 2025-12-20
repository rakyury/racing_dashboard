#pragma once

#include <memory>
#include <string>
#include <vector>

#include "screen.h"
#include "signal_bus.h"

namespace firmware {

struct TouchGFXPalette {
    std::string name{"Motec-inspired dark"};
    std::string background{"#0c0f12"};
    std::string accent{"#ff4300"};
    std::string success{"#3ddc97"};
    std::string warning{"#ffb703"};
    std::string critical{"#ff3366"};
};

class TouchGFXWidget {
  public:
    virtual ~TouchGFXWidget() = default;
    virtual void render(const SignalBus &bus, const TouchGFXPalette &palette) const = 0;
};

class RadialGauge : public TouchGFXWidget {
  public:
    RadialGauge(std::string channel, std::string label, std::string unit, double min, double max);
    void render(const SignalBus &bus, const TouchGFXPalette &) const override;

  private:
    std::string channel_;
    std::string label_;
    std::string unit_;
    double min_;
    double max_;
};

class LinearBar : public TouchGFXWidget {
  public:
    LinearBar(std::string channel, std::string label, std::string unit, double max);
    void render(const SignalBus &bus, const TouchGFXPalette &) const override;

  private:
    std::string channel_;
    std::string label_;
    std::string unit_;
    double max_;
};

class StatusPill : public TouchGFXWidget {
  public:
    StatusPill(std::string channel, std::string label, std::string unit, double warn, double crit);
    void render(const SignalBus &bus, const TouchGFXPalette &palette) const override;

  private:
    std::string channel_;
    std::string label_;
    std::string unit_;
    double warn_;
    double crit_;
};

class MixtureGraph : public TouchGFXWidget {
  public:
    MixtureGraph(std::string current_channel, std::string target_channel);
    void render(const SignalBus &bus, const TouchGFXPalette &palette) const override;

  private:
    std::string current_channel_;
    std::string target_channel_;
};

class TouchGFXScreen {
  public:
    TouchGFXScreen(std::string id, std::string title, std::vector<std::shared_ptr<TouchGFXWidget>> widgets);
    Screen to_runtime_screen(const TouchGFXPalette &palette) const;

  private:
    std::string id_;
    std::string title_;
    std::vector<std::shared_ptr<TouchGFXWidget>> widgets_;
};

} // namespace firmware
