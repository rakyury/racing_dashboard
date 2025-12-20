#pragma once

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @file lap_timer.h
 * @brief Professional lap timing system with track mapping and sector analysis
 *
 * Features:
 * - GPS-based lap detection with configurable finish line
 * - Multi-sector timing (up to 10 sectors per track)
 * - Best lap tracking with delta calculations
 * - Predictive lap time estimation
 * - Track database with popular circuits
 * - Auto-detection of known tracks
 * - Export to Video BBOX format for overlay
 */

// ============================================================================
// Constants
// ============================================================================

#define MAX_SECTORS 10
#define MAX_LAPS 1000
#define MAX_TRACKS 50
#define GPS_PROXIMITY_THRESHOLD_M 15.0f  // Distance to trigger sector/finish

// ============================================================================
// Structures
// ============================================================================

typedef struct {
    double lat;                  // Latitude (degrees)
    double lon;                  // Longitude (degrees)
    float radius_m;              // Detection radius (meters)
    char name[32];               // Sector/finish line name
} GPSPoint;

typedef struct {
    char track_name[64];
    char country[32];
    char circuit_type[16];       // "road", "oval", "street", "rally"

    GPSPoint start_finish;
    GPSPoint sectors[MAX_SECTORS];
    size_t sector_count;

    double track_length_m;
    float track_record_s;        // Official track record
    char record_holder[32];

    bool is_validated;           // GPS points verified
} TrackMap;

typedef struct {
    uint32_t lap_number;
    uint64_t lap_time_ms;
    uint64_t sector_times_ms[MAX_SECTORS];
    bool sector_valid[MAX_SECTORS];

    // Performance metrics
    float max_speed_kmh;
    float avg_speed_kmh;
    float min_speed_kmh;

    // Position data
    double start_lat;
    double start_lon;
    uint64_t timestamp_utc;

    // Validity
    bool is_valid;
    bool is_out_lap;             // Outlap from pits
    bool is_in_lap;              // Inlap to pits
} LapRecord;

typedef struct {
    uint8_t current_sector;
    uint64_t sector_start_time_ms;
    uint64_t lap_start_time_ms;

    double last_lat;
    double last_lon;
    float current_speed_kmh;

    bool in_lap_now;
    bool sector_triggered[MAX_SECTORS];
} LapState;

typedef struct {
    TrackMap current_track;
    bool track_loaded;
    bool auto_detection_enabled;

    LapRecord laps[MAX_LAPS];
    size_t lap_count;

    LapRecord best_lap;
    LapRecord last_lap;
    LapRecord current_lap;

    LapState state;

    // Delta timing
    int32_t current_lap_delta_ms;     // vs best lap
    int32_t sector_delta_ms[MAX_SECTORS];

    // Predictive
    uint64_t predicted_lap_time_ms;
    float prediction_confidence;       // 0.0-1.0

    // Statistics
    uint32_t total_distance_m;
    uint32_t valid_lap_count;
    uint32_t invalid_lap_count;
} LapTimer;

// ============================================================================
// Track Database
// ============================================================================

extern const TrackMap TRACK_SPA_FRANCORCHAMPS;
extern const TrackMap TRACK_NURBURGRING_GP;
extern const TrackMap TRACK_SILVERSTONE;
extern const TrackMap TRACK_MONZA;
extern const TrackMap TRACK_SUZUKA;

// ============================================================================
// Public API
// ============================================================================

/**
 * @brief Initialize lap timer
 * @param lt LapTimer instance
 */
void lap_timer_init(LapTimer *lt);

/**
 * @brief Load track configuration
 * @param lt LapTimer instance
 * @param track Track map to load
 * @return true if successfully loaded
 */
bool lap_timer_load_track(LapTimer *lt, const TrackMap *track);

/**
 * @brief Load track by name
 * @param lt LapTimer instance
 * @param track_name Track name
 * @return true if found and loaded
 */
bool lap_timer_load_track_by_name(LapTimer *lt, const char *track_name);

/**
 * @brief Update lap timer with GPS data
 * @param lt LapTimer instance
 * @param lat Current latitude
 * @param lon Current longitude
 * @param speed_kmh Current speed
 * @param timestamp_ms Current timestamp
 */
void lap_timer_update(LapTimer *lt, double lat, double lon,
                     float speed_kmh, uint64_t timestamp_ms);

/**
 * @brief Check if position crosses sector/finish line
 * @param lt LapTimer instance
 * @param lat Current latitude
 * @param lon Current longitude
 * @param point GPS point to check
 * @return true if crossed
 */
bool lap_timer_check_crossing(const LapTimer *lt, double lat, double lon,
                              const GPSPoint *point);

/**
 * @brief Manually start new lap
 * @param lt LapTimer instance
 * @param timestamp_ms Current timestamp
 */
void lap_timer_manual_start_lap(LapTimer *lt, uint64_t timestamp_ms);

/**
 * @brief Get current lap delta vs best lap
 * @param lt LapTimer instance
 * @return Delta in milliseconds (negative = ahead)
 */
int32_t lap_timer_get_current_delta(const LapTimer *lt);

/**
 * @brief Get sector delta vs best lap
 * @param lt LapTimer instance
 * @param sector Sector number (0-based)
 * @return Delta in milliseconds (negative = ahead)
 */
int32_t lap_timer_get_sector_delta(const LapTimer *lt, uint8_t sector);

/**
 * @brief Get predicted lap time
 * @param lt LapTimer instance
 * @return Predicted lap time in milliseconds
 */
uint64_t lap_timer_get_predicted_time(const LapTimer *lt);

/**
 * @brief Reset all lap data
 * @param lt LapTimer instance
 */
void lap_timer_reset(LapTimer *lt);

/**
 * @brief Get best lap record
 * @param lt LapTimer instance
 * @return Pointer to best lap (NULL if none)
 */
const LapRecord* lap_timer_get_best_lap(const LapTimer *lt);

/**
 * @brief Get last completed lap
 * @param lt LapTimer instance
 * @return Pointer to last lap (NULL if none)
 */
const LapRecord* lap_timer_get_last_lap(const LapTimer *lt);

/**
 * @brief Export laps to CSV
 * @param lt LapTimer instance
 * @param filepath Output file path
 * @return true if successfully exported
 */
bool lap_timer_export_to_csv(const LapTimer *lt, const char *filepath);

/**
 * @brief Export to Video BBOX format (for video overlay)
 * @param lt LapTimer instance
 * @param filepath Output file path
 * @return true if successfully exported
 */
bool lap_timer_export_to_vbo(const LapTimer *lt, const char *filepath);

/**
 * @brief Calculate distance between two GPS coordinates
 * @param lat1 Latitude point 1
 * @param lon1 Longitude point 1
 * @param lat2 Latitude point 2
 * @param lon2 Longitude point 2
 * @return Distance in meters
 */
float lap_timer_calculate_distance(double lat1, double lon1, double lat2, double lon2);

/**
 * @brief Auto-detect current track based on GPS position
 * @param lt LapTimer instance
 * @param lat Current latitude
 * @param lon Current longitude
 * @return true if track detected and loaded
 */
bool lap_timer_auto_detect_track(LapTimer *lt, double lat, double lon);

#ifdef __cplusplus
}
#endif
