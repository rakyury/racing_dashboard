#pragma once

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @file voice_alerts.h
 * @brief Voice Alert System with Text-to-Speech
 *
 * Features:
 * - Text-to-Speech (TTS) for critical alerts
 * - Pre-recorded audio messages
 * - Bluetooth audio output
 * - Multi-language support
 * - Priority-based alert queue
 * - Configurable voice settings
 * - Racing-specific callouts (lap times, deltas, alerts)
 */

// ============================================================================
// Constants
// ============================================================================

#define VOICE_MAX_MESSAGE_LEN 256
#define VOICE_MAX_QUEUE_SIZE 32
#define VOICE_MAX_PRESETS 64

// ============================================================================
// Enumerations
// ============================================================================

typedef enum {
    VOICE_ENGINE_TTS_GOOGLE,        // Google TTS (cloud)
    VOICE_ENGINE_TTS_ESPEAK,        // eSpeak (offline)
    VOICE_ENGINE_TTS_FLITE,         // Festival Lite (offline)
    VOICE_ENGINE_PRERECORDED,       // Pre-recorded audio files
    VOICE_ENGINE_NONE
} VoiceEngine;

typedef enum {
    VOICE_LANG_ENGLISH_US,
    VOICE_LANG_ENGLISH_UK,
    VOICE_LANG_RUSSIAN,
    VOICE_LANG_GERMAN,
    VOICE_LANG_FRENCH,
    VOICE_LANG_SPANISH,
    VOICE_LANG_ITALIAN,
    VOICE_LANG_JAPANESE
} VoiceLanguage;

typedef enum {
    VOICE_GENDER_MALE,
    VOICE_GENDER_FEMALE,
    VOICE_GENDER_NEUTRAL
} VoiceGender;

typedef enum {
    VOICE_PRIORITY_LOW,
    VOICE_PRIORITY_NORMAL,
    VOICE_PRIORITY_HIGH,
    VOICE_PRIORITY_CRITICAL
} VoicePriority;

typedef enum {
    VOICE_OUTPUT_BLUETOOTH,
    VOICE_OUTPUT_SPEAKER,
    VOICE_OUTPUT_HEADPHONE_JACK,
    VOICE_OUTPUT_USB_AUDIO
} VoiceOutput;

typedef enum {
    ALERT_TYPE_LAP_TIME,            // "Lap 5, one minute thirty-two point three"
    ALERT_TYPE_DELTA,               // "Two seconds ahead"
    ALERT_TYPE_BEST_LAP,            // "Best lap!"
    ALERT_TYPE_SHIFT_POINT,         // "Shift now!"
    ALERT_TYPE_PIT_LIMITER,         // "Pit limiter on"
    ALERT_TYPE_FUEL_LOW,            // "Low fuel, 5 laps remaining"
    ALERT_TYPE_TEMPERATURE_HIGH,    // "High coolant temperature"
    ALERT_TYPE_OIL_PRESSURE_LOW,    // "Low oil pressure, pit immediately"
    ALERT_TYPE_SPEED_WARNING,       // "Reduce speed"
    ALERT_TYPE_TRACK_LIMITS,        // "Track limits violation"
    ALERT_TYPE_CUSTOM
} AlertType;

// ============================================================================
// Structures
// ============================================================================

typedef struct {
    VoiceEngine engine;
    VoiceLanguage language;
    VoiceGender gender;
    VoiceOutput output;

    // Voice characteristics
    float speech_rate;              // 0.5-2.0 (1.0 = normal)
    float pitch;                    // 0.5-2.0 (1.0 = normal)
    uint8_t volume_percent;         // 0-100

    // TTS cloud settings (for Google TTS)
    char api_key[64];
    bool use_cloud_tts;

    // Audio settings
    uint16_t sample_rate_hz;        // 16000, 22050, 44100
    uint8_t bit_depth;              // 8 or 16

    // Bluetooth
    char bluetooth_device_name[32];
    char bluetooth_mac_address[18];
    bool auto_connect_bluetooth;

    // Behavior
    bool interrupt_on_critical;     // Interrupt current message for critical
    bool repeat_critical_alerts;
    uint32_t min_repeat_interval_ms;
    bool mute_during_recording;     // Mute if camera recording
} VoiceConfig;

typedef struct {
    AlertType type;
    VoicePriority priority;
    char message[VOICE_MAX_MESSAGE_LEN];
    uint64_t timestamp_ms;
    bool is_spoken;
} VoiceAlert;

typedef struct {
    VoiceAlert alerts[VOICE_MAX_QUEUE_SIZE];
    size_t head;
    size_t tail;
    size_t count;
} VoiceAlertQueue;

typedef struct {
    AlertType type;
    char audio_file_path[128];
} PrerecordedMessage;

typedef struct {
    VoiceConfig config;
    VoiceAlertQueue queue;

    // TTS engine
    void *tts_engine;               // Platform-specific TTS handle

    // Bluetooth
    void *bluetooth_handle;
    bool bluetooth_connected;

    // Prerecorded messages
    PrerecordedMessage presets[VOICE_MAX_PRESETS];
    size_t preset_count;

    // State
    bool is_speaking;
    bool is_muted;
    VoiceAlert *current_alert;

    // Statistics
    uint32_t total_alerts_spoken;
    uint32_t alerts_dropped;        // Dropped due to full queue
    uint64_t last_alert_time_ms;

    // Error
    char last_error[128];
} VoiceAlertSystem;

// ============================================================================
// Public API - Core Functions
// ============================================================================

/**
 * @brief Initialize voice alert system
 * @param voice Voice alert system instance
 * @param config Configuration parameters
 * @return true if successfully initialized
 */
bool voice_alerts_init(VoiceAlertSystem *voice, const VoiceConfig *config);

/**
 * @brief Deinitialize voice alert system
 * @param voice Voice alert system instance
 */
void voice_alerts_deinit(VoiceAlertSystem *voice);

/**
 * @brief Update voice alert system (call from main loop)
 * @param voice Voice alert system instance
 */
void voice_alerts_update(VoiceAlertSystem *voice);

/**
 * @brief Check if currently speaking
 * @param voice Voice alert system instance
 * @return true if voice is currently playing
 */
bool voice_alerts_is_speaking(const VoiceAlertSystem *voice);

/**
 * @brief Mute voice alerts
 * @param voice Voice alert system instance
 * @param mute true to mute, false to unmute
 */
void voice_alerts_set_mute(VoiceAlertSystem *voice, bool mute);

/**
 * @brief Check if muted
 * @param voice Voice alert system instance
 * @return true if muted
 */
bool voice_alerts_is_muted(const VoiceAlertSystem *voice);

// ============================================================================
// Public API - Alert Management
// ============================================================================

/**
 * @brief Queue voice alert
 * @param voice Voice alert system instance
 * @param type Alert type
 * @param priority Alert priority
 * @param message Message text
 * @return true if successfully queued
 */
bool voice_alert_queue(VoiceAlertSystem *voice, AlertType type,
                      VoicePriority priority, const char *message);

/**
 * @brief Queue formatted voice alert
 * @param voice Voice alert system instance
 * @param type Alert type
 * @param priority Alert priority
 * @param format Printf-style format string
 * @param ... Variable arguments
 * @return true if successfully queued
 */
bool voice_alert_queue_formatted(VoiceAlertSystem *voice, AlertType type,
                                 VoicePriority priority, const char *format, ...);

/**
 * @brief Clear alert queue
 * @param voice Voice alert system instance
 */
void voice_alert_clear_queue(VoiceAlertSystem *voice);

/**
 * @brief Stop current message
 * @param voice Voice alert system instance
 */
void voice_alert_stop_current(VoiceAlertSystem *voice);

/**
 * @brief Get queue depth
 * @param voice Voice alert system instance
 * @return Number of alerts in queue
 */
size_t voice_alert_get_queue_depth(const VoiceAlertSystem *voice);

// ============================================================================
// Public API - Racing Callouts
// ============================================================================

/**
 * @brief Announce lap time
 * @param voice Voice alert system instance
 * @param lap_number Lap number
 * @param lap_time_ms Lap time in milliseconds
 * @return true if successfully queued
 */
bool voice_announce_lap_time(VoiceAlertSystem *voice, uint32_t lap_number,
                             uint64_t lap_time_ms);

/**
 * @brief Announce delta to best lap
 * @param voice Voice alert system instance
 * @param delta_ms Delta in milliseconds (negative = ahead)
 * @return true if successfully queued
 */
bool voice_announce_delta(VoiceAlertSystem *voice, int32_t delta_ms);

/**
 * @brief Announce best lap
 * @param voice Voice alert system instance
 * @param lap_time_ms Lap time
 * @return true if successfully queued
 */
bool voice_announce_best_lap(VoiceAlertSystem *voice, uint64_t lap_time_ms);

/**
 * @brief Announce shift point
 * @param voice Voice alert system instance
 * @return true if successfully queued
 */
bool voice_announce_shift_now(VoiceAlertSystem *voice);

/**
 * @brief Announce pit limiter status
 * @param voice Voice alert system instance
 * @param enabled true if pit limiter on
 * @return true if successfully queued
 */
bool voice_announce_pit_limiter(VoiceAlertSystem *voice, bool enabled);

/**
 * @brief Announce fuel status
 * @param voice Voice alert system instance
 * @param laps_remaining Estimated laps remaining
 * @return true if successfully queued
 */
bool voice_announce_fuel_status(VoiceAlertSystem *voice, uint32_t laps_remaining);

/**
 * @brief Announce temperature warning
 * @param voice Voice alert system instance
 * @param temp_c Temperature in Celsius
 * @param critical true if critical level
 * @return true if successfully queued
 */
bool voice_announce_temperature_warning(VoiceAlertSystem *voice,
                                       float temp_c, bool critical);

/**
 * @brief Announce oil pressure warning
 * @param voice Voice alert system instance
 * @param pressure_psi Pressure in PSI
 * @param critical true if critical level
 * @return true if successfully queued
 */
bool voice_announce_oil_pressure_warning(VoiceAlertSystem *voice,
                                        float pressure_psi, bool critical);

// ============================================================================
// Public API - Prerecorded Messages
// ============================================================================

/**
 * @brief Add prerecorded message
 * @param voice Voice alert system instance
 * @param type Alert type
 * @param audio_file_path Path to audio file (WAV/MP3)
 * @return true if successfully added
 */
bool voice_add_prerecorded(VoiceAlertSystem *voice, AlertType type,
                           const char *audio_file_path);

/**
 * @brief Play prerecorded message
 * @param voice Voice alert system instance
 * @param type Alert type
 * @return true if message found and queued
 */
bool voice_play_prerecorded(VoiceAlertSystem *voice, AlertType type);

// ============================================================================
// Public API - Bluetooth
// ============================================================================

/**
 * @brief Connect to Bluetooth audio device
 * @param voice Voice alert system instance
 * @param device_name Device name (NULL = use config)
 * @return true if connection successful
 */
bool voice_bluetooth_connect(VoiceAlertSystem *voice, const char *device_name);

/**
 * @brief Disconnect Bluetooth
 * @param voice Voice alert system instance
 */
void voice_bluetooth_disconnect(VoiceAlertSystem *voice);

/**
 * @brief Check Bluetooth connection
 * @param voice Voice alert system instance
 * @return true if Bluetooth connected
 */
bool voice_bluetooth_is_connected(const VoiceAlertSystem *voice);

/**
 * @brief Scan for Bluetooth audio devices
 * @param devices Output buffer for device names
 * @param max_devices Maximum devices to return
 * @return Number of devices found
 */
size_t voice_bluetooth_scan_devices(char devices[][32], size_t max_devices);

// ============================================================================
// Public API - Voice Settings
// ============================================================================

/**
 * @brief Set speech rate
 * @param voice Voice alert system instance
 * @param rate Speech rate (0.5-2.0)
 */
void voice_set_speech_rate(VoiceAlertSystem *voice, float rate);

/**
 * @brief Set voice pitch
 * @param voice Voice alert system instance
 * @param pitch Voice pitch (0.5-2.0)
 */
void voice_set_pitch(VoiceAlertSystem *voice, float pitch);

/**
 * @brief Set volume
 * @param voice Voice alert system instance
 * @param volume_percent Volume (0-100%)
 */
void voice_set_volume(VoiceAlertSystem *voice, uint8_t volume_percent);

/**
 * @brief Set language
 * @param voice Voice alert system instance
 * @param language Voice language
 */
void voice_set_language(VoiceAlertSystem *voice, VoiceLanguage language);

/**
 * @brief Set voice gender
 * @param voice Voice alert system instance
 * @param gender Voice gender
 */
void voice_set_gender(VoiceAlertSystem *voice, VoiceGender gender);

// ============================================================================
// Public API - Utilities
// ============================================================================

/**
 * @brief Format lap time as speech text
 * @param lap_time_ms Lap time in milliseconds
 * @param output Output buffer
 * @param output_size Output buffer size
 */
void voice_format_lap_time(uint64_t lap_time_ms, char *output, size_t output_size);

/**
 * @brief Format delta as speech text
 * @param delta_ms Delta in milliseconds (negative = ahead)
 * @param output Output buffer
 * @param output_size Output buffer size
 */
void voice_format_delta(int32_t delta_ms, char *output, size_t output_size);

/**
 * @brief Get language name
 * @param language Voice language
 * @return Language name string
 */
const char* voice_language_to_string(VoiceLanguage language);

/**
 * @brief Get engine name
 * @param engine Voice engine
 * @return Engine name string
 */
const char* voice_engine_to_string(VoiceEngine engine);

/**
 * @brief Get last error message
 * @param voice Voice alert system instance
 * @return Error string
 */
const char* voice_get_last_error(const VoiceAlertSystem *voice);

#ifdef __cplusplus
}
#endif
