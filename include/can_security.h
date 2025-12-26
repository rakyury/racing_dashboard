#pragma once

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @file can_security.h
 * @brief CAN Bus Security Module with AES-256 Encryption
 *
 * Features:
 * - AES-256-GCM encryption for CAN messages
 * - HMAC-SHA256 message authentication
 * - Replay attack protection (sequence numbers)
 * - Key rotation support
 * - CAN bus diagnostics and health monitoring
 * - Intrusion detection (anomaly detection)
 */

// ============================================================================
// Constants
// ============================================================================

#define CAN_SECURITY_KEY_SIZE 32        // AES-256
#define CAN_SECURITY_IV_SIZE 12         // GCM IV
#define CAN_SECURITY_TAG_SIZE 16        // GCM authentication tag
#define CAN_SECURITY_MAX_PAYLOAD 64     // Maximum CAN-FD payload
#define CAN_SECURITY_SESSION_TIMEOUT_S 3600  // 1 hour

// ============================================================================
// Enumerations
// ============================================================================

typedef enum {
    CAN_SEC_MODE_DISABLED,
    CAN_SEC_MODE_MAC_ONLY,          // HMAC only (no encryption)
    CAN_SEC_MODE_ENCRYPT_MAC,       // AES-256-GCM
    CAN_SEC_MODE_ENCRYPT_SIGN       // AES + Digital signature
} CANSecurityMode;

typedef enum {
    CAN_SEC_STATUS_OK,
    CAN_SEC_STATUS_INVALID_KEY,
    CAN_SEC_STATUS_INVALID_MAC,
    CAN_SEC_STATUS_REPLAY_DETECTED,
    CAN_SEC_STATUS_SEQUENCE_ERROR,
    CAN_SEC_STATUS_DECRYPTION_FAILED,
    CAN_SEC_STATUS_BUFFER_OVERFLOW
} CANSecurityStatus;

typedef enum {
    CAN_DIAG_NORMAL,
    CAN_DIAG_WARNING,               // High error rate
    CAN_DIAG_CRITICAL,              // Bus-off or attack detected
    CAN_DIAG_BUS_OFF
} CANDiagnosticLevel;

// ============================================================================
// Structures
// ============================================================================

typedef struct {
    uint8_t key[CAN_SECURITY_KEY_SIZE];
    uint8_t key_id;                 // For key rotation
    uint64_t key_valid_until_s;     // Unix timestamp
    bool is_valid;
} CANSecurityKey;

typedef struct {
    CANSecurityMode mode;
    bool enable_replay_protection;
    bool enable_intrusion_detection;
    uint32_t max_sequence_gap;      // Max allowed gap in sequence numbers
    uint32_t key_rotation_interval_s;

    // Whitelist/blacklist
    uint32_t allowed_can_ids[64];
    size_t allowed_can_id_count;
    bool use_whitelist;
} CANSecurityConfig;

typedef struct {
    uint32_t sequence_number;       // Incremental counter
    uint32_t expected_seq_number;
    uint64_t last_rx_timestamp_ms;
    uint8_t nonce[CAN_SECURITY_IV_SIZE];
} CANSecuritySession;

typedef struct {
    CANSecurityConfig config;
    CANSecurityKey primary_key;
    CANSecurityKey backup_key;      // For key rotation
    CANSecuritySession session;

    // Statistics
    uint32_t total_tx_count;
    uint32_t total_rx_count;
    uint32_t encryption_count;
    uint32_t decryption_count;
    uint32_t mac_failures;
    uint32_t replay_attacks_blocked;
    uint32_t sequence_errors;

    // Error state
    CANSecurityStatus last_status;
    char last_error[128];
} CANSecurityContext;

// ============================================================================
// CAN Diagnostics
// ============================================================================

typedef struct {
    // Traffic statistics
    uint32_t rx_frame_count;
    uint32_t tx_frame_count;
    uint32_t rx_error_count;
    uint32_t tx_error_count;

    // Error details
    uint32_t stuff_error_count;
    uint32_t form_error_count;
    uint32_t ack_error_count;
    uint32_t crc_error_count;
    uint32_t bit_error_count;

    // Bus state
    uint32_t bus_off_events;
    uint32_t error_warning_events;
    uint32_t error_passive_events;

    // Performance
    float bus_load_percent;
    uint32_t peak_frame_rate;
    uint64_t last_rx_timestamp_ms;
    uint64_t last_tx_timestamp_ms;

    // Health
    CANDiagnosticLevel level;
    bool is_bus_off;
    uint8_t tx_error_counter;
    uint8_t rx_error_counter;
} CANDiagnostics;

typedef struct {
    uint32_t can_id;
    uint32_t rx_count;
    uint32_t error_count;
    uint64_t last_seen_ms;
    float expected_rate_hz;         // Expected message rate
    float actual_rate_hz;           // Measured rate
    bool is_anomalous;              // Rate deviation detected
} CANMessageStats;

typedef struct {
    CANMessageStats messages[256];  // Stats per CAN ID
    size_t message_count;

    // Anomaly detection
    uint32_t anomaly_count;
    uint32_t new_id_count;          // Unknown IDs detected
    bool intrusion_detected;
} CANIntrusionDetector;

// ============================================================================
// Public API - Encryption/Decryption
// ============================================================================

/**
 * @brief Initialize CAN security context
 * @param ctx Security context
 * @param config Configuration parameters
 * @return true if successfully initialized
 */
bool can_security_init(CANSecurityContext *ctx, const CANSecurityConfig *config);

/**
 * @brief Set encryption key
 * @param ctx Security context
 * @param key 256-bit key (32 bytes)
 * @param key_id Key identifier (0-255)
 * @return true if key is valid
 */
bool can_security_set_key(CANSecurityContext *ctx, const uint8_t *key, uint8_t key_id);

/**
 * @brief Generate random encryption key
 * @param key Output buffer (32 bytes)
 * @return true if successfully generated
 */
bool can_security_generate_key(uint8_t *key);

/**
 * @brief Encrypt CAN message
 * @param ctx Security context
 * @param plain_data Plaintext data
 * @param plain_len Length of plaintext
 * @param encrypted_data Output buffer for ciphertext
 * @param encrypted_len Output length
 * @return Security status
 */
CANSecurityStatus can_security_encrypt(CANSecurityContext *ctx,
                                       const uint8_t *plain_data, size_t plain_len,
                                       uint8_t *encrypted_data, size_t *encrypted_len);

/**
 * @brief Decrypt CAN message
 * @param ctx Security context
 * @param encrypted_data Ciphertext data
 * @param encrypted_len Length of ciphertext
 * @param plain_data Output buffer for plaintext
 * @param plain_len Output length
 * @return Security status
 */
CANSecurityStatus can_security_decrypt(CANSecurityContext *ctx,
                                       const uint8_t *encrypted_data, size_t encrypted_len,
                                       uint8_t *plain_data, size_t *plain_len);

/**
 * @brief Calculate HMAC for message authentication
 * @param ctx Security context
 * @param data Message data
 * @param data_len Data length
 * @param hmac Output HMAC (32 bytes)
 * @return true if successfully calculated
 */
bool can_security_calculate_hmac(CANSecurityContext *ctx,
                                 const uint8_t *data, size_t data_len,
                                 uint8_t *hmac);

/**
 * @brief Verify HMAC
 * @param ctx Security context
 * @param data Message data
 * @param data_len Data length
 * @param hmac HMAC to verify (32 bytes)
 * @return true if HMAC is valid
 */
bool can_security_verify_hmac(CANSecurityContext *ctx,
                              const uint8_t *data, size_t data_len,
                              const uint8_t *hmac);

/**
 * @brief Check if CAN ID is allowed (whitelist check)
 * @param ctx Security context
 * @param can_id CAN identifier
 * @return true if allowed
 */
bool can_security_is_id_allowed(const CANSecurityContext *ctx, uint32_t can_id);

/**
 * @brief Add CAN ID to whitelist
 * @param ctx Security context
 * @param can_id CAN identifier to allow
 * @return true if successfully added
 */
bool can_security_add_allowed_id(CANSecurityContext *ctx, uint32_t can_id);

/**
 * @brief Rotate encryption key
 * @param ctx Security context
 * @param new_key New 256-bit key
 * @param new_key_id New key identifier
 * @return true if successfully rotated
 */
bool can_security_rotate_key(CANSecurityContext *ctx,
                             const uint8_t *new_key, uint8_t new_key_id);

/**
 * @brief Get last error message
 * @param ctx Security context
 * @return Error string
 */
const char* can_security_get_last_error(const CANSecurityContext *ctx);

// ============================================================================
// Public API - Diagnostics
// ============================================================================

/**
 * @brief Initialize CAN diagnostics
 * @param diag Diagnostics structure
 */
void can_diagnostics_init(CANDiagnostics *diag);

/**
 * @brief Update diagnostics on frame receive
 * @param diag Diagnostics structure
 * @param success true if frame received successfully
 * @param timestamp_ms Current timestamp
 */
void can_diagnostics_update_rx(CANDiagnostics *diag, bool success, uint64_t timestamp_ms);

/**
 * @brief Update diagnostics on frame transmit
 * @param diag Diagnostics structure
 * @param success true if frame transmitted successfully
 * @param timestamp_ms Current timestamp
 */
void can_diagnostics_update_tx(CANDiagnostics *diag, bool success, uint64_t timestamp_ms);

/**
 * @brief Calculate bus load percentage
 * @param diag Diagnostics structure
 * @param sample_period_ms Measurement period in milliseconds
 * @return Bus load (0.0-100.0%)
 */
float can_diagnostics_calculate_bus_load(CANDiagnostics *diag, uint32_t sample_period_ms);

/**
 * @brief Get diagnostic level
 * @param diag Diagnostics structure
 * @return Current diagnostic level
 */
CANDiagnosticLevel can_diagnostics_get_level(const CANDiagnostics *diag);

/**
 * @brief Check if bus is healthy
 * @param diag Diagnostics structure
 * @return true if bus is operating normally
 */
bool can_diagnostics_is_healthy(const CANDiagnostics *diag);

/**
 * @brief Reset diagnostic counters
 * @param diag Diagnostics structure
 */
void can_diagnostics_reset(CANDiagnostics *diag);

/**
 * @brief Export diagnostics to JSON
 * @param diag Diagnostics structure
 * @param json_buffer Output buffer
 * @param buffer_size Buffer size
 * @return Number of bytes written
 */
size_t can_diagnostics_to_json(const CANDiagnostics *diag,
                               char *json_buffer, size_t buffer_size);

// ============================================================================
// Public API - Intrusion Detection
// ============================================================================

/**
 * @brief Initialize intrusion detector
 * @param detector Intrusion detector
 */
void can_intrusion_detector_init(CANIntrusionDetector *detector);

/**
 * @brief Update intrusion detector with received frame
 * @param detector Intrusion detector
 * @param can_id CAN identifier
 * @param timestamp_ms Timestamp
 */
void can_intrusion_detector_update(CANIntrusionDetector *detector,
                                   uint32_t can_id, uint64_t timestamp_ms);

/**
 * @brief Check for anomalies
 * @param detector Intrusion detector
 * @return true if anomaly detected
 */
bool can_intrusion_detector_check_anomaly(const CANIntrusionDetector *detector);

/**
 * @brief Get anomaly details
 * @param detector Intrusion detector
 * @param can_id CAN ID with anomaly
 * @param description Description buffer
 * @param desc_size Description buffer size
 * @return true if anomaly exists
 */
bool can_intrusion_detector_get_anomaly_details(const CANIntrusionDetector *detector,
                                                uint32_t *can_id,
                                                char *description, size_t desc_size);

/**
 * @brief Set expected message rate for CAN ID
 * @param detector Intrusion detector
 * @param can_id CAN identifier
 * @param expected_rate_hz Expected message rate
 */
void can_intrusion_detector_set_expected_rate(CANIntrusionDetector *detector,
                                              uint32_t can_id, float expected_rate_hz);

#ifdef __cplusplus
}
#endif
