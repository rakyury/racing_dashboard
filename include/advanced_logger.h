#pragma once

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include "signal_bus.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @file advanced_logger.h
 * @brief Advanced data logger with compression and selective recording
 *
 * Features:
 * - Multiple format support (CSV, Binary, Compressed)
 * - Selective channel logging with whitelist/blacklist
 * - Trigger-based recording (start on condition)
 * - Circular buffer mode for continuous recording
 * - Ring buffer for pre-trigger data capture
 * - Session management with automatic file rotation
 * - GPS time synchronization
 */

// ============================================================================
// Constants
// ============================================================================

#define MAX_LOG_CHANNELS 128
#define MAX_LOG_FILENAME 64
#define DEFAULT_BUFFER_SIZE_KB 128
#define COMPRESSION_LEVEL_DEFAULT 6

// ============================================================================
// Enumerations
// ============================================================================

typedef enum {
    LOG_FORMAT_CSV,              // Human-readable CSV
    LOG_FORMAT_BINARY,           // Fast binary format
    LOG_FORMAT_COMPRESSED_ZLIB,  // Compressed binary (zlib)
    LOG_FORMAT_PARQUET           // Columnar format for analytics
} LogFormat;

typedef enum {
    LOG_STATE_STOPPED,
    LOG_STATE_ARMED,             // Waiting for trigger
    LOG_STATE_PRE_TRIGGER,       // Capturing pre-trigger buffer
    LOG_STATE_RECORDING,
    LOG_STATE_PAUSED,
    LOG_STATE_ERROR
} LogState;

typedef enum {
    TRIGGER_MODE_NONE,
    TRIGGER_MODE_MANUAL,         // User button
    TRIGGER_MODE_THRESHOLD,      // Channel crosses threshold
    TRIGGER_MODE_DIGITAL_INPUT,  // Digital signal (e.g., ignition)
    TRIGGER_MODE_GPS_SPEED,      // Speed threshold
    TRIGGER_MODE_GPS_GEOFENCE    // Enter/exit area
} TriggerMode;

typedef enum {
    ROTATION_MODE_NONE,
    ROTATION_MODE_SIZE,          // Rotate at file size
    ROTATION_MODE_TIME,          // Rotate at time interval
    ROTATION_MODE_LAP            // Rotate on lap completion
} RotationMode;

// ============================================================================
// Structures
// ============================================================================

typedef struct {
    char channel_name[32];
    bool enabled;
    float sample_rate_hz;        // Per-channel sample rate
    float last_value;
    uint64_t last_sample_time_ms;
} LogChannel;

typedef struct {
    TriggerMode mode;
    char channel_name[32];       // For threshold triggers
    float threshold_value;
    bool threshold_rising;       // true = rising edge, false = falling
    bool is_armed;
    bool is_triggered;

    // Pre-trigger buffer settings
    uint32_t pre_trigger_duration_ms;
    uint32_t pre_trigger_samples;
} TriggerConfig;

typedef struct {
    RotationMode mode;
    uint32_t max_file_size_mb;
    uint32_t max_duration_seconds;
    uint32_t file_counter;
    char base_filename[48];
} RotationConfig;

typedef struct {
    // File settings
    LogFormat format;
    char output_path[MAX_LOG_FILENAME];
    bool append_mode;

    // Buffer settings
    size_t buffer_size_kb;
    bool circular_buffer_mode;

    // Compression
    uint8_t compression_level;   // 1-9 (zlib)

    // Sample rate
    float default_sample_rate_hz;

    // Channel selection
    LogChannel channels[MAX_LOG_CHANNELS];
    size_t channel_count;
    bool use_whitelist;          // true = only log whitelisted channels

    // Trigger configuration
    TriggerConfig trigger;

    // File rotation
    RotationConfig rotation;

    // GPS synchronization
    bool sync_gps_time;
    bool include_gps_position;

    // Metadata
    char session_name[32];
    char driver_name[32];
    char vehicle_id[32];
} AdvancedLogConfig;

typedef struct {
    uint64_t timestamp_ms;       // Monotonic time
    uint64_t gps_timestamp_utc;  // GPS UTC time
    uint32_t sample_number;
    char channel_name[32];
    float value;
    bool is_digital;
} LogSample;

typedef struct {
    LogSample *samples;
    size_t capacity;
    size_t count;
    size_t write_index;
    size_t read_index;
    bool is_full;
} RingBuffer;

typedef struct {
    AdvancedLogConfig config;
    LogState state;

    // File handling
    void *file_handle;           // Platform-specific file handle
    uint32_t current_file_size_bytes;
    uint32_t total_bytes_written;
    uint32_t total_samples_written;

    // Buffers
    RingBuffer ring_buffer;      // Pre-trigger buffer
    uint8_t *write_buffer;
    size_t write_buffer_used;

    // Statistics
    uint64_t session_start_time_ms;
    uint64_t recording_start_time_ms;
    uint32_t samples_dropped;
    float compression_ratio;
    float write_throughput_kbps;

    // Error tracking
    char last_error[128];
    uint32_t error_count;
} AdvancedLogger;

// ============================================================================
// Public API
// ============================================================================

/**
 * @brief Initialize advanced logger
 * @param logger Logger instance
 * @param config Configuration parameters
 * @return true if successfully initialized
 */
bool advanced_logger_init(AdvancedLogger *logger, const AdvancedLogConfig *config);

/**
 * @brief Deinitialize and cleanup logger
 * @param logger Logger instance
 */
void advanced_logger_deinit(AdvancedLogger *logger);

/**
 * @brief Start logging session
 * @param logger Logger instance
 * @param session_name Optional session name (NULL = auto-generate)
 * @return true if successfully started
 */
bool advanced_logger_start(AdvancedLogger *logger, const char *session_name);

/**
 * @brief Stop logging session
 * @param logger Logger instance
 * @return true if successfully stopped
 */
bool advanced_logger_stop(AdvancedLogger *logger);

/**
 * @brief Pause logging (can be resumed)
 * @param logger Logger instance
 */
void advanced_logger_pause(AdvancedLogger *logger);

/**
 * @brief Resume paused logging
 * @param logger Logger instance
 */
void advanced_logger_resume(AdvancedLogger *logger);

/**
 * @brief Log a sample from signal bus
 * @param logger Logger instance
 * @param channel Channel name
 * @param value Signal value
 * @param timestamp_ms Timestamp in milliseconds
 * @param is_digital true if digital signal
 * @return true if sample was logged
 */
bool advanced_logger_log_sample(AdvancedLogger *logger, const char *channel,
                                float value, uint64_t timestamp_ms, bool is_digital);

/**
 * @brief Log all signals from signal bus
 * @param logger Logger instance
 * @param bus Signal bus to read from
 * @param timestamp_ms Current timestamp
 * @return Number of samples logged
 */
size_t advanced_logger_log_from_bus(AdvancedLogger *logger, const SignalBus *bus,
                                    uint64_t timestamp_ms);

/**
 * @brief Force flush write buffer to storage
 * @param logger Logger instance
 * @return true if successfully flushed
 */
bool advanced_logger_flush(AdvancedLogger *logger);

/**
 * @brief Add channel to whitelist
 * @param logger Logger instance
 * @param channel_name Channel name
 * @param sample_rate_hz Sample rate for this channel (0 = use default)
 * @return true if successfully added
 */
bool advanced_logger_add_channel(AdvancedLogger *logger, const char *channel_name,
                                 float sample_rate_hz);

/**
 * @brief Remove channel from logging
 * @param logger Logger instance
 * @param channel_name Channel name
 * @return true if successfully removed
 */
bool advanced_logger_remove_channel(AdvancedLogger *logger, const char *channel_name);

/**
 * @brief Configure trigger
 * @param logger Logger instance
 * @param mode Trigger mode
 * @param channel Trigger channel (for threshold mode)
 * @param threshold Threshold value
 * @param rising true for rising edge, false for falling
 * @param pre_trigger_ms Pre-trigger buffer duration
 * @return true if successfully configured
 */
bool advanced_logger_set_trigger(AdvancedLogger *logger, TriggerMode mode,
                                 const char *channel, float threshold,
                                 bool rising, uint32_t pre_trigger_ms);

/**
 * @brief Arm trigger for recording
 * @param logger Logger instance
 */
void advanced_logger_arm_trigger(AdvancedLogger *logger);

/**
 * @brief Manually trigger recording
 * @param logger Logger instance
 */
void advanced_logger_manual_trigger(AdvancedLogger *logger);

/**
 * @brief Get current logger state
 * @param logger Logger instance
 * @return Current state
 */
LogState advanced_logger_get_state(const AdvancedLogger *logger);

/**
 * @brief Get compression ratio
 * @param logger Logger instance
 * @return Compression ratio (e.g., 3.5 = 3.5:1)
 */
float advanced_logger_get_compression_ratio(const AdvancedLogger *logger);

/**
 * @brief Get write throughput
 * @param logger Logger instance
 * @return Throughput in kB/s
 */
float advanced_logger_get_throughput(const AdvancedLogger *logger);

/**
 * @brief Get total samples logged
 * @param logger Logger instance
 * @return Sample count
 */
uint32_t advanced_logger_get_sample_count(const AdvancedLogger *logger);

/**
 * @brief Get session duration
 * @param logger Logger instance
 * @return Duration in milliseconds
 */
uint64_t advanced_logger_get_session_duration(const AdvancedLogger *logger);

/**
 * @brief Export binary log to CSV
 * @param binary_path Input binary file path
 * @param csv_path Output CSV file path
 * @return true if successfully exported
 */
bool advanced_logger_export_to_csv(const char *binary_path, const char *csv_path);

/**
 * @brief Get last error message
 * @param logger Logger instance
 * @return Error string (empty if no error)
 */
const char* advanced_logger_get_last_error(const AdvancedLogger *logger);

/**
 * @brief Clear error state
 * @param logger Logger instance
 */
void advanced_logger_clear_error(AdvancedLogger *logger);

#ifdef __cplusplus
}
#endif
