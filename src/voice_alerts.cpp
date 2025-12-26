#include "voice_alerts.h"
#include <Arduino.h>
#include <string.h>
#include <stdio.h>
#include <stdarg.h>

// ============================================================================
// Public API Implementation
// ============================================================================

bool voice_alerts_init(VoiceAlertSystem *voice, const VoiceConfig *config) {
    if (!voice || !config) return false;

    memset(voice, 0, sizeof(VoiceAlertSystem));
    memcpy(&voice->config, config, sizeof(VoiceConfig));

    voice->queue.head = 0;
    voice->queue.tail = 0;
    voice->queue.count = 0;
    voice->is_muted = false;
    voice->is_speaking = false;

    Serial.println("[VOICE] Initialized");
    return true;
}

void voice_alerts_deinit(VoiceAlertSystem *voice) {
    if (!voice) return;

    voice_alert_clear_queue(voice);
    voice->is_speaking = false;
}

void voice_alerts_update(VoiceAlertSystem *voice) {
    if (!voice || voice->is_muted || voice->queue.count == 0) return;

    // Process queue
    if (!voice->is_speaking && voice->queue.count > 0) {
        VoiceAlert *alert = &voice->queue.alerts[voice->queue.head];

        // TODO: Implement actual TTS playback
        Serial.printf("[VOICE] %s\n", alert->message);

        alert->is_spoken = true;
        voice->queue.head = (voice->queue.head + 1) % VOICE_MAX_QUEUE_SIZE;
        voice->queue.count--;
        voice->total_alerts_spoken++;
        voice->last_alert_time_ms = millis();
    }
}

bool voice_alerts_is_speaking(const VoiceAlertSystem *voice) {
    return voice ? voice->is_speaking : false;
}

void voice_alerts_set_mute(VoiceAlertSystem *voice, bool mute) {
    if (voice) {
        voice->is_muted = mute;
        Serial.printf("[VOICE] Mute: %s\n", mute ? "ON" : "OFF");
    }
}

bool voice_alerts_is_muted(const VoiceAlertSystem *voice) {
    return voice ? voice->is_muted : true;
}

bool voice_alert_queue(VoiceAlertSystem *voice, AlertType type,
                      VoicePriority priority, const char *message) {
    if (!voice || !message) return false;

    if (voice->queue.count >= VOICE_MAX_QUEUE_SIZE) {
        voice->alerts_dropped++;
        return false;
    }

    VoiceAlert *alert = &voice->queue.alerts[voice->queue.tail];
    alert->type = type;
    alert->priority = priority;
    strncpy(alert->message, message, sizeof(alert->message) - 1);
    alert->timestamp_ms = millis();
    alert->is_spoken = false;

    voice->queue.tail = (voice->queue.tail + 1) % VOICE_MAX_QUEUE_SIZE;
    voice->queue.count++;

    return true;
}

bool voice_alert_queue_formatted(VoiceAlertSystem *voice, AlertType type,
                                 VoicePriority priority, const char *format, ...) {
    if (!voice || !format) return false;

    char message[VOICE_MAX_MESSAGE_LEN];
    va_list args;
    va_start(args, format);
    vsnprintf(message, sizeof(message), format, args);
    va_end(args);

    return voice_alert_queue(voice, type, priority, message);
}

void voice_alert_clear_queue(VoiceAlertSystem *voice) {
    if (voice) {
        voice->queue.head = 0;
        voice->queue.tail = 0;
        voice->queue.count = 0;
    }
}

void voice_alert_stop_current(VoiceAlertSystem *voice) {
    if (voice) {
        voice->is_speaking = false;
    }
}

size_t voice_alert_get_queue_depth(const VoiceAlertSystem *voice) {
    return voice ? voice->queue.count : 0;
}

// ============================================================================
// Racing Callouts
// ============================================================================

bool voice_announce_lap_time(VoiceAlertSystem *voice, uint32_t lap_number,
                             uint64_t lap_time_ms) {
    if (!voice) return false;

    char message[VOICE_MAX_MESSAGE_LEN];
    int minutes = lap_time_ms / 60000;
    int seconds = (lap_time_ms / 1000) % 60;
    int millis = lap_time_ms % 1000;

    snprintf(message, sizeof(message),
             "Lap %u, %d minute%s %d point %d seconds",
             lap_number,
             minutes,
             minutes != 1 ? "s" : "",
             seconds,
             millis / 100);

    return voice_alert_queue(voice, ALERT_TYPE_LAP_TIME, VOICE_PRIORITY_NORMAL, message);
}

bool voice_announce_delta(VoiceAlertSystem *voice, int32_t delta_ms) {
    if (!voice) return false;

    char message[VOICE_MAX_MESSAGE_LEN];
    float delta_s = abs(delta_ms) / 1000.0f;

    if (delta_ms < 0) {
        snprintf(message, sizeof(message), "%.2f seconds ahead", delta_s);
    } else {
        snprintf(message, sizeof(message), "%.2f seconds behind", delta_s);
    }

    return voice_alert_queue(voice, ALERT_TYPE_DELTA, VOICE_PRIORITY_NORMAL, message);
}

bool voice_announce_best_lap(VoiceAlertSystem *voice, uint64_t lap_time_ms) {
    if (!voice) return false;

    char message[VOICE_MAX_MESSAGE_LEN];
    int minutes = lap_time_ms / 60000;
    int seconds = (lap_time_ms / 1000) % 60;
    int millis = lap_time_ms % 1000;

    snprintf(message, sizeof(message),
             "Best lap! %d:%02d.%03d",
             minutes, seconds, millis);

    return voice_alert_queue(voice, ALERT_TYPE_BEST_LAP, VOICE_PRIORITY_HIGH, message);
}

bool voice_announce_shift_now(VoiceAlertSystem *voice) {
    return voice_alert_queue(voice, ALERT_TYPE_SHIFT_POINT,
                            VOICE_PRIORITY_HIGH, "Shift now!");
}

bool voice_announce_pit_limiter(VoiceAlertSystem *voice, bool enabled) {
    return voice_alert_queue(voice, ALERT_TYPE_PIT_LIMITER,
                            VOICE_PRIORITY_NORMAL,
                            enabled ? "Pit limiter on" : "Pit limiter off");
}

bool voice_announce_fuel_status(VoiceAlertSystem *voice, uint32_t laps_remaining) {
    if (!voice) return false;

    char message[VOICE_MAX_MESSAGE_LEN];
    snprintf(message, sizeof(message),
             "Low fuel, %u lap%s remaining",
             laps_remaining,
             laps_remaining != 1 ? "s" : "");

    return voice_alert_queue(voice, ALERT_TYPE_FUEL_LOW,
                            VOICE_PRIORITY_HIGH, message);
}

bool voice_announce_temperature_warning(VoiceAlertSystem *voice,
                                       float temp_c, bool critical) {
    if (!voice) return false;

    char message[VOICE_MAX_MESSAGE_LEN];
    snprintf(message, sizeof(message),
             "%s coolant temperature, %.0f degrees",
             critical ? "Critical" : "High",
             temp_c);

    return voice_alert_queue(voice, ALERT_TYPE_TEMPERATURE_HIGH,
                            critical ? VOICE_PRIORITY_CRITICAL : VOICE_PRIORITY_HIGH,
                            message);
}

bool voice_announce_oil_pressure_warning(VoiceAlertSystem *voice,
                                        float pressure_psi, bool critical) {
    if (!voice) return false;

    char message[VOICE_MAX_MESSAGE_LEN];
    snprintf(message, sizeof(message),
             "%s oil pressure, %.0f PSI%s",
             critical ? "Critical" : "Low",
             pressure_psi,
             critical ? ", pit immediately" : "");

    return voice_alert_queue(voice, ALERT_TYPE_OIL_PRESSURE_LOW,
                            critical ? VOICE_PRIORITY_CRITICAL : VOICE_PRIORITY_HIGH,
                            message);
}

// ============================================================================
// Utilities
// ============================================================================

void voice_format_lap_time(uint64_t lap_time_ms, char *output, size_t output_size) {
    int minutes = lap_time_ms / 60000;
    int seconds = (lap_time_ms / 1000) % 60;
    int millis = lap_time_ms % 1000;

    snprintf(output, output_size, "%d:%02d.%03d", minutes, seconds, millis);
}

void voice_format_delta(int32_t delta_ms, char *output, size_t output_size) {
    float delta_s = abs(delta_ms) / 1000.0f;

    if (delta_ms < 0) {
        snprintf(output, output_size, "+%.2f s", delta_s);
    } else {
        snprintf(output, output_size, "-%.2f s", delta_s);
    }
}

const char* voice_language_to_string(VoiceLanguage language) {
    switch (language) {
        case VOICE_LANG_ENGLISH_US: return "English (US)";
        case VOICE_LANG_ENGLISH_UK: return "English (UK)";
        case VOICE_LANG_RUSSIAN: return "Russian";
        case VOICE_LANG_GERMAN: return "German";
        case VOICE_LANG_FRENCH: return "French";
        case VOICE_LANG_SPANISH: return "Spanish";
        case VOICE_LANG_ITALIAN: return "Italian";
        case VOICE_LANG_JAPANESE: return "Japanese";
        default: return "Unknown";
    }
}

const char* voice_engine_to_string(VoiceEngine engine) {
    switch (engine) {
        case VOICE_ENGINE_TTS_GOOGLE: return "Google TTS";
        case VOICE_ENGINE_TTS_ESPEAK: return "eSpeak";
        case VOICE_ENGINE_TTS_FLITE: return "Festival Lite";
        case VOICE_ENGINE_PRERECORDED: return "Prerecorded";
        default: return "None";
    }
}

const char* voice_get_last_error(const VoiceAlertSystem *voice) {
    return voice ? voice->last_error : "";
}

void voice_set_speech_rate(VoiceAlertSystem *voice, float rate) {
    if (voice) {
        voice->config.speech_rate = rate;
    }
}

void voice_set_volume(VoiceAlertSystem *voice, uint8_t volume_percent) {
    if (voice) {
        voice->config.volume_percent = volume_percent;
    }
}
