#include "touchgfx_widgets.h"

#include <algorithm>
#include <iostream>

namespace firmware {

RadialGauge::RadialGauge(std::string channel, std::string label, std::string unit, double min, double max)
    : channel_(std::move(channel)), label_(std::move(label)), unit_(std::move(unit)), min_(min), max_(max) {}

void RadialGauge::render(const SignalBus &bus, const TouchGFXPalette &) const {
    auto value = bus.get_numeric(channel_).value_or(0.0);
    double pct = std::clamp((value - min_) / (max_ - min_), 0.0, 1.0);
    std::cout << "  [Gauge] " << label_ << ": " << value << unit_ << " (" << pct * 100 << "%)\n";
}

LinearBar::LinearBar(std::string channel, std::string label, std::string unit, double max)
    : channel_(std::move(channel)), label_(std::move(label)), unit_(std::move(unit)), max_(max) {}

void LinearBar::render(const SignalBus &bus, const TouchGFXPalette &) const {
    auto value = bus.get_numeric(channel_).value_or(0.0);
    double pct = std::clamp(value / max_, 0.0, 1.0);
    std::cout << "  [Bar]   " << label_ << ": " << value << unit_ << " (" << pct * 100 << "%)\n";
}

StatusPill::StatusPill(std::string channel, std::string label, std::string unit, double warn, double crit)
    : channel_(std::move(channel)), label_(std::move(label)), unit_(std::move(unit)), warn_(warn), crit_(crit) {}

void StatusPill::render(const SignalBus &bus, const TouchGFXPalette &palette) const {
    auto value = bus.get_numeric(channel_).value_or(0.0);
    std::string color = value <= crit_ ? palette.critical : (value <= warn_ ? palette.warning : palette.success);
    std::cout << "  [Pill]  " << label_ << ": " << value << unit_ << " (" << color << ")\n";
}

MixtureGraph::MixtureGraph(std::string current_channel, std::string target_channel)
    : current_channel_(std::move(current_channel)), target_channel_(std::move(target_channel)) {}

void MixtureGraph::render(const SignalBus &bus, const TouchGFXPalette &palette) const {
    auto cur = bus.get_numeric(current_channel_).value_or(0.0);
    auto tgt = bus.get_numeric(target_channel_).value_or(0.0);
    std::string trend = cur > tgt ? palette.warning : palette.success;
    std::cout << "  [Graph] AFR current=" << cur << " target=" << tgt << " trend color " << trend << "\n";
}

TouchGFXScreen::TouchGFXScreen(std::string id, std::string title, std::vector<std::shared_ptr<TouchGFXWidget>> widgets)
    : id_(std::move(id)), title_(std::move(title)), widgets_(std::move(widgets)) {}

Screen TouchGFXScreen::to_runtime_screen(const TouchGFXPalette &palette) const {
    auto widgets = widgets_;
    auto title = title_;
    auto palette_copy = palette;
    return Screen{ id_, title_, [widgets, title, palette_copy](const SignalBus &bus) {
                       std::cout << "[TouchGFX] " << title << " | palette " << palette_copy.name << "\n";
                       for (const auto &w : widgets) {
                           w->render(bus, palette_copy);
                       }
                   }};
}

} // namespace firmware
