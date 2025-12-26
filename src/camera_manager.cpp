#include "camera_manager.h"
#include <Arduino.h>
#include <string.h>

// ============================================================================
// Public API Implementation
// ============================================================================

void camera_manager_init(CameraManager *mgr) {
    if (!mgr) return;
    memset(mgr, 0, sizeof(CameraManager));
    mgr->camera_count = 0;
    mgr->is_sync_recording = false;

    // Default trigger configuration
    mgr->trigger_config.trigger_mode = TRIGGER_MODE_MANUAL;
    mgr->trigger_config.auto_start_on_ignition = false;
    mgr->trigger_config.auto_stop_on_ignition_off = true;
    mgr->trigger_config.gps_speed_threshold_kmh = 30.0f;
    mgr->trigger_config.pre_record_duration_s = 0;
    mgr->trigger_config.post_record_duration_s = 5;
    mgr->trigger_config.sync_all_cameras = true;

    // Default overlay configuration
    mgr->overlay_config.enable_telemetry_overlay = true;
    mgr->overlay_config.format = OVERLAY_FORMAT_SRT;
    mgr->overlay_config.include_speed = true;
    mgr->overlay_config.include_rpm = true;
    mgr->overlay_config.include_gps = true;
    mgr->overlay_config.include_lap_times = true;
    mgr->overlay_config.include_g_forces = false;
    mgr->overlay_config.include_throttle_brake = true;

    Serial.println("[CAMERA] Manager initialized");
}

int camera_manager_add_camera(CameraManager *mgr, CameraType type,
                              const char *name, const char *ip, uint16_t port) {
    if (!mgr || mgr->camera_count >= MAX_CAMERAS) return -1;

    CameraConnection *cam = &mgr->cameras[mgr->camera_count];
    cam->type = type;
    strncpy(cam->name, name, sizeof(cam->name) - 1);
    strncpy(cam->ip_address, ip, sizeof(cam->ip_address) - 1);
    cam->port = port;
    cam->state = CAMERA_STATE_DISCONNECTED;
    cam->is_connected = false;

    Serial.printf("[CAMERA] Added: %s (%s:%u)\n", name, ip, port);

    return mgr->camera_count++;
}

bool camera_manager_connect(CameraManager *mgr, size_t camera_idx) {
    if (!mgr || camera_idx >= mgr->camera_count) return false;

    CameraConnection *cam = &mgr->cameras[camera_idx];

    // TODO: Implement WiFi connection based on camera type
    // For now, simulate connection
    cam->is_connected = true;
    cam->state = CAMERA_STATE_IDLE;
    cam->battery_percent = 100;
    cam->storage_available_mb = 32000;

    Serial.printf("[CAMERA] Connected to %s\n", cam->name);
    return true;
}

void camera_manager_disconnect(CameraManager *mgr, size_t camera_idx) {
    if (!mgr || camera_idx >= mgr->camera_count) return;

    CameraConnection *cam = &mgr->cameras[camera_idx];
    cam->is_connected = false;
    cam->state = CAMERA_STATE_DISCONNECTED;

    Serial.printf("[CAMERA] Disconnected from %s\n", cam->name);
}

bool camera_manager_start_recording(CameraManager *mgr, size_t camera_idx) {
    if (!mgr || camera_idx >= mgr->camera_count) return false;

    CameraConnection *cam = &mgr->cameras[camera_idx];
    if (!cam->is_connected) return false;

    cam->state = CAMERA_STATE_RECORDING;
    cam->recording_start_time_ms = millis();

    Serial.printf("[CAMERA] Recording started on %s\n", cam->name);
    return true;
}

bool camera_manager_stop_recording(CameraManager *mgr, size_t camera_idx) {
    if (!mgr || camera_idx >= mgr->camera_count) return false;

    CameraConnection *cam = &mgr->cameras[camera_idx];
    if (cam->state != CAMERA_STATE_RECORDING) return false;

    cam->state = CAMERA_STATE_IDLE;
    cam->recording_duration_s = (millis() - cam->recording_start_time_ms) / 1000;

    Serial.printf("[CAMERA] Recording stopped on %s (duration: %u s)\n",
                  cam->name, cam->recording_duration_s);
    return true;
}

size_t camera_manager_start_all_cameras(CameraManager *mgr) {
    if (!mgr) return 0;

    size_t started = 0;
    mgr->sync_start_time_ms = millis();

    for (size_t i = 0; i < mgr->camera_count; i++) {
        if (camera_manager_start_recording(mgr, i)) {
            started++;
        }
    }

    mgr->is_sync_recording = (started > 0);
    Serial.printf("[CAMERA] Started %zu cameras\n", started);
    return started;
}

size_t camera_manager_stop_all_cameras(CameraManager *mgr) {
    if (!mgr) return 0;

    size_t stopped = 0;
    for (size_t i = 0; i < mgr->camera_count; i++) {
        if (camera_manager_stop_recording(mgr, i)) {
            stopped++;
        }
    }

    mgr->is_sync_recording = false;
    return stopped;
}

CameraState camera_manager_get_state(const CameraManager *mgr, size_t camera_idx) {
    if (!mgr || camera_idx >= mgr->camera_count) return CAMERA_STATE_ERROR;
    return mgr->cameras[camera_idx].state;
}

bool camera_manager_is_any_recording(const CameraManager *mgr) {
    if (!mgr) return false;

    for (size_t i = 0; i < mgr->camera_count; i++) {
        if (mgr->cameras[i].state == CAMERA_STATE_RECORDING) {
            return true;
        }
    }
    return false;
}

void camera_manager_set_trigger_mode(CameraManager *mgr, CameraTriggerMode mode) {
    if (mgr) {
        mgr->trigger_config.trigger_mode = mode;
    }
}

void camera_manager_set_ignition_trigger(CameraManager *mgr, bool enable, bool auto_stop) {
    if (mgr) {
        mgr->trigger_config.auto_start_on_ignition = enable;
        mgr->trigger_config.auto_stop_on_ignition_off = auto_stop;
    }
}

void camera_manager_update_triggers(CameraManager *mgr, bool ignition_on,
                                    float gps_speed_kmh, bool lap_started) {
    if (!mgr) return;

    static bool prev_ignition = false;

    // Ignition trigger
    if (mgr->trigger_config.auto_start_on_ignition) {
        if (ignition_on && !prev_ignition) {
            camera_manager_start_all_cameras(mgr);
        } else if (!ignition_on && prev_ignition && mgr->trigger_config.auto_stop_on_ignition_off) {
            camera_manager_stop_all_cameras(mgr);
        }
    }

    // GPS speed trigger
    if (mgr->trigger_config.trigger_mode == TRIGGER_MODE_GPS_SPEED) {
        static bool recording = false;
        if (gps_speed_kmh >= mgr->trigger_config.gps_speed_threshold_kmh && !recording) {
            camera_manager_start_all_cameras(mgr);
            recording = true;
        } else if (gps_speed_kmh < mgr->trigger_config.gps_speed_threshold_kmh && recording) {
            camera_manager_stop_all_cameras(mgr);
            recording = false;
        }
    }

    // Lap start trigger
    if (mgr->trigger_config.trigger_mode == TRIGGER_MODE_LAP_START && lap_started) {
        camera_manager_start_all_cameras(mgr);
    }

    prev_ignition = ignition_on;
}

void camera_manager_add_telemetry_frame(CameraManager *mgr, const TelemetryFrame *frame) {
    if (!mgr || !frame) return;

    if (mgr->telemetry_buffer.frame_count < mgr->telemetry_buffer.capacity) {
        memcpy(&mgr->telemetry_buffer.frames[mgr->telemetry_buffer.frame_count],
               frame, sizeof(TelemetryFrame));
        mgr->telemetry_buffer.frame_count++;
    }
}

const char* camera_type_to_string(CameraType type) {
    switch (type) {
        case CAMERA_TYPE_GOPRO_WIFI: return "GoPro WiFi";
        case CAMERA_TYPE_INSTA360_WIFI: return "Insta360 WiFi";
        case CAMERA_TYPE_RTSP: return "RTSP";
        default: return "Unknown";
    }
}

const char* camera_state_to_string(CameraState state) {
    switch (state) {
        case CAMERA_STATE_DISCONNECTED: return "Disconnected";
        case CAMERA_STATE_CONNECTED: return "Connected";
        case CAMERA_STATE_IDLE: return "Idle";
        case CAMERA_STATE_RECORDING: return "Recording";
        case CAMERA_STATE_PAUSED: return "Paused";
        case CAMERA_STATE_ERROR: return "Error";
        default: return "Unknown";
    }
}
