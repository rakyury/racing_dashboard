#include "external_video.h"

void external_input_init(ExternalInputManager *mgr) { mgr->source = EXTERNAL_NONE; }

void external_input_set_source(ExternalInputManager *mgr, ExternalVideoSource source) { mgr->source = source; }

const char *external_input_label(ExternalVideoSource source) {
    switch (source) {
    case EXTERNAL_HDMI:
        return "HDMI";
    case EXTERNAL_CARPLAY:
        return "CarPlay";
    case EXTERNAL_ANDROID_AUTO:
        return "Android Auto";
    default:
        return "None";
    }
}

