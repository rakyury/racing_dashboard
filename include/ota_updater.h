#pragma once

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @file ota_updater.h
 * @brief Over-The-Air Firmware Update System
 *
 * Features:
 * - Dual-slot bootloader (safe rollback)
 * - WiFi/HTTP(S) download
 * - Incremental (delta) updates
 * - CRC32/SHA-256 verification
 * - Encrypted firmware (AES-256)
 * - Automatic rollback on boot failure
 * - Update via SD card (offline mode)
 * - Progress tracking and resume
 */

// ============================================================================
// Constants
// ============================================================================

#define OTA_MAX_VERSION_LEN 32
#define OTA_MAX_URL_LEN 256
#define OTA_CHUNK_SIZE 4096
#define OTA_SIGNATURE_SIZE 32

// ============================================================================
// Enumerations
// ============================================================================

typedef enum {
    OTA_STATE_IDLE,
    OTA_STATE_CHECKING,             // Checking for updates
    OTA_STATE_DOWNLOADING,
    OTA_STATE_VERIFYING,
    OTA_STATE_INSTALLING,
    OTA_STATE_COMPLETE,
    OTA_STATE_ERROR,
    OTA_STATE_ROLLBACK              // Rolling back to previous version
} OTAState;

typedef enum {
    OTA_ERROR_NONE,
    OTA_ERROR_NO_NETWORK,
    OTA_ERROR_SERVER_UNREACHABLE,
    OTA_ERROR_INVALID_RESPONSE,
    OTA_ERROR_VERSION_CHECK_FAILED,
    OTA_ERROR_DOWNLOAD_FAILED,
    OTA_ERROR_VERIFICATION_FAILED,
    OTA_ERROR_SIGNATURE_INVALID,
    OTA_ERROR_INSUFFICIENT_SPACE,
    OTA_ERROR_FLASH_WRITE_FAILED,
    OTA_ERROR_CORRUPT_IMAGE
} OTAError;

typedef enum {
    OTA_SOURCE_WIFI_HTTP,
    OTA_SOURCE_WIFI_HTTPS,
    OTA_SOURCE_SD_CARD,
    OTA_SOURCE_USB
} OTASource;

typedef enum {
    BOOT_SLOT_A,                    // Primary firmware slot
    BOOT_SLOT_B,                    // Backup firmware slot
    BOOT_SLOT_FACTORY               // Factory firmware (read-only)
} BootSlot;

// ============================================================================
// Structures
// ============================================================================

typedef struct {
    char version[OTA_MAX_VERSION_LEN];
    uint32_t build_number;
    uint64_t release_timestamp;     // Unix timestamp
    uint32_t firmware_size_bytes;
    uint8_t signature[OTA_SIGNATURE_SIZE];  // SHA-256 hash
    char changelog[256];
    bool is_critical;               // Critical security update
    bool is_beta;
} FirmwareMetadata;

typedef struct {
    char update_server_url[OTA_MAX_URL_LEN];
    char manifest_path[128];        // Path to version manifest JSON
    char ca_cert_path[128];         // CA certificate for HTTPS
    char api_key[64];               // API key for authenticated updates

    bool auto_check_updates;
    uint32_t check_interval_hours;

    bool allow_beta_updates;
    bool require_signature;
    bool enable_delta_updates;      // Incremental updates
    bool auto_install;              // Auto-install after download

    OTASource preferred_source;
} OTAConfig;

typedef struct {
    OTAState state;
    OTAError last_error;

    FirmwareMetadata current_version;
    FirmwareMetadata available_version;
    bool update_available;

    // Progress tracking
    uint32_t total_bytes;
    uint32_t downloaded_bytes;
    uint8_t progress_percent;
    uint32_t download_speed_kbps;

    // Verification
    uint8_t calculated_hash[OTA_SIGNATURE_SIZE];
    bool signature_verified;

    // Bootloader state
    BootSlot active_slot;
    BootSlot update_slot;
    uint32_t boot_count;
    bool rollback_available;

    // Timing
    uint64_t check_start_time_ms;
    uint64_t download_start_time_ms;
    uint64_t last_check_time_ms;

    char status_message[128];
} OTAUpdater;

typedef struct {
    BootSlot slot;
    char version[OTA_MAX_VERSION_LEN];
    uint32_t build_number;
    uint64_t install_timestamp;
    bool is_valid;
    bool is_active;
    uint32_t boot_count;
    uint32_t crc32;
} BootSlotInfo;

// ============================================================================
// Public API - Core Functions
// ============================================================================

/**
 * @brief Initialize OTA updater
 * @param ota OTA updater instance
 * @param config Configuration parameters
 * @return true if successfully initialized
 */
bool ota_init(OTAUpdater *ota, const OTAConfig *config);

/**
 * @brief Check for firmware updates
 * @param ota OTA updater instance
 * @return true if update is available
 */
bool ota_check_for_updates(OTAUpdater *ota);

/**
 * @brief Download available update
 * @param ota OTA updater instance
 * @return true if download successful
 */
bool ota_download_update(OTAUpdater *ota);

/**
 * @brief Verify downloaded firmware
 * @param ota OTA updater instance
 * @return true if firmware is valid
 */
bool ota_verify_firmware(OTAUpdater *ota);

/**
 * @brief Install verified firmware
 * @param ota OTA updater instance
 * @return true if installation successful
 */
bool ota_install_firmware(OTAUpdater *ota);

/**
 * @brief Complete update and reboot
 * @param ota OTA updater instance
 */
void ota_complete_and_reboot(OTAUpdater *ota);

/**
 * @brief Get current firmware version
 * @param ota OTA updater instance
 * @return Pointer to current version metadata
 */
const FirmwareMetadata* ota_get_current_version(const OTAUpdater *ota);

/**
 * @brief Get available update version
 * @param ota OTA updater instance
 * @return Pointer to available version metadata (NULL if none)
 */
const FirmwareMetadata* ota_get_available_version(const OTAUpdater *ota);

/**
 * @brief Get current state
 * @param ota OTA updater instance
 * @return Current OTA state
 */
OTAState ota_get_state(const OTAUpdater *ota);

/**
 * @brief Get download progress
 * @param ota OTA updater instance
 * @return Progress percentage (0-100)
 */
uint8_t ota_get_progress(const OTAUpdater *ota);

/**
 * @brief Get last error
 * @param ota OTA updater instance
 * @return Last error code
 */
OTAError ota_get_last_error(const OTAUpdater *ota);

/**
 * @brief Get status message
 * @param ota OTA updater instance
 * @return Status message string
 */
const char* ota_get_status_message(const OTAUpdater *ota);

// ============================================================================
// Public API - Bootloader Management
// ============================================================================

/**
 * @brief Get active boot slot
 * @return Active boot slot
 */
BootSlot ota_bootloader_get_active_slot(void);

/**
 * @brief Get boot slot information
 * @param slot Boot slot to query
 * @param info Output slot information
 * @return true if slot is valid
 */
bool ota_bootloader_get_slot_info(BootSlot slot, BootSlotInfo *info);

/**
 * @brief Mark boot as successful (prevents rollback)
 * @return true if successfully marked
 */
bool ota_bootloader_mark_boot_successful(void);

/**
 * @brief Trigger rollback to previous firmware
 * @return true if rollback initiated
 */
bool ota_bootloader_rollback(void);

/**
 * @brief Check if rollback is available
 * @return true if rollback slot is valid
 */
bool ota_bootloader_can_rollback(void);

/**
 * @brief Erase boot slot
 * @param slot Boot slot to erase
 * @return true if successfully erased
 */
bool ota_bootloader_erase_slot(BootSlot slot);

/**
 * @brief Set next boot slot
 * @param slot Boot slot for next reboot
 * @return true if successfully set
 */
bool ota_bootloader_set_next_boot_slot(BootSlot slot);

// ============================================================================
// Public API - SD Card Update
// ============================================================================

/**
 * @brief Check for firmware on SD card
 * @param firmware_path Path to firmware binary
 * @return true if valid firmware found
 */
bool ota_sd_check_firmware(const char *firmware_path);

/**
 * @brief Install firmware from SD card
 * @param firmware_path Path to firmware binary
 * @param ota OTA updater instance (for progress tracking)
 * @return true if successfully installed
 */
bool ota_sd_install_firmware(const char *firmware_path, OTAUpdater *ota);

// ============================================================================
// Public API - Delta Updates
// ============================================================================

/**
 * @brief Check if delta update is available
 * @param ota OTA updater instance
 * @param from_version Source version
 * @param to_version Target version
 * @return true if delta patch exists
 */
bool ota_delta_check_available(OTAUpdater *ota, const char *from_version,
                               const char *to_version);

/**
 * @brief Download delta patch
 * @param ota OTA updater instance
 * @return true if download successful
 */
bool ota_delta_download_patch(OTAUpdater *ota);

/**
 * @brief Apply delta patch to create new firmware
 * @param ota OTA updater instance
 * @param patch_path Path to delta patch
 * @param output_path Path to output firmware
 * @return true if patch applied successfully
 */
bool ota_delta_apply_patch(OTAUpdater *ota, const char *patch_path,
                           const char *output_path);

// ============================================================================
// Public API - Verification
// ============================================================================

/**
 * @brief Calculate SHA-256 hash of firmware
 * @param firmware_path Path to firmware binary
 * @param hash Output hash (32 bytes)
 * @return true if successfully calculated
 */
bool ota_calculate_firmware_hash(const char *firmware_path, uint8_t *hash);

/**
 * @brief Verify firmware signature
 * @param firmware_path Path to firmware binary
 * @param signature Expected signature (32 bytes)
 * @return true if signature matches
 */
bool ota_verify_firmware_signature(const char *firmware_path, const uint8_t *signature);

/**
 * @brief Check firmware integrity (CRC32)
 * @param firmware_path Path to firmware binary
 * @return true if CRC check passes
 */
bool ota_check_firmware_integrity(const char *firmware_path);

// ============================================================================
// Public API - Network
// ============================================================================

/**
 * @brief Download file via HTTP(S)
 * @param url File URL
 * @param output_path Local save path
 * @param progress_callback Progress callback (percentage, user_data)
 * @param user_data User data for callback
 * @return true if download successful
 */
bool ota_http_download_file(const char *url, const char *output_path,
                            void (*progress_callback)(uint8_t, void*),
                            void *user_data);

/**
 * @brief Fetch version manifest from server
 * @param ota OTA updater instance
 * @param manifest_url Manifest URL
 * @return true if manifest successfully fetched
 */
bool ota_fetch_version_manifest(OTAUpdater *ota, const char *manifest_url);

/**
 * @brief Parse version string (e.g., "2.1.3")
 * @param version_string Version string
 * @param major Output major version
 * @param minor Output minor version
 * @param patch Output patch version
 * @return true if successfully parsed
 */
bool ota_parse_version_string(const char *version_string,
                              uint8_t *major, uint8_t *minor, uint8_t *patch);

/**
 * @brief Compare versions
 * @param version_a First version string
 * @param version_b Second version string
 * @return -1 if A < B, 0 if A == B, 1 if A > B
 */
int ota_compare_versions(const char *version_a, const char *version_b);

// ============================================================================
// Public API - Utilities
// ============================================================================

/**
 * @brief Get error string
 * @param error Error code
 * @return Error description
 */
const char* ota_error_to_string(OTAError error);

/**
 * @brief Get state string
 * @param state OTA state
 * @return State description
 */
const char* ota_state_to_string(OTAState state);

/**
 * @brief Format version string
 * @param metadata Firmware metadata
 * @param output Output buffer
 * @param output_size Output buffer size
 */
void ota_format_version(const FirmwareMetadata *metadata, char *output, size_t output_size);

/**
 * @brief Format firmware size (e.g., "1.2 MB")
 * @param size_bytes Size in bytes
 * @param output Output buffer
 * @param output_size Output buffer size
 */
void ota_format_size(uint32_t size_bytes, char *output, size_t output_size);

#ifdef __cplusplus
}
#endif
