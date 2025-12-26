/**
 * @file main_arduino.cpp
 * @brief Racing Dashboard - Arduino/PlatformIO Main Entry Point
 *
 * Target: STM32H7B3 + RVT70HSSNWN00 Display (1024x600)
 * Platform: PlatformIO + Arduino Framework
 * Graphics: TouchGFX + LVGL
 */

#include <Arduino.h>
#include "config.h"
#include "display_config.h"
#include "theme_manager.h"
#include "signal_bus.h"

// Modules
#include "advanced_logger.h"
#include "lap_timer.h"
#include "camera_manager.h"
#include "voice_alerts.h"

// Platform-specific includes
#include <TinyGPSPlus.h>
#include <SD.h>

// ============================================================================
// Global Objects
// ============================================================================

SignalBus signal_bus;
ThemeManager theme_manager;
const DisplayConfig *display_config;

// Modules
AdvancedLogger logger;
LapTimer lap_timer;
CameraManager camera_mgr;
VoiceAlertSystem voice;

// GPS
TinyGPSPlus gps;
HardwareSerial gpsSerial(2);  // UART2 for GPS

// Timing
unsigned long last_frame_time_ms = 0;
unsigned long last_can_poll_time_ms = 0;
uint32_t frame_count = 0;
float fps = 0.0f;

// Demo data
float demo_rpm = 2000.0f;
float demo_speed = 80.0f;
bool demo_direction = true;

// ============================================================================
// Hardware Initialization
// ============================================================================

void setup_display() {
    Serial.println(F("[INIT] Configuring display..."));

    // Initialize display configuration for RVT70HSSNWN00
    display_config = display_config_init(DISPLAY_PROFILE_1024x600_STANDARD);

    Serial.printf("[INIT] Display: %dx%d @ %d DPI\n",
                  display_config->width,
                  display_config->height,
                  display_config->dpi);

#ifdef USE_TOUCHGFX
    // TouchGFX initialization
    Serial.println(F("[INIT] TouchGFX initialized"));
#endif

    // Configure backlight PWM
    pinMode(BACKLIGHT_PWM_PIN, OUTPUT);
    analogWrite(BACKLIGHT_PWM_PIN, 200);  // ~80% brightness

    Serial.println(F("[INIT] Display ready"));
}

void setup_can_bus() {
    Serial.println(F("[INIT] Configuring CAN bus..."));
    // TODO: Initialize CAN based on platform
    Serial.println(F("[INIT] CAN bus ready"));
}

void setup_gps() {
    Serial.println(F("[INIT] Configuring GPS..."));
    gpsSerial.begin(GPS_BAUDRATE);
    Serial.printf("[INIT] GPS UART @ %d baud\n", GPS_BAUDRATE);
}

void setup_sd_card() {
    Serial.println(F("[INIT] Initializing SD card..."));
#ifdef STM32H7xx
    if (SD.begin()) {
        uint64_t card_size = SD.cardSize() / (1024 * 1024);
        Serial.printf("[INIT] SD card mounted: %llu MB\n", card_size);
    } else {
        Serial.println(F("[ERROR] SD card mount failed!"));
    }
#endif
}

void setup_signal_bus() {
    Serial.println(F("[INIT] Initializing signal bus..."));
    signal_bus_init(&signal_bus);
    Serial.println(F("[INIT] Signal bus initialized"));
}

void setup_theme() {
    Serial.println(F("[INIT] Initializing theme manager..."));
    theme_manager_init(&theme_manager);
    theme_manager_set_preset(&theme_manager, THEME_MOTEC_DARK);

    // Enable auto night mode (8 PM to 6 AM)
    theme_manager_set_auto_night_mode(&theme_manager, true, 20, 6,
                                      THEME_MOTEC_DARK, THEME_NIGHT_MODE);

    const Theme *active_theme = theme_manager_get_active(&theme_manager);
    Serial.printf("[INIT] Active theme: %s\n", active_theme->name);
}

#ifdef ENABLE_LAP_TIMER
void setup_lap_timer() {
    Serial.println(F("[INIT] Initializing lap timer..."));
    lap_timer_init(&lap_timer);
    lap_timer.auto_detection_enabled = true;
    lap_timer.auto_sector_detection = true;
    Serial.println(F("[INIT] Lap timer ready"));
}
#endif

#ifdef ENABLE_CAMERA_MANAGER
void setup_camera_manager() {
    Serial.println(F("[INIT] Initializing camera manager..."));

    camera_manager_init(&camera_mgr);

    // Configure trigger mode
    camera_manager_set_trigger_mode(&camera_mgr, TRIGGER_MODE_MANUAL);
    camera_manager_set_ignition_trigger(&camera_mgr, true, true);

    // Add GoPro camera
    camera_manager_add_camera(&camera_mgr, CAMERA_TYPE_GOPRO_WIFI,
                              "GoPro Hero 11", "10.5.5.9", 8080);

    Serial.println(F("[INIT] Camera manager ready"));
}
#endif

#ifdef ENABLE_VOICE_ALERTS
void setup_voice_alerts() {
    Serial.println(F("[INIT] Initializing voice alerts..."));

    VoiceConfig voice_config = {
        .engine = VOICE_ENGINE_TTS_ESPEAK,
        .language = VOICE_LANG_ENGLISH_US,
        .gender = VOICE_GENDER_MALE,
        .output = VOICE_OUTPUT_BLUETOOTH,
        .speech_rate = 1.0f,
        .pitch = 1.0f,
        .volume_percent = 80,
        .use_cloud_tts = false,
        .sample_rate_hz = 22050,
        .bit_depth = 16,
        .auto_connect_bluetooth = true,
        .interrupt_on_critical = true,
        .repeat_critical_alerts = false,
        .min_repeat_interval_ms = 5000,
        .mute_during_recording = false
    };

    voice_alerts_init(&voice, &voice_config);

    Serial.println(F("[INIT] Voice alerts ready"));
}
#endif

#ifdef ENABLE_ADVANCED_LOGGING
void setup_logger() {
    Serial.println(F("[INIT] Configuring advanced logger..."));

    LoggerConfig log_config = {
        .format = LOG_FORMAT_CSV,
        .compression = LOG_COMPRESSION_ZLIB,
        .compression_level = 6,
        .buffer_size_kb = 128,
        .auto_flush_interval_ms = 5000,
        .use_sd_card = true,
        .use_internal_flash = false,
        .max_file_size_mb = 500,
        .auto_rotate = true,
        .sample_rate_hz = 100,
        .enable_pre_trigger = true,
        .pre_trigger_seconds = 5
    };

    strcpy(log_config.base_path, "/sd/logs");

    if (advanced_logger_init(&logger, &log_config)) {
        // Add logging channels
        advanced_logger_add_channel(&logger, "rpm", 0.0f, 10000.0f, false);
        advanced_logger_add_channel(&logger, "speed", 0.0f, 350.0f, false);
        advanced_logger_add_channel(&logger, "throttle", 0.0f, 100.0f, false);
        advanced_logger_add_channel(&logger, "brake", 0.0f, 100.0f, false);
        advanced_logger_add_channel(&logger, "gear", 0.0f, 8.0f, false);
        advanced_logger_add_channel(&logger, "oil_pressure", 0.0f, 150.0f, false);
        advanced_logger_add_channel(&logger, "coolant_temp", 0.0f, 150.0f, false);
        advanced_logger_add_channel(&logger, "gps_lat", -90.0f, 90.0f, false);
        advanced_logger_add_channel(&logger, "gps_lon", -180.0f, 180.0f, false);

        // Add trigger condition for high RPM
        advanced_logger_add_trigger(&logger, "rpm", TRIGGER_OP_GREATER, 8000.0f);

        Serial.println(F("[INIT] Logger configured with 9 channels"));
    } else {
        Serial.println(F("[ERROR] Logger initialization failed!"));
    }

    Serial.println(F("[INIT] Logger ready"));
}
#endif

// ============================================================================
// Main Setup
// ============================================================================

void setup() {
    Serial.begin(DEBUG_SERIAL_BAUDRATE);
    delay(2000);

    Serial.println(F("\n=========================================="));
    Serial.println(F("  Racing Dashboard v2.0"));
    Serial.printf("  Build: %s %s\n", FIRMWARE_BUILD_DATE, FIRMWARE_BUILD_TIME);
    Serial.println(F("  Target: STM32H7B3 + RVT70HSSNWN00"));
    Serial.println(F("==========================================\n"));

    setup_display();
    setup_can_bus();
    setup_gps();
    setup_sd_card();
    setup_signal_bus();
    setup_theme();

#ifdef ENABLE_LAP_TIMER
    setup_lap_timer();
#endif

#ifdef ENABLE_CAMERA_MANAGER
    setup_camera_manager();
#endif

#ifdef ENABLE_VOICE_ALERTS
    setup_voice_alerts();
#endif

#ifdef ENABLE_ADVANCED_LOGGING
    setup_logger();
#endif

    Serial.println(F("\n[READY] System initialized\n"));
    last_frame_time_ms = millis();
}

// ============================================================================
// Main Loop
// ============================================================================

void loop() {
    unsigned long loop_start_ms = millis();

    // Process GPS
    while (gpsSerial.available() > 0) {
        gps.encode(gpsSerial.read());
    }

    // Update GPS data for lap timer
#ifdef ENABLE_LAP_TIMER
    if (gps.location.isValid() && gps.speed.isValid()) {
        lap_timer_update(&lap_timer,
                         gps.location.lat(), gps.location.lng(),
                         gps.speed.kmph(), loop_start_ms);

        // Check for lap completion
        if (lap_timer.current_lap > 0 && lap_timer.laps[lap_timer.current_lap - 1].time_ms > 0) {
            uint32_t lap_num = lap_timer.current_lap - 1;
            uint64_t lap_time = lap_timer.laps[lap_num].time_ms;

#ifdef ENABLE_VOICE_ALERTS
            // Announce lap time
            voice_announce_lap_time(&voice, lap_num + 1, lap_time);

            // Announce if best lap
            if (lap_num > 0 && lap_time == lap_timer.best_lap_time_ms) {
                voice_announce_best_lap(&voice, lap_time);
            }
#endif
        }
    }
#endif

    // Update demo data (simulate CAN data)
    if (demo_direction) {
        demo_rpm += 50.0f;
        demo_speed += 2.0f;
        if (demo_rpm >= 8500.0f) demo_direction = false;
    } else {
        demo_rpm -= 50.0f;
        demo_speed -= 2.0f;
        if (demo_rpm <= 1000.0f) demo_direction = true;
    }

    // Publish signals to signal bus
    signal_bus_publish(&signal_bus, "rpm", demo_rpm, loop_start_ms, false);
    signal_bus_publish(&signal_bus, "speed", demo_speed, loop_start_ms, false);
    signal_bus_publish(&signal_bus, "throttle", demo_rpm / 85.0f, loop_start_ms, false);
    signal_bus_publish(&signal_bus, "gear", (uint8_t)(demo_speed / 40.0f) + 1, loop_start_ms, false);

    // Log data
#ifdef ENABLE_ADVANCED_LOGGING
    if (logger.is_logging) {
        advanced_logger_log_sample(&logger, "rpm", demo_rpm, loop_start_ms, false);
        advanced_logger_log_sample(&logger, "speed", demo_speed, loop_start_ms, false);
        advanced_logger_log_sample(&logger, "throttle", demo_rpm / 85.0f, loop_start_ms, false);

        if (gps.location.isValid()) {
            advanced_logger_log_sample(&logger, "gps_lat", gps.location.lat(), loop_start_ms, false);
            advanced_logger_log_sample(&logger, "gps_lon", gps.location.lng(), loop_start_ms, false);
        }

        // Auto-flush periodically
        static unsigned long last_flush_ms = 0;
        if (loop_start_ms - last_flush_ms >= logger.config.auto_flush_interval_ms) {
            advanced_logger_flush(&logger);
            last_flush_ms = loop_start_ms;
        }
    }
#endif

    // Update voice alerts
#ifdef ENABLE_VOICE_ALERTS
    voice_alerts_update(&voice);
#endif

    // Update camera triggers
#ifdef ENABLE_CAMERA_MANAGER
    static bool last_ignition = false;
    bool ignition_on = true;  // TODO: Get from CAN
    bool lap_started = false;

#ifdef ENABLE_LAP_TIMER
    lap_started = (lap_timer.current_lap > 0);
#endif

    camera_manager_update_triggers(&camera_mgr, ignition_on,
                                   gps.speed.isValid() ? gps.speed.kmph() : 0.0f,
                                   lap_started);

    // Start recording on ignition
    if (ignition_on && !last_ignition) {
        camera_manager_start_all_cameras(&camera_mgr);
        Serial.println(F("[CAMERA] Started recording on ignition"));
    }
    last_ignition = ignition_on;
#endif

    // Update theme (check for auto night mode)
    static unsigned long last_theme_update_ms = 0;
    if (loop_start_ms - last_theme_update_ms >= 60000) {  // Check every minute
        theme_manager_update(&theme_manager);
        last_theme_update_ms = loop_start_ms;
    }

    // Render frame (60 Hz)
    static unsigned long last_render_ms = 0;
    if (loop_start_ms - last_render_ms >= (1000 / DISPLAY_REFRESH_RATE)) {
#ifdef USE_TOUCHGFX
        // TouchGFX rendering
        // touchgfx_render();
#endif
        last_render_ms = loop_start_ms;
        frame_count++;
    }

    // Calculate FPS
    static unsigned long last_fps_calc_ms = 0;
    if (loop_start_ms - last_fps_calc_ms >= 1000) {
        fps = frame_count / ((loop_start_ms - last_fps_calc_ms) / 1000.0f);
        frame_count = 0;
        last_fps_calc_ms = loop_start_ms;

        // Print statistics
        Serial.printf("[STATS] FPS: %.1f | RPM: %.0f | Speed: %.1f km/h\n",
                      fps, demo_rpm, demo_speed);

#ifdef ENABLE_ADVANCED_LOGGING
        if (logger.is_logging) {
            LoggerStats stats = advanced_logger_get_stats(&logger);
            Serial.printf("[LOGGER] Samples: %lu | Rate: %.1f Hz | Buffer: %u%%\n",
                          stats.total_samples_logged,
                          stats.current_sample_rate_hz,
                          stats.buffer_usage_percent);
        }
#endif

#ifdef ENABLE_LAP_TIMER
        if (lap_timer.current_lap > 0) {
            Serial.printf("[LAP] Lap %u | Best: %.3f s\n",
                          lap_timer.current_lap,
                          lap_timer.best_lap_time_ms / 1000.0f);
        }
#endif
    }

    delay(1);
}
