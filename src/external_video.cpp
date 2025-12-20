#include "external_video.h"

#include <iostream>

namespace firmware {

void ExternalInputManager::set_source(ExternalVideoSource source) {
    source_ = source;
    std::cout << "External source set to " << source_to_string(source_) << "\n";
}

ExternalVideoSource ExternalInputManager::current() const { return source_; }

void ExternalInputManager::process_frame() const {
    if (source_ == ExternalVideoSource::None) return;
    std::cout << "[VIDEO] Rendering external frame from " << source_to_string(source_) << " with overlay\n";
}

void ExternalInputManager::negotiate_carplay_session() { set_source(ExternalVideoSource::CarPlay); }

void ExternalInputManager::negotiate_android_auto_session() { set_source(ExternalVideoSource::AndroidAuto); }

std::string ExternalInputManager::source_to_string(ExternalVideoSource source) {
    switch (source) {
    case ExternalVideoSource::HDMI:
        return "HDMI";
    case ExternalVideoSource::CarPlay:
        return "CarPlay";
    case ExternalVideoSource::AndroidAuto:
        return "AndroidAuto";
    default:
        return "None";
    }
}

} // namespace firmware
