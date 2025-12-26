/**
 * @file rd_laptimer.h
 * @brief Racing Dashboard - Lap Timer Module
 */

#ifndef RD_LAPTIMER_H
#define RD_LAPTIMER_H

#include "rd_types.h"

// =============================================================================
// Configuration
// =============================================================================

#define RD_LAP_MAX_SECTORS          6       // Maximum sectors per track
#define RD_LAP_MAX_STORED_LAPS      100     // Maximum stored lap times
#define RD_LAP_MAX_TRACKS           50      // Maximum stored tracks
#define RD_LAP_NAME_LENGTH          32      // Track name length

// =============================================================================
// Track Definitions
// =============================================================================

/**
 * @brief Finish line / sector line definition
 */
typedef struct {
    double lat1;                            // Line start latitude
    double lon1;                            // Line start longitude
    double lat2;                            // Line end latitude
    double lon2;                            // Line end longitude
    float heading;                          // Required crossing heading (0 = any)
    float heading_tolerance;                // Heading tolerance in degrees
} RD_TrackLine_t;

/**
 * @brief Track definition
 */
typedef struct {
    char name[RD_LAP_NAME_LENGTH];          // Track name
    RD_TrackLine_t start_finish;            // Start/Finish line
    RD_TrackLine_t sectors[RD_LAP_MAX_SECTORS]; // Sector lines
    uint8_t sector_count;                   // Number of sectors (0-6)
    double center_lat;                      // Track center latitude
    double center_lon;                      // Track center longitude
    float radius;                           // Detection radius in meters
    bool enabled;                           // Track enabled
} RD_Track_t;

// =============================================================================
// Lap Data Structures
// =============================================================================

/**
 * @brief Individual lap data
 */
typedef struct {
    uint32_t lap_time_ms;                   // Total lap time in milliseconds
    uint32_t sector_times_ms[RD_LAP_MAX_SECTORS]; // Sector times
    uint8_t sector_count;                   // Number of sectors
    uint32_t timestamp;                     // Unix timestamp when lap completed
    bool valid;                             // Lap validity
    bool best_lap;                          // Was best lap when recorded
    float max_speed;                        // Maximum speed during lap (m/s)
    float avg_speed;                        // Average speed during lap (m/s)
} RD_LapData_t;

/**
 * @brief Current session data
 */
typedef struct {
    RD_LapData_t laps[RD_LAP_MAX_STORED_LAPS];
    uint16_t lap_count;
    uint16_t best_lap_index;
    uint32_t best_lap_time_ms;
    uint32_t best_sector_times_ms[RD_LAP_MAX_SECTORS];
    uint32_t session_start;                 // Session start timestamp
    uint32_t total_distance;                // Total distance in meters
} RD_Session_t;

/**
 * @brief Lap timer status
 */
typedef struct {
    bool active;                            // Timer running
    bool in_pit;                            // Currently in pit lane
    uint32_t current_lap_time_ms;           // Current lap time
    uint32_t current_sector_time_ms;        // Current sector time
    uint32_t last_lap_time_ms;              // Last completed lap time
    uint32_t best_lap_time_ms;              // Best lap time (session)
    int32_t delta_ms;                       // Delta to best lap (+ slower, - faster)
    int32_t predicted_lap_ms;               // Predicted lap time based on current pace
    uint16_t lap_number;                    // Current lap number
    uint8_t current_sector;                 // Current sector (0-based)
    const RD_Track_t *active_track;         // Active track (or NULL)
} RD_LapTimer_Status_t;

// =============================================================================
// Callbacks
// =============================================================================

/**
 * @brief Lap completed callback
 */
typedef void (*RD_LapTimer_LapCallback_t)(const RD_LapData_t *lap, void *user_data);

/**
 * @brief Sector completed callback
 */
typedef void (*RD_LapTimer_SectorCallback_t)(uint8_t sector, uint32_t time_ms, void *user_data);

// =============================================================================
// Public API
// =============================================================================

/**
 * @brief Initialize lap timer
 * @return RD_OK on success
 */
RD_Error_t RD_LapTimer_Init(void);

/**
 * @brief Deinitialize lap timer
 */
void RD_LapTimer_Deinit(void);

/**
 * @brief Start lap timing
 * @return RD_OK on success
 */
RD_Error_t RD_LapTimer_Start(void);

/**
 * @brief Stop lap timing
 */
void RD_LapTimer_Stop(void);

/**
 * @brief Reset lap timer and session data
 */
void RD_LapTimer_Reset(void);

/**
 * @brief Get current lap timer status
 * @param status Output status
 * @return RD_OK on success
 */
RD_Error_t RD_LapTimer_GetStatus(RD_LapTimer_Status_t *status);

/**
 * @brief Get current lap time in milliseconds
 * @return Current lap time
 */
uint32_t RD_LapTimer_GetCurrentTime(void);

/**
 * @brief Get last completed lap time
 * @return Last lap time in ms
 */
uint32_t RD_LapTimer_GetLastLapTime(void);

/**
 * @brief Get best lap time (session)
 * @return Best lap time in ms
 */
uint32_t RD_LapTimer_GetBestLapTime(void);

/**
 * @brief Get delta to best lap
 * @return Delta in ms (positive = slower, negative = faster)
 */
int32_t RD_LapTimer_GetDelta(void);

/**
 * @brief Get predicted lap time
 * @return Predicted time in ms
 */
uint32_t RD_LapTimer_GetPredictedTime(void);

/**
 * @brief Get current lap number
 * @return Lap number (starts at 1)
 */
uint16_t RD_LapTimer_GetLapNumber(void);

/**
 * @brief Get current sector
 * @return Sector number (0-based)
 */
uint8_t RD_LapTimer_GetCurrentSector(void);

/**
 * @brief Get session data
 * @return Pointer to session data
 */
const RD_Session_t* RD_LapTimer_GetSession(void);

/**
 * @brief Get specific lap data
 * @param lap_index Lap index (0 = most recent)
 * @param lap Output lap data
 * @return RD_OK on success
 */
RD_Error_t RD_LapTimer_GetLap(uint16_t lap_index, RD_LapData_t *lap);

// =============================================================================
// Track Management
// =============================================================================

/**
 * @brief Set active track
 * @param track Track definition (NULL for manual mode)
 * @return RD_OK on success
 */
RD_Error_t RD_LapTimer_SetTrack(const RD_Track_t *track);

/**
 * @brief Get active track
 * @return Pointer to active track or NULL
 */
const RD_Track_t* RD_LapTimer_GetTrack(void);

/**
 * @brief Auto-detect track from GPS position
 * @param tracks Array of available tracks
 * @param track_count Number of tracks
 * @return Index of detected track or -1 if none
 */
int RD_LapTimer_AutoDetectTrack(const RD_Track_t *tracks, uint8_t track_count);

/**
 * @brief Load tracks from storage
 * @param tracks Output track array
 * @param max_tracks Maximum tracks to load
 * @return Number of tracks loaded
 */
int RD_LapTimer_LoadTracks(RD_Track_t *tracks, uint8_t max_tracks);

/**
 * @brief Save track to storage
 * @param track Track to save
 * @return RD_OK on success
 */
RD_Error_t RD_LapTimer_SaveTrack(const RD_Track_t *track);

/**
 * @brief Learn finish line from GPS crossing
 * @param line Output finish line
 * @return RD_OK on success
 */
RD_Error_t RD_LapTimer_LearnFinishLine(RD_TrackLine_t *line);

// =============================================================================
// Callbacks
// =============================================================================

/**
 * @brief Register lap completed callback
 * @param callback Callback function
 * @param user_data User data
 */
void RD_LapTimer_SetLapCallback(RD_LapTimer_LapCallback_t callback, void *user_data);

/**
 * @brief Register sector completed callback
 * @param callback Callback function
 * @param user_data User data
 */
void RD_LapTimer_SetSectorCallback(RD_LapTimer_SectorCallback_t callback, void *user_data);

// =============================================================================
// Processing
// =============================================================================

/**
 * @brief Process lap timer (call from main loop with GPS data)
 * @param lat Current latitude
 * @param lon Current longitude
 * @param speed Current speed (m/s)
 * @param heading Current heading (degrees)
 */
void RD_LapTimer_Process(double lat, double lon, float speed, float heading);

/**
 * @brief Manual lap trigger (e.g., from external beacon)
 */
void RD_LapTimer_TriggerLap(void);

/**
 * @brief Manual sector trigger
 */
void RD_LapTimer_TriggerSector(void);

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * @brief Format lap time as string
 * @param time_ms Time in milliseconds
 * @param buffer Output buffer
 * @param buffer_size Buffer size
 * @return Formatted string length
 */
int RD_LapTimer_FormatTime(uint32_t time_ms, char *buffer, size_t buffer_size);

/**
 * @brief Format delta time as string (with +/-)
 * @param delta_ms Delta in milliseconds
 * @param buffer Output buffer
 * @param buffer_size Buffer size
 * @return Formatted string length
 */
int RD_LapTimer_FormatDelta(int32_t delta_ms, char *buffer, size_t buffer_size);

#endif // RD_LAPTIMER_H
