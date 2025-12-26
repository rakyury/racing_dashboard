#pragma once

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @file cloud_telemetry.h
 * @brief Cloud Telemetry Integration (AWS IoT / Azure IoT / Google Cloud)
 *
 * Features:
 * - Real-time telemetry streaming
 * - Session upload to cloud storage (S3/Azure Blob/GCS)
 * - Remote monitoring dashboard
 * - Team data sharing
 * - Historical data analysis
 * - Alert notifications (SMS/email/push)
 * - Cloud-based lap comparison
 */

// ============================================================================
// Constants
// ============================================================================

#define CLOUD_MAX_ENDPOINT_LEN 256
#define CLOUD_MAX_DEVICE_ID_LEN 64
#define CLOUD_MAX_CERT_SIZE 2048
#define CLOUD_BATCH_SIZE 50         // Telemetry samples per upload

// ============================================================================
// Enumerations
// ============================================================================

typedef enum {
    CLOUD_PROVIDER_AWS_IOT,
    CLOUD_PROVIDER_AZURE_IOT,
    CLOUD_PROVIDER_GOOGLE_IOT,
    CLOUD_PROVIDER_CUSTOM_MQTT
} CloudProvider;

typedef enum {
    CLOUD_STATE_DISCONNECTED,
    CLOUD_STATE_CONNECTING,
    CLOUD_STATE_CONNECTED,
    CLOUD_STATE_AUTHENTICATED,
    CLOUD_STATE_ERROR
} CloudState;

typedef enum {
    CLOUD_MSG_TELEMETRY,            // Real-time telemetry
    CLOUD_MSG_LAP_COMPLETE,         // Lap summary
    CLOUD_MSG_SESSION_START,
    CLOUD_MSG_SESSION_END,
    CLOUD_MSG_ALERT,                // Warning/critical alert
    CLOUD_MSG_COMMAND,              // Remote command
    CLOUD_MSG_HEARTBEAT
} CloudMessageType;

typedef enum {
    UPLOAD_PRIORITY_LOW,
    UPLOAD_PRIORITY_NORMAL,
    UPLOAD_PRIORITY_HIGH,
    UPLOAD_PRIORITY_CRITICAL
} UploadPriority;

// ============================================================================
// Structures
// ============================================================================

typedef struct {
    CloudProvider provider;
    char endpoint[CLOUD_MAX_ENDPOINT_LEN];
    uint16_t port;

    // Device identity
    char device_id[CLOUD_MAX_DEVICE_ID_LEN];
    char device_name[64];
    char team_id[32];

    // Authentication (X.509 certificates)
    char ca_cert_path[128];
    char device_cert_path[128];
    char private_key_path[128];

    // AWS IoT specific
    char aws_thing_name[64];
    char aws_region[32];

    // Azure IoT specific
    char azure_connection_string[256];
    char azure_device_key[64];

    // Topics/channels
    char telemetry_topic[128];
    char command_topic[128];

    // QoS and reliability
    uint8_t qos_level;              // 0, 1, or 2
    bool retain_messages;
    uint16_t keepalive_interval_s;

    // Upload behavior
    bool auto_upload_sessions;
    bool real_time_streaming;
    uint32_t batch_interval_ms;     // Batch telemetry every N ms
    uint32_t retry_interval_ms;
} CloudConfig;

typedef struct {
    uint64_t timestamp_ms;
    float rpm;
    float speed_kmh;
    float throttle_percent;
    float brake_percent;
    float oil_pressure_psi;
    float coolant_temp_c;
    double lat;
    double lon;
    uint8_t gear;
    uint32_t lap_number;
} TelemetrySnapshot;

typedef struct {
    char session_id[64];
    uint64_t start_time_utc;
    uint64_t end_time_utc;
    char track_name[64];
    char driver_name[32];
    char vehicle_id[32];
    uint32_t lap_count;
    uint32_t best_lap_ms;
    float total_distance_km;
    float avg_speed_kmh;
    float max_speed_kmh;
} SessionMetadata;

typedef struct {
    CloudMessageType type;
    uint64_t timestamp_ms;
    uint8_t payload[512];
    size_t payload_size;
    UploadPriority priority;
    bool requires_ack;
} CloudMessage;

typedef struct {
    CloudMessage messages[256];
    size_t head;
    size_t tail;
    size_t count;
    size_t dropped_count;           // Messages dropped due to full queue
} CloudMessageQueue;

typedef struct {
    CloudConfig config;
    CloudState state;

    // MQTT/connection
    void *mqtt_client;              // Platform-specific MQTT client
    bool is_connected;
    uint64_t last_connect_attempt_ms;
    uint32_t connection_failures;

    // Message queue
    CloudMessageQueue queue;

    // Batching
    TelemetrySnapshot batch[CLOUD_BATCH_SIZE];
    size_t batch_count;
    uint64_t last_batch_send_ms;

    // Statistics
    uint64_t total_messages_sent;
    uint64_t total_bytes_sent;
    uint64_t total_messages_failed;
    float upload_throughput_kbps;
    uint32_t avg_latency_ms;

    // Session upload
    char current_session_id[64];
    bool session_active;
    char upload_url[CLOUD_MAX_ENDPOINT_LEN];

    // Error state
    char last_error[128];
} CloudTelemetry;

// Remote command callback
typedef void (*CloudCommandCallback)(const char *command, const char *params, void *user_data);

// ============================================================================
// Public API - Core Functions
// ============================================================================

/**
 * @brief Initialize cloud telemetry
 * @param cloud Cloud telemetry instance
 * @param config Configuration parameters
 * @return true if successfully initialized
 */
bool cloud_telemetry_init(CloudTelemetry *cloud, const CloudConfig *config);

/**
 * @brief Connect to cloud service
 * @param cloud Cloud telemetry instance
 * @return true if connection successful
 */
bool cloud_telemetry_connect(CloudTelemetry *cloud);

/**
 * @brief Disconnect from cloud service
 * @param cloud Cloud telemetry instance
 */
void cloud_telemetry_disconnect(CloudTelemetry *cloud);

/**
 * @brief Update cloud telemetry (call from main loop)
 * @param cloud Cloud telemetry instance
 */
void cloud_telemetry_update(CloudTelemetry *cloud);

/**
 * @brief Check if connected to cloud
 * @param cloud Cloud telemetry instance
 * @return true if connected
 */
bool cloud_telemetry_is_connected(const CloudTelemetry *cloud);

/**
 * @brief Get connection state
 * @param cloud Cloud telemetry instance
 * @return Current cloud state
 */
CloudState cloud_telemetry_get_state(const CloudTelemetry *cloud);

// ============================================================================
// Public API - Telemetry Streaming
// ============================================================================

/**
 * @brief Send telemetry snapshot
 * @param cloud Cloud telemetry instance
 * @param snapshot Telemetry data
 * @return true if queued successfully
 */
bool cloud_send_telemetry(CloudTelemetry *cloud, const TelemetrySnapshot *snapshot);

/**
 * @brief Send batched telemetry
 * @param cloud Cloud telemetry instance
 * @param snapshots Array of telemetry snapshots
 * @param count Number of snapshots
 * @return Number of snapshots successfully queued
 */
size_t cloud_send_telemetry_batch(CloudTelemetry *cloud,
                                  const TelemetrySnapshot *snapshots, size_t count);

/**
 * @brief Send lap completion event
 * @param cloud Cloud telemetry instance
 * @param lap_number Lap number
 * @param lap_time_ms Lap time
 * @param delta_to_best_ms Delta to best lap
 * @return true if sent successfully
 */
bool cloud_send_lap_complete(CloudTelemetry *cloud, uint32_t lap_number,
                             uint64_t lap_time_ms, int32_t delta_to_best_ms);

/**
 * @brief Send alert/warning
 * @param cloud Cloud telemetry instance
 * @param severity Severity level (0=info, 1=warning, 2=critical)
 * @param message Alert message
 * @return true if sent successfully
 */
bool cloud_send_alert(CloudTelemetry *cloud, uint8_t severity, const char *message);

/**
 * @brief Send heartbeat (keep-alive)
 * @param cloud Cloud telemetry instance
 * @return true if sent successfully
 */
bool cloud_send_heartbeat(CloudTelemetry *cloud);

// ============================================================================
// Public API - Session Management
// ============================================================================

/**
 * @brief Start new session
 * @param cloud Cloud telemetry instance
 * @param metadata Session metadata
 * @return Session ID (empty on failure)
 */
const char* cloud_session_start(CloudTelemetry *cloud, const SessionMetadata *metadata);

/**
 * @brief End current session
 * @param cloud Cloud telemetry instance
 * @param metadata Final session metadata
 * @return true if session ended successfully
 */
bool cloud_session_end(CloudTelemetry *cloud, const SessionMetadata *metadata);

/**
 * @brief Upload session log file
 * @param cloud Cloud telemetry instance
 * @param log_file_path Path to log file
 * @return true if upload initiated
 */
bool cloud_session_upload_log(CloudTelemetry *cloud, const char *log_file_path);

/**
 * @brief Upload session video
 * @param cloud Cloud telemetry instance
 * @param video_file_path Path to video file
 * @return true if upload initiated
 */
bool cloud_session_upload_video(CloudTelemetry *cloud, const char *video_file_path);

/**
 * @brief Get session upload URL
 * @param cloud Cloud telemetry instance
 * @return Upload URL (empty if not available)
 */
const char* cloud_session_get_upload_url(const CloudTelemetry *cloud);

// ============================================================================
// Public API - Remote Commands
// ============================================================================

/**
 * @brief Register command callback
 * @param cloud Cloud telemetry instance
 * @param callback Command callback function
 * @param user_data User data for callback
 */
void cloud_register_command_callback(CloudTelemetry *cloud,
                                     CloudCommandCallback callback, void *user_data);

/**
 * @brief Subscribe to command topic
 * @param cloud Cloud telemetry instance
 * @return true if subscribed successfully
 */
bool cloud_subscribe_commands(CloudTelemetry *cloud);

// ============================================================================
// Public API - Statistics
// ============================================================================

/**
 * @brief Get upload statistics
 * @param cloud Cloud telemetry instance
 * @param messages_sent Output total messages sent
 * @param bytes_sent Output total bytes sent
 * @param throughput_kbps Output current throughput
 * @param latency_ms Output average latency
 */
void cloud_get_statistics(const CloudTelemetry *cloud,
                         uint64_t *messages_sent, uint64_t *bytes_sent,
                         float *throughput_kbps, uint32_t *latency_ms);

/**
 * @brief Get queue depth
 * @param cloud Cloud telemetry instance
 * @return Number of messages in queue
 */
size_t cloud_get_queue_depth(const CloudTelemetry *cloud);

/**
 * @brief Get dropped message count
 * @param cloud Cloud telemetry instance
 * @return Number of messages dropped
 */
size_t cloud_get_dropped_count(const CloudTelemetry *cloud);

/**
 * @brief Reset statistics
 * @param cloud Cloud telemetry instance
 */
void cloud_reset_statistics(CloudTelemetry *cloud);

// ============================================================================
// Public API - Utilities
// ============================================================================

/**
 * @brief Get provider name
 * @param provider Cloud provider
 * @return Provider name string
 */
const char* cloud_provider_to_string(CloudProvider provider);

/**
 * @brief Get state name
 * @param state Cloud state
 * @return State name string
 */
const char* cloud_state_to_string(CloudState state);

/**
 * @brief Generate device ID from MAC address
 * @param mac_address MAC address (6 bytes)
 * @param device_id Output device ID buffer
 * @param device_id_size Buffer size
 */
void cloud_generate_device_id(const uint8_t *mac_address,
                              char *device_id, size_t device_id_size);

/**
 * @brief Get last error message
 * @param cloud Cloud telemetry instance
 * @return Error string
 */
const char* cloud_get_last_error(const CloudTelemetry *cloud);

#ifdef __cplusplus
}
#endif
