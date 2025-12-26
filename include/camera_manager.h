#pragma once

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @file camera_manager.h
 * @brief Camera integration and telemetry overlay manager
 *
 * Features:
 * - GoPro WiFi API integration (Hero 9/10/11/12)
 * - Insta360 USB/WiFi control
 * - Generic RTSP camera support
 * - Auto-record on ignition/GPS trigger
 * - Telemetry overlay export (SRT, VBO, GPX)
 * - Multi-camera synchronization
 * - Live preview streaming
 */

// ============================================================================
// Constants
// ============================================================================

#define MAX_CAMERAS 4
#define CAMERA_NAME_MAX 32
#define CAMERA_IP_MAX 16
#define TELEMETRY_BUFFER_SIZE 1024

// ============================================================================
// Enumerations
// ============================================================================

typedef enum {
    CAMERA_TYPE_NONE,
    CAMERA_TYPE_GOPRO_WIFI,         // GoPro Hero 9+ WiFi
    CAMERA_TYPE_GOPRO_USB,          // GoPro via USB (media mode)
    CAMERA_TYPE_INSTA360_WIFI,      // Insta360 One X2/X3
    CAMERA_TYPE_INSTA360_USB,       // Insta360 via USB
    CAMERA_TYPE_RTSP,               // Generic RTSP camera
    CAMERA_TYPE_DJI_OSMO,           // DJI Osmo Action
    CAMERA_TYPE_GENERIC_HTTP        // Generic HTTP API camera
} CameraType;

typedef enum {
    CAMERA_STATE_DISCONNECTED,
    CAMERA_STATE_CONNECTED,
    CAMERA_STATE_IDLE,
    CAMERA_STATE_RECORDING,
    CAMERA_STATE_PAUSED,
    CAMERA_STATE_ERROR
} CameraState;

typedef enum {
    CAMERA_RESOLUTION_1080P,
    CAMERA_RESOLUTION_2_7K,
    CAMERA_RESOLUTION_4K,
    CAMERA_RESOLUTION_5_3K,
    CAMERA_RESOLUTION_8K
} CameraResolution;

typedef enum {
    CAMERA_FPS_24,
    CAMERA_FPS_30,
    CAMERA_FPS_60,
    CAMERA_FPS_120,
    CAMERA_FPS_240
} CameraFrameRate;

typedef enum {
    TRIGGER_MODE_MANUAL,
    TRIGGER_MODE_IGNITION,          // Start on ignition on
    TRIGGER_MODE_GPS_SPEED,         // Start at speed threshold
    TRIGGER_MODE_LAP_START,         // Start on lap detection
    TRIGGER_MODE_BUTTON             // External button trigger
} CameraTriggerMode;

typedef enum {
    OVERLAY_FORMAT_SRT,             // SubRip telemetry (for video editing)
    OVERLAY_FORMAT_VBO,             // Video BBOX format
    OVERLAY_FORMAT_GPX,             // GPS track
    OVERLAY_FORMAT_CSV,             // CSV telemetry
    OVERLAY_FORMAT_DASHWARE         // DashWare format
} OverlayFormat;

// ============================================================================
// Structures
// ============================================================================

typedef struct {
    CameraType type;
    char name[CAMERA_NAME_MAX];
    char ip_address[CAMERA_IP_MAX];
    uint16_t port;

    // Authentication
    char wifi_ssid[32];
    char wifi_password[32];
    char http_user[32];
    char http_password[32];

    // Settings
    CameraResolution resolution;
    CameraFrameRate frame_rate;
    bool enable_stabilization;
    bool enable_protune;            // GoPro advanced settings

    // State
    CameraState state;
    bool is_connected;
    uint64_t recording_start_time_ms;
    uint32_t recording_duration_s;
    uint32_t battery_percent;
    uint32_t storage_available_mb;
    float temperature_c;

    // Error
    char last_error[128];
} CameraConnection;

typedef struct {
    CameraTriggerMode trigger_mode;
    bool auto_start_on_ignition;
    bool auto_stop_on_ignition_off;
    float gps_speed_threshold_kmh;  // For GPS speed trigger
    uint32_t pre_record_duration_s; // Pre-record buffer (if supported)
    uint32_t post_record_duration_s;// Continue recording after trigger off
    bool sync_all_cameras;          // Start all cameras simultaneously
} CameraTriggerConfig;

typedef struct {
    bool enable_telemetry_overlay;
    OverlayFormat format;
    char output_path[128];

    // Data to include in overlay
    bool include_speed;
    bool include_rpm;
    bool include_gps;
    bool include_lap_times;
    bool include_g_forces;
    bool include_throttle_brake;

    // Overlay styling (for SRT)
    char font_name[32];
    uint8_t font_size;
    uint32_t font_color;            // RGB
    bool use_background;
} TelemetryOverlayConfig;

typedef struct {
    uint64_t timestamp_ms;          // Video timestamp
    double lat;
    double lon;
    float speed_kmh;
    float rpm;
    float throttle_percent;
    float brake_percent;
    float g_force_lat;
    float g_force_lon;
    int32_t lap_delta_ms;
    char custom_text[64];
} TelemetryFrame;

typedef struct {
    TelemetryFrame *frames;
    size_t frame_count;
    size_t capacity;
    uint64_t start_time_ms;
    uint64_t end_time_ms;
} TelemetryBuffer;

typedef struct {
    CameraConnection cameras[MAX_CAMERAS];
    size_t camera_count;

    CameraTriggerConfig trigger_config;
    TelemetryOverlayConfig overlay_config;

    TelemetryBuffer telemetry_buffer;

    // Multi-camera sync
    uint64_t sync_start_time_ms;
    bool is_sync_recording;

    // Statistics
    uint32_t total_recordings;
    uint64_t total_recording_time_s;
} CameraManager;

// ============================================================================
// Public API - Camera Management
// ============================================================================

/**
 * @brief Initialize camera manager
 * @param mgr Camera manager instance
 */
void camera_manager_init(CameraManager *mgr);

/**
 * @brief Add camera to manager
 * @param mgr Camera manager instance
 * @param type Camera type
 * @param name Camera name
 * @param ip IP address (for WiFi cameras)
 * @param port Port number
 * @return Camera index, or -1 if failed
 */
int camera_manager_add_camera(CameraManager *mgr, CameraType type,
                              const char *name, const char *ip, uint16_t port);

/**
 * @brief Remove camera
 * @param mgr Camera manager instance
 * @param camera_idx Camera index
 * @return true if successfully removed
 */
bool camera_manager_remove_camera(CameraManager *mgr, size_t camera_idx);

/**
 * @brief Connect to camera
 * @param mgr Camera manager instance
 * @param camera_idx Camera index
 * @return true if successfully connected
 */
bool camera_manager_connect(CameraManager *mgr, size_t camera_idx);

/**
 * @brief Disconnect from camera
 * @param mgr Camera manager instance
 * @param camera_idx Camera index
 */
void camera_manager_disconnect(CameraManager *mgr, size_t camera_idx);

/**
 * @brief Start recording on camera
 * @param mgr Camera manager instance
 * @param camera_idx Camera index
 * @return true if recording started
 */
bool camera_manager_start_recording(CameraManager *mgr, size_t camera_idx);

/**
 * @brief Stop recording on camera
 * @param mgr Camera manager instance
 * @param camera_idx Camera index
 * @return true if recording stopped
 */
bool camera_manager_stop_recording(CameraManager *mgr, size_t camera_idx);

/**
 * @brief Start recording on all cameras (synchronized)
 * @param mgr Camera manager instance
 * @return Number of cameras that started recording
 */
size_t camera_manager_start_all_cameras(CameraManager *mgr);

/**
 * @brief Stop recording on all cameras
 * @param mgr Camera manager instance
 * @return Number of cameras that stopped recording
 */
size_t camera_manager_stop_all_cameras(CameraManager *mgr);

/**
 * @brief Get camera state
 * @param mgr Camera manager instance
 * @param camera_idx Camera index
 * @return Current camera state
 */
CameraState camera_manager_get_state(const CameraManager *mgr, size_t camera_idx);

/**
 * @brief Check if any camera is recording
 * @param mgr Camera manager instance
 * @return true if at least one camera is recording
 */
bool camera_manager_is_any_recording(const CameraManager *mgr);

/**
 * @brief Update camera status (battery, storage, etc.)
 * @param mgr Camera manager instance
 * @param camera_idx Camera index
 * @return true if status successfully updated
 */
bool camera_manager_update_status(CameraManager *mgr, size_t camera_idx);

// ============================================================================
// Public API - GoPro Specific
// ============================================================================

/**
 * @brief GoPro: Set resolution and frame rate
 * @param mgr Camera manager instance
 * @param camera_idx Camera index
 * @param resolution Video resolution
 * @param fps Frame rate
 * @return true if successfully set
 */
bool camera_gopro_set_video_mode(CameraManager *mgr, size_t camera_idx,
                                 CameraResolution resolution, CameraFrameRate fps);

/**
 * @brief GoPro: Enable/disable Protune
 * @param mgr Camera manager instance
 * @param camera_idx Camera index
 * @param enable Enable Protune
 * @return true if successfully set
 */
bool camera_gopro_set_protune(CameraManager *mgr, size_t camera_idx, bool enable);

/**
 * @brief GoPro: Get media list
 * @param mgr Camera manager instance
 * @param camera_idx Camera index
 * @param media_list Output buffer for media filenames
 * @param max_items Maximum number of items
 * @return Number of media files found
 */
size_t camera_gopro_get_media_list(CameraManager *mgr, size_t camera_idx,
                                   char media_list[][64], size_t max_items);

/**
 * @brief GoPro: Download media file
 * @param mgr Camera manager instance
 * @param camera_idx Camera index
 * @param filename Remote filename
 * @param local_path Local save path
 * @return true if successfully downloaded
 */
bool camera_gopro_download_media(CameraManager *mgr, size_t camera_idx,
                                 const char *filename, const char *local_path);

// ============================================================================
// Public API - Trigger Configuration
// ============================================================================

/**
 * @brief Set trigger mode
 * @param mgr Camera manager instance
 * @param mode Trigger mode
 */
void camera_manager_set_trigger_mode(CameraManager *mgr, CameraTriggerMode mode);

/**
 * @brief Configure auto-start on ignition
 * @param mgr Camera manager instance
 * @param enable Enable auto-start
 * @param auto_stop Also auto-stop on ignition off
 */
void camera_manager_set_ignition_trigger(CameraManager *mgr, bool enable, bool auto_stop);

/**
 * @brief Configure GPS speed trigger
 * @param mgr Camera manager instance
 * @param speed_threshold_kmh Speed threshold to start recording
 */
void camera_manager_set_gps_speed_trigger(CameraManager *mgr, float speed_threshold_kmh);

/**
 * @brief Update trigger state (call from main loop)
 * @param mgr Camera manager instance
 * @param ignition_on Current ignition state
 * @param gps_speed_kmh Current GPS speed
 * @param lap_started Lap start event
 */
void camera_manager_update_triggers(CameraManager *mgr, bool ignition_on,
                                    float gps_speed_kmh, bool lap_started);

// ============================================================================
// Public API - Telemetry Overlay
// ============================================================================

/**
 * @brief Enable telemetry overlay export
 * @param mgr Camera manager instance
 * @param enable Enable overlay
 * @param format Overlay format
 * @param output_path Output file path
 */
void camera_manager_set_telemetry_overlay(CameraManager *mgr, bool enable,
                                          OverlayFormat format, const char *output_path);

/**
 * @brief Add telemetry frame to buffer
 * @param mgr Camera manager instance
 * @param frame Telemetry data for current frame
 */
void camera_manager_add_telemetry_frame(CameraManager *mgr, const TelemetryFrame *frame);

/**
 * @brief Export telemetry overlay to file
 * @param mgr Camera manager instance
 * @param video_start_time_ms Video start timestamp
 * @return true if successfully exported
 */
bool camera_manager_export_telemetry(CameraManager *mgr, uint64_t video_start_time_ms);

/**
 * @brief Clear telemetry buffer
 * @param mgr Camera manager instance
 */
void camera_manager_clear_telemetry(CameraManager *mgr);

/**
 * @brief Generate SRT subtitle file from telemetry
 * @param mgr Camera manager instance
 * @param srt_path Output SRT file path
 * @param video_start_ms Video start timestamp
 * @return true if successfully generated
 */
bool camera_manager_generate_srt(const CameraManager *mgr, const char *srt_path,
                                 uint64_t video_start_ms);

/**
 * @brief Generate GPX track from telemetry
 * @param mgr Camera manager instance
 * @param gpx_path Output GPX file path
 * @return true if successfully generated
 */
bool camera_manager_generate_gpx(const CameraManager *mgr, const char *gpx_path);

// ============================================================================
// Public API - Utilities
// ============================================================================

/**
 * @brief Get camera type name
 * @param type Camera type
 * @return Type name string
 */
const char* camera_type_to_string(CameraType type);

/**
 * @brief Get camera state name
 * @param state Camera state
 * @return State name string
 */
const char* camera_state_to_string(CameraState state);

/**
 * @brief Format recording duration as HH:MM:SS
 * @param duration_s Duration in seconds
 * @param output Output buffer
 * @param output_size Output buffer size
 */
void camera_format_duration(uint32_t duration_s, char *output, size_t output_size);

#ifdef __cplusplus
}
#endif
