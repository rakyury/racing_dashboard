#pragma once

#include <string>

namespace firmware {

enum class ExternalVideoSource {
    None,
    HDMI,
    CarPlay,
    AndroidAuto,
};

class ExternalInputManager {
  public:
    void set_source(ExternalVideoSource source);
    ExternalVideoSource current() const;
    void process_frame() const;
    void negotiate_carplay_session();
    void negotiate_android_auto_session();

  private:
    static std::string source_to_string(ExternalVideoSource source);
    ExternalVideoSource source_{ExternalVideoSource::None};
};

} // namespace firmware
