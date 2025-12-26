/**
 * @file rd_adc.h
 * @brief Racing Dashboard - ADC and Digital Input Interface
 */

#ifndef RD_ADC_H
#define RD_ADC_H

#include "rd_types.h"

// =============================================================================
// Hardware Configuration
// =============================================================================

// ADC channels available on STM32H743
#define RD_ADC_NUM_CHANNELS     8       // Number of analog input channels
#define RD_ADC_RESOLUTION       16      // ADC resolution in bits
#define RD_ADC_MAX_VALUE        65535   // Maximum ADC value

// Digital input channels
#define RD_DIN_NUM_CHANNELS     8       // Number of digital input channels

// ADC channel assignments (customize for your hardware)
typedef enum {
    RD_ADC_CH_AIN1 = 0,     // Analog Input 1 (e.g., Oil Pressure)
    RD_ADC_CH_AIN2,         // Analog Input 2 (e.g., Fuel Pressure)
    RD_ADC_CH_AIN3,         // Analog Input 3 (e.g., Oil Temperature)
    RD_ADC_CH_AIN4,         // Analog Input 4 (e.g., Coolant Temperature)
    RD_ADC_CH_AIN5,         // Analog Input 5 (e.g., EGT 1)
    RD_ADC_CH_AIN6,         // Analog Input 6 (e.g., EGT 2)
    RD_ADC_CH_AIN7,         // Analog Input 7 (General purpose)
    RD_ADC_CH_AIN8,         // Analog Input 8 (General purpose)
    RD_ADC_CH_COUNT
} RD_ADC_Channel_t;

// Digital input assignments
typedef enum {
    RD_DIN_CH_1 = 0,        // Digital Input 1 (e.g., Wheel Speed FL)
    RD_DIN_CH_2,            // Digital Input 2 (e.g., Wheel Speed FR)
    RD_DIN_CH_3,            // Digital Input 3 (e.g., Wheel Speed RL)
    RD_DIN_CH_4,            // Digital Input 4 (e.g., Wheel Speed RR)
    RD_DIN_CH_5,            // Digital Input 5 (General purpose)
    RD_DIN_CH_6,            // Digital Input 6 (General purpose)
    RD_DIN_CH_7,            // Digital Input 7 (General purpose)
    RD_DIN_CH_8,            // Digital Input 8 (General purpose)
    RD_DIN_CH_COUNT
} RD_DIN_Channel_t;

// =============================================================================
// Configuration Structures
// =============================================================================

/**
 * @brief ADC hardware configuration
 */
typedef struct {
    uint32_t sample_rate_hz;            // Sample rate in Hz
    uint8_t oversample_bits;            // Oversampling bits (0-4)
    bool use_dma;                       // Use DMA for sampling
} RD_ADC_Config_t;

/**
 * @brief Digital input hardware configuration
 */
typedef struct {
    bool enable_pull_up;                // Enable internal pull-up
    bool enable_pull_down;              // Enable internal pull-down
    bool capture_both_edges;            // Capture both edges for frequency
} RD_DIN_Config_t;

/**
 * @brief Digital input runtime state
 */
typedef struct {
    uint32_t frequency_mhz;             // Measured frequency in mHz
    uint32_t pulse_count;               // Total pulse count
    uint32_t duty_cycle;                // Duty cycle in 0.01% (0-10000)
    bool state;                         // Current digital state
    uint32_t last_edge_us;              // Timestamp of last edge
} RD_DIN_State_t;

// =============================================================================
// Public API
// =============================================================================

/**
 * @brief Initialize ADC subsystem
 * @param config ADC configuration
 * @return RD_OK on success
 */
RD_Error_t RD_ADC_Init(const RD_ADC_Config_t *config);

/**
 * @brief Deinitialize ADC subsystem
 */
void RD_ADC_Deinit(void);

/**
 * @brief Start continuous ADC sampling
 * @return RD_OK on success
 */
RD_Error_t RD_ADC_Start(void);

/**
 * @brief Stop continuous ADC sampling
 */
void RD_ADC_Stop(void);

/**
 * @brief Get raw ADC value for channel
 * @param channel ADC channel
 * @return Raw ADC value (0-65535)
 */
uint16_t RD_ADC_GetRaw(RD_ADC_Channel_t channel);

/**
 * @brief Get averaged ADC value for channel
 * @param channel ADC channel
 * @return Averaged ADC value
 */
uint16_t RD_ADC_GetAveraged(RD_ADC_Channel_t channel);

/**
 * @brief Get voltage for ADC channel
 * @param channel ADC channel
 * @param vref Reference voltage (typically 3.3V)
 * @return Voltage in volts
 */
float RD_ADC_GetVoltage(RD_ADC_Channel_t channel, float vref);

/**
 * @brief Set ADC channel enable state
 * @param channel ADC channel
 * @param enabled Enable state
 */
void RD_ADC_SetChannelEnabled(RD_ADC_Channel_t channel, bool enabled);

/**
 * @brief Check if ADC is ready
 * @return true if ADC data is available
 */
bool RD_ADC_IsReady(void);

// =============================================================================
// Digital Input API
// =============================================================================

/**
 * @brief Initialize digital inputs subsystem
 * @param config Configuration for all channels
 * @return RD_OK on success
 */
RD_Error_t RD_DIN_Init(const RD_DIN_Config_t *config);

/**
 * @brief Deinitialize digital inputs
 */
void RD_DIN_Deinit(void);

/**
 * @brief Get digital input state
 * @param channel Digital input channel
 * @return Current state (true = high)
 */
bool RD_DIN_GetState(RD_DIN_Channel_t channel);

/**
 * @brief Get digital input frequency
 * @param channel Digital input channel
 * @return Frequency in mHz (millihertz)
 */
uint32_t RD_DIN_GetFrequency(RD_DIN_Channel_t channel);

/**
 * @brief Get digital input pulse count
 * @param channel Digital input channel
 * @return Total pulse count since start/reset
 */
uint32_t RD_DIN_GetPulseCount(RD_DIN_Channel_t channel);

/**
 * @brief Reset pulse count for channel
 * @param channel Digital input channel
 */
void RD_DIN_ResetPulseCount(RD_DIN_Channel_t channel);

/**
 * @brief Get digital input duty cycle
 * @param channel Digital input channel
 * @return Duty cycle in 0.01% (0-10000)
 */
uint32_t RD_DIN_GetDutyCycle(RD_DIN_Channel_t channel);

/**
 * @brief Get full state for digital input
 * @param channel Digital input channel
 * @param state Output state structure
 * @return RD_OK on success
 */
RD_Error_t RD_DIN_GetFullState(RD_DIN_Channel_t channel, RD_DIN_State_t *state);

/**
 * @brief Configure digital input mode
 * @param channel Digital input channel
 * @param type Input type (on/off, frequency, etc.)
 * @return RD_OK on success
 */
RD_Error_t RD_DIN_SetMode(RD_DIN_Channel_t channel, RD_DigitalInputType_t type);

/**
 * @brief Process digital inputs (call from timer interrupt)
 * Called internally by hardware timer
 */
void RD_DIN_Process(void);

// =============================================================================
// Internal Temperature Sensor
// =============================================================================

/**
 * @brief Get MCU internal temperature
 * @return Temperature in Celsius
 */
float RD_ADC_GetMCUTemperature(void);

/**
 * @brief Get Vrefint voltage
 * @return Reference voltage in volts
 */
float RD_ADC_GetVrefint(void);

#endif // RD_ADC_H
