/**
 * @file rd_can.h
 * @brief Racing Dashboard - CAN Bus Interface
 */

#ifndef RD_CAN_H
#define RD_CAN_H

#include "rd_types.h"

// =============================================================================
// Configuration
// =============================================================================

#define RD_CAN_NUM_INTERFACES   2       // CAN1 and CAN2 (FDCAN)
#define RD_CAN_MAX_RX_FILTERS   32      // Maximum RX filters per interface
#define RD_CAN_TX_QUEUE_SIZE    16      // TX message queue size
#define RD_CAN_RX_QUEUE_SIZE    64      // RX message queue size

// CAN interface identifiers
typedef enum {
    RD_CAN_1 = 0,       // Primary CAN interface
    RD_CAN_2 = 1,       // Secondary CAN interface
    RD_CAN_COUNT
} RD_CAN_Interface_t;

// =============================================================================
// CAN Message Structure
// =============================================================================

/**
 * @brief CAN message flags
 */
typedef enum {
    RD_CAN_FLAG_NONE       = 0x00,
    RD_CAN_FLAG_EXTENDED   = 0x01,      // Extended ID (29-bit)
    RD_CAN_FLAG_RTR        = 0x02,      // Remote Transmission Request
    RD_CAN_FLAG_FD         = 0x04,      // CAN FD frame
    RD_CAN_FLAG_BRS        = 0x08,      // Bit Rate Switch (FD only)
} RD_CAN_Flags_t;

/**
 * @brief CAN message structure
 */
typedef struct {
    uint32_t id;                        // Message ID (11 or 29 bit)
    uint8_t data[64];                   // Data (up to 64 bytes for CAN FD)
    uint8_t dlc;                        // Data Length Code
    uint8_t flags;                      // Message flags
    uint32_t timestamp;                 // Reception timestamp (ms)
} RD_CAN_Message_t;

// =============================================================================
// CAN Configuration
// =============================================================================

/**
 * @brief CAN bus speed presets
 */
typedef enum {
    RD_CAN_SPEED_125K = 0,
    RD_CAN_SPEED_250K,
    RD_CAN_SPEED_500K,
    RD_CAN_SPEED_1M,
    // CAN FD data rates
    RD_CAN_FD_SPEED_2M,
    RD_CAN_FD_SPEED_4M,
    RD_CAN_FD_SPEED_5M,
    RD_CAN_FD_SPEED_8M,
} RD_CAN_Speed_t;

/**
 * @brief CAN interface configuration
 */
typedef struct {
    RD_CAN_Speed_t speed;               // Bus speed
    RD_CAN_Speed_t fd_data_speed;       // FD data phase speed (0 for classic CAN)
    bool fd_enabled;                    // Enable CAN FD
    bool silent_mode;                   // Listen only mode
    bool loopback_mode;                 // Internal loopback (for testing)
    bool auto_retransmit;               // Automatic retransmission
} RD_CAN_Config_t;

/**
 * @brief RX filter configuration
 */
typedef struct {
    uint32_t id;                        // Filter ID
    uint32_t mask;                      // Filter mask (1 = must match)
    bool extended;                      // Extended ID filter
    bool enabled;                       // Filter enabled
} RD_CAN_Filter_t;

/**
 * @brief CAN bus status
 */
typedef struct {
    bool bus_off;                       // Bus off state
    bool error_passive;                 // Error passive state
    bool error_warning;                 // Error warning state
    uint8_t tx_error_count;             // TX error counter
    uint8_t rx_error_count;             // RX error counter
    uint32_t rx_count;                  // Total received messages
    uint32_t tx_count;                  // Total transmitted messages
    uint32_t error_count;               // Total errors
} RD_CAN_Status_t;

// =============================================================================
// CAN RX Callback
// =============================================================================

/**
 * @brief CAN message receive callback type
 * @param iface Interface that received the message
 * @param msg Received message
 * @param user_data User data pointer
 */
typedef void (*RD_CAN_RxCallback_t)(RD_CAN_Interface_t iface,
                                    const RD_CAN_Message_t *msg,
                                    void *user_data);

// =============================================================================
// Public API
// =============================================================================

/**
 * @brief Initialize CAN interface
 * @param iface Interface to initialize
 * @param config Configuration
 * @return RD_OK on success
 */
RD_Error_t RD_CAN_Init(RD_CAN_Interface_t iface, const RD_CAN_Config_t *config);

/**
 * @brief Deinitialize CAN interface
 * @param iface Interface to deinitialize
 */
void RD_CAN_Deinit(RD_CAN_Interface_t iface);

/**
 * @brief Start CAN interface
 * @param iface Interface to start
 * @return RD_OK on success
 */
RD_Error_t RD_CAN_Start(RD_CAN_Interface_t iface);

/**
 * @brief Stop CAN interface
 * @param iface Interface to stop
 */
void RD_CAN_Stop(RD_CAN_Interface_t iface);

/**
 * @brief Add RX filter
 * @param iface Interface
 * @param filter Filter configuration
 * @return Filter index on success, negative on error
 */
int RD_CAN_AddFilter(RD_CAN_Interface_t iface, const RD_CAN_Filter_t *filter);

/**
 * @brief Remove RX filter
 * @param iface Interface
 * @param filter_index Filter index to remove
 * @return RD_OK on success
 */
RD_Error_t RD_CAN_RemoveFilter(RD_CAN_Interface_t iface, int filter_index);

/**
 * @brief Clear all filters
 * @param iface Interface
 */
void RD_CAN_ClearFilters(RD_CAN_Interface_t iface);

/**
 * @brief Transmit CAN message
 * @param iface Interface to transmit on
 * @param msg Message to transmit
 * @return RD_OK on success
 */
RD_Error_t RD_CAN_Transmit(RD_CAN_Interface_t iface, const RD_CAN_Message_t *msg);

/**
 * @brief Transmit CAN message (queued)
 * @param iface Interface to transmit on
 * @param msg Message to transmit
 * @return RD_OK on success (message queued)
 */
RD_Error_t RD_CAN_TransmitQueued(RD_CAN_Interface_t iface, const RD_CAN_Message_t *msg);

/**
 * @brief Receive CAN message (non-blocking)
 * @param iface Interface to receive from
 * @param msg Output message
 * @return RD_OK if message received, RD_ERR_EMPTY if no message
 */
RD_Error_t RD_CAN_Receive(RD_CAN_Interface_t iface, RD_CAN_Message_t *msg);

/**
 * @brief Register RX callback
 * @param iface Interface
 * @param callback Callback function
 * @param user_data User data passed to callback
 * @return RD_OK on success
 */
RD_Error_t RD_CAN_RegisterCallback(RD_CAN_Interface_t iface,
                                   RD_CAN_RxCallback_t callback,
                                   void *user_data);

/**
 * @brief Get CAN bus status
 * @param iface Interface
 * @param status Output status
 * @return RD_OK on success
 */
RD_Error_t RD_CAN_GetStatus(RD_CAN_Interface_t iface, RD_CAN_Status_t *status);

/**
 * @brief Check if CAN bus is OK
 * @param iface Interface
 * @return true if bus is operational
 */
bool RD_CAN_IsOK(RD_CAN_Interface_t iface);

/**
 * @brief Reset CAN error counters
 * @param iface Interface
 */
void RD_CAN_ResetErrors(RD_CAN_Interface_t iface);

/**
 * @brief Process CAN (call from main loop or task)
 * Processes TX queue and handles received messages
 */
void RD_CAN_Process(void);

// =============================================================================
// CAN Protocol Helpers
// =============================================================================

/**
 * @brief Extract signal from CAN message
 * @param msg CAN message
 * @param start_bit Start bit position
 * @param bit_length Number of bits
 * @param byte_order Byte order
 * @param data_type Data type
 * @param scale Scale factor
 * @param offset Offset
 * @return Extracted and scaled value
 */
float RD_CAN_ExtractSignal(const RD_CAN_Message_t *msg,
                           uint8_t start_bit,
                           uint8_t bit_length,
                           RD_CAN_ByteOrder_t byte_order,
                           RD_CAN_DataType_t data_type,
                           float scale,
                           float offset);

/**
 * @brief Pack signal into CAN message
 * @param msg CAN message
 * @param value Value to pack
 * @param start_bit Start bit position
 * @param bit_length Number of bits
 * @param byte_order Byte order
 * @param scale Scale factor
 * @param offset Offset
 */
void RD_CAN_PackSignal(RD_CAN_Message_t *msg,
                       float value,
                       uint8_t start_bit,
                       uint8_t bit_length,
                       RD_CAN_ByteOrder_t byte_order,
                       float scale,
                       float offset);

/**
 * @brief Build CAN message from parameters
 * @param msg Output message
 * @param id Message ID
 * @param data Data bytes
 * @param dlc Data length
 * @param extended Extended ID flag
 */
void RD_CAN_BuildMessage(RD_CAN_Message_t *msg,
                         uint32_t id,
                         const uint8_t *data,
                         uint8_t dlc,
                         bool extended);

#endif // RD_CAN_H
