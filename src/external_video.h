#pragma once

typedef enum {
    EXTERNAL_NONE = 0,
    EXTERNAL_HDMI = 1,
    EXTERNAL_CARPLAY = 2,
    EXTERNAL_ANDROID_AUTO = 3
} ExternalVideoSource;

typedef struct {
    ExternalVideoSource source;
} ExternalInputManager;

void external_input_init(ExternalInputManager *mgr);
void external_input_set_source(ExternalInputManager *mgr, ExternalVideoSource source);
const char *external_input_label(ExternalVideoSource source);

