#pragma once

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @file ml_analytics.h
 * @brief Machine Learning Analytics with TensorFlow Lite
 *
 * Features:
 * - Driver behavior analysis
 * - Predictive lap time estimation
 * - Anomaly detection (mechanical issues)
 * - Optimal shift point recommendation
 * - Tire wear prediction
 * - Fuel consumption optimization
 * - Track learning (racing line optimization)
 */

// ============================================================================
// Constants
// ============================================================================

#define ML_MAX_INPUT_SIZE 128
#define ML_MAX_OUTPUT_SIZE 32
#define ML_MAX_MODELS 8
#define ML_FEATURE_WINDOW_SIZE 100  // Samples for temporal features

// ============================================================================
// Enumerations
// ============================================================================

typedef enum {
    ML_MODEL_DRIVER_STYLE,          // Smooth vs aggressive
    ML_MODEL_LAP_TIME_PREDICTOR,
    ML_MODEL_SHIFT_POINT_OPTIMIZER,
    ML_MODEL_TIRE_WEAR_ESTIMATOR,
    ML_MODEL_FUEL_OPTIMIZER,
    ML_MODEL_ANOMALY_DETECTOR,
    ML_MODEL_RACING_LINE,
    ML_MODEL_CUSTOM
} MLModelType;

typedef enum {
    DRIVER_STYLE_SMOOTH,
    DRIVER_STYLE_NORMAL,
    DRIVER_STYLE_AGGRESSIVE,
    DRIVER_STYLE_ERRATIC
} DriverStyle;

typedef enum {
    ANOMALY_NONE,
    ANOMALY_ENGINE_MISFIRE,
    ANOMALY_BRAKE_FADE,
    ANOMALY_TIRE_DEGRADATION,
    ANOMALY_COOLING_ISSUE,
    ANOMALY_FUEL_STARVATION,
    ANOMALY_ELECTRICAL_FAULT
} AnomalyType;

// ============================================================================
// Structures
// ============================================================================

typedef struct {
    float input[ML_MAX_INPUT_SIZE];
    size_t input_size;
    float output[ML_MAX_OUTPUT_SIZE];
    size_t output_size;
} MLTensor;

typedef struct {
    MLModelType type;
    char model_path[128];           // Path to .tflite model
    void *interpreter;              // TFLite interpreter
    bool is_loaded;
    bool is_quantized;              // INT8 quantized model
    size_t input_tensor_size;
    size_t output_tensor_size;

    // Performance
    uint32_t inference_time_us;
    uint32_t total_inferences;
} MLModel;

typedef struct {
    MLModel models[ML_MAX_MODELS];
    size_t model_count;

    // Feature buffers (rolling windows)
    float rpm_history[ML_FEATURE_WINDOW_SIZE];
    float speed_history[ML_FEATURE_WINDOW_SIZE];
    float throttle_history[ML_FEATURE_WINDOW_SIZE];
    float brake_history[ML_FEATURE_WINDOW_SIZE];
    float steering_history[ML_FEATURE_WINDOW_SIZE];
    size_t history_index;

    // Inference results cache
    DriverStyle driver_style;
    float driver_style_confidence;
    uint64_t predicted_lap_time_ms;
    float prediction_confidence;
    uint16_t optimal_shift_rpm;
    float tire_wear_percent;
    AnomalyType detected_anomaly;
    float anomaly_confidence;

    // Performance
    bool enable_quantization;
    bool enable_gpu_delegate;       // For platforms with GPU
} MLAnalytics;

// Driver behavior metrics
typedef struct {
    DriverStyle style;
    float smoothness_score;         // 0.0-1.0 (1.0 = very smooth)
    float aggression_score;         // 0.0-1.0 (1.0 = very aggressive)
    float consistency_score;        // 0.0-1.0 (1.0 = very consistent)

    // Detailed metrics
    float avg_throttle_gradient;    // How quickly throttle is applied
    float avg_brake_gradient;
    float avg_steering_rate;
    uint32_t aggressive_events;     // Hard braking, wheel spin, etc.
} DriverBehaviorMetrics;

// Lap time prediction
typedef struct {
    uint64_t predicted_lap_time_ms;
    float confidence;               // 0.0-1.0
    int32_t delta_to_best_ms;
    uint8_t current_sector;
    uint64_t sector_predictions_ms[10];
} LapTimePrediction;

// Shift point optimization
typedef struct {
    uint16_t current_rpm;
    uint16_t optimal_shift_rpm;
    uint8_t current_gear;
    uint8_t recommended_gear;
    float time_gain_ms;             // Time gained by optimal shifting
    bool shift_now;                 // Immediate shift recommendation
} ShiftPointAdvice;

// Tire wear prediction
typedef struct {
    float front_left_percent;
    float front_right_percent;
    float rear_left_percent;
    float rear_right_percent;
    uint32_t estimated_laps_remaining;
    float degradation_rate;         // % per lap
    bool recommend_pit;
} TireWearEstimate;

// Fuel optimization
typedef struct {
    float current_fuel_kg;
    float consumption_rate_kg_per_lap;
    uint32_t laps_remaining_current_rate;
    float recommended_lift_and_coast_percent;
    float fuel_saving_target_kg_per_lap;
    uint32_t target_laps;
} FuelOptimization;

// Anomaly detection
typedef struct {
    AnomalyType type;
    float confidence;               // 0.0-1.0
    char description[128];
    uint64_t first_detected_ms;
    uint64_t last_detected_ms;
    bool is_critical;
    float severity;                 // 0.0-1.0
} AnomalyDetection;

// ============================================================================
// Public API - Core Functions
// ============================================================================

/**
 * @brief Initialize ML analytics
 * @param ml ML analytics instance
 * @return true if successfully initialized
 */
bool ml_analytics_init(MLAnalytics *ml);

/**
 * @brief Load TensorFlow Lite model
 * @param ml ML analytics instance
 * @param type Model type
 * @param model_path Path to .tflite file
 * @return true if model loaded successfully
 */
bool ml_load_model(MLAnalytics *ml, MLModelType type, const char *model_path);

/**
 * @brief Unload model from memory
 * @param ml ML analytics instance
 * @param type Model type
 */
void ml_unload_model(MLAnalytics *ml, MLModelType type);

/**
 * @brief Run inference on model
 * @param ml ML analytics instance
 * @param type Model type
 * @param input Input tensor
 * @param output Output tensor
 * @return true if inference successful
 */
bool ml_run_inference(MLAnalytics *ml, MLModelType type,
                     const MLTensor *input, MLTensor *output);

/**
 * @brief Update feature history with new data
 * @param ml ML analytics instance
 * @param rpm Engine RPM
 * @param speed Speed (km/h)
 * @param throttle Throttle position (0-100%)
 * @param brake Brake pressure (0-100%)
 * @param steering Steering angle (degrees)
 */
void ml_update_features(MLAnalytics *ml, float rpm, float speed,
                       float throttle, float brake, float steering);

// ============================================================================
// Public API - Driver Behavior Analysis
// ============================================================================

/**
 * @brief Analyze driver behavior
 * @param ml ML analytics instance
 * @param metrics Output driver behavior metrics
 * @return true if analysis successful
 */
bool ml_analyze_driver_behavior(MLAnalytics *ml, DriverBehaviorMetrics *metrics);

/**
 * @brief Get current driver style
 * @param ml ML analytics instance
 * @return Driver style classification
 */
DriverStyle ml_get_driver_style(const MLAnalytics *ml);

/**
 * @brief Get driver style confidence
 * @param ml ML analytics instance
 * @return Confidence score (0.0-1.0)
 */
float ml_get_driver_style_confidence(const MLAnalytics *ml);

// ============================================================================
// Public API - Lap Time Prediction
// ============================================================================

/**
 * @brief Predict lap time based on current pace
 * @param ml ML analytics instance
 * @param prediction Output lap time prediction
 * @return true if prediction successful
 */
bool ml_predict_lap_time(MLAnalytics *ml, LapTimePrediction *prediction);

/**
 * @brief Get predicted lap time
 * @param ml ML analytics instance
 * @return Predicted lap time in milliseconds
 */
uint64_t ml_get_predicted_lap_time(const MLAnalytics *ml);

// ============================================================================
// Public API - Shift Point Optimization
// ============================================================================

/**
 * @brief Get optimal shift point recommendation
 * @param ml ML analytics instance
 * @param current_rpm Current engine RPM
 * @param current_gear Current gear
 * @param advice Output shift point advice
 * @return true if recommendation available
 */
bool ml_get_shift_advice(MLAnalytics *ml, uint16_t current_rpm,
                        uint8_t current_gear, ShiftPointAdvice *advice);

/**
 * @brief Get optimal shift RPM
 * @param ml ML analytics instance
 * @return Optimal shift RPM
 */
uint16_t ml_get_optimal_shift_rpm(const MLAnalytics *ml);

// ============================================================================
// Public API - Tire Wear Prediction
// ============================================================================

/**
 * @brief Estimate tire wear
 * @param ml ML analytics instance
 * @param laps_completed Laps completed on current tires
 * @param estimate Output tire wear estimate
 * @return true if estimate successful
 */
bool ml_estimate_tire_wear(MLAnalytics *ml, uint32_t laps_completed,
                           TireWearEstimate *estimate);

/**
 * @brief Get tire wear percentage
 * @param ml ML analytics instance
 * @return Average tire wear (0-100%)
 */
float ml_get_tire_wear_percent(const MLAnalytics *ml);

// ============================================================================
// Public API - Fuel Optimization
// ============================================================================

/**
 * @brief Optimize fuel consumption strategy
 * @param ml ML analytics instance
 * @param current_fuel_kg Current fuel load
 * @param target_laps Target number of laps
 * @param optimization Output fuel optimization strategy
 * @return true if optimization successful
 */
bool ml_optimize_fuel(MLAnalytics *ml, float current_fuel_kg,
                     uint32_t target_laps, FuelOptimization *optimization);

// ============================================================================
// Public API - Anomaly Detection
// ============================================================================

/**
 * @brief Detect mechanical/performance anomalies
 * @param ml ML analytics instance
 * @param detection Output anomaly detection results
 * @return true if anomaly detected
 */
bool ml_detect_anomaly(MLAnalytics *ml, AnomalyDetection *detection);

/**
 * @brief Get detected anomaly type
 * @param ml ML analytics instance
 * @return Anomaly type (ANOMALY_NONE if none)
 */
AnomalyType ml_get_detected_anomaly(const MLAnalytics *ml);

/**
 * @brief Get anomaly confidence
 * @param ml ML analytics instance
 * @return Confidence score (0.0-1.0)
 */
float ml_get_anomaly_confidence(const MLAnalytics *ml);

// ============================================================================
// Public API - Utilities
// ============================================================================

/**
 * @brief Get driver style string
 * @param style Driver style
 * @return Style name
 */
const char* ml_driver_style_to_string(DriverStyle style);

/**
 * @brief Get anomaly type string
 * @param type Anomaly type
 * @return Anomaly name
 */
const char* ml_anomaly_type_to_string(AnomalyType type);

/**
 * @brief Get model inference time
 * @param ml ML analytics instance
 * @param type Model type
 * @return Inference time in microseconds
 */
uint32_t ml_get_inference_time(const MLAnalytics *ml, MLModelType type);

/**
 * @brief Enable/disable GPU acceleration
 * @param ml ML analytics instance
 * @param enable Enable GPU delegate
 */
void ml_set_gpu_acceleration(MLAnalytics *ml, bool enable);

#ifdef __cplusplus
}
#endif
