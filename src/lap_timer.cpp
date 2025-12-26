#include "lap_timer.h"
#include <Arduino.h>
#include <math.h>
#include <string.h>

// ============================================================================
// Constants
// ============================================================================

#define EARTH_RADIUS_M 6371000.0  // Earth radius in meters
#define DEG_TO_RAD(deg) ((deg) * M_PI / 180.0)

// ============================================================================
// Track Database
// ============================================================================

const TrackMap TRACK_SPA_FRANCORCHAMPS = {
    .track_name = "Spa-Francorchamps",
    .country = "Belgium",
    .circuit_type = "road",
    .start_finish = {50.437222, 5.971389, 15.0f, "Start/Finish"},
    .sectors = {
        {50.444444, 5.969444, 15.0f, "Sector 1"},
        {50.448889, 5.963333, 15.0f, "Sector 2"}
    },
    .sector_count = 2,
    .track_length_m = 7004.0,
    .track_record_s = 103.8f,
    .record_holder = "Lewis Hamilton",
    .is_validated = true
};

const TrackMap TRACK_NURBURGRING_GP = {
    .track_name = "Nürburgring GP",
    .country = "Germany",
    .circuit_type = "road",
    .start_finish = {50.335278, 6.943056, 15.0f, "Start/Finish"},
    .sectors = {},
    .sector_count = 0,
    .track_length_m = 5148.0,
    .track_record_s = 75.5f,
    .record_holder = "Max Verstappen",
    .is_validated = true
};

// ============================================================================
// Private Helper Functions
// ============================================================================

static float haversine_distance(double lat1, double lon1, double lat2, double lon2) {
    double dLat = DEG_TO_RAD(lat2 - lat1);
    double dLon = DEG_TO_RAD(lon2 - lon1);

    double a = sin(dLat / 2) * sin(dLat / 2) +
               cos(DEG_TO_RAD(lat1)) * cos(DEG_TO_RAD(lat2)) *
               sin(dLon / 2) * sin(dLon / 2);

    double c = 2 * atan2(sqrt(a), sqrt(1 - a));

    return EARTH_RADIUS_M * c;
}

// ============================================================================
// Public API Implementation
// ============================================================================

void lap_timer_init(LapTimer *lt) {
    if (!lt) return;

    memset(lt, 0, sizeof(LapTimer));
    lt->track_loaded = false;
    lt->auto_detection_enabled = false;
    lt->state.in_lap_now = false;
    lt->current_lap_delta_ms = 0;
}

bool lap_timer_load_track(LapTimer *lt, const TrackMap *track) {
    if (!lt || !track) return false;

    memcpy(&lt->current_track, track, sizeof(TrackMap));
    lt->track_loaded = true;

    Serial.printf("[LAP] Loaded track: %s (%.0f m)\n",
                  track->track_name, track->track_length_m);

    return true;
}

bool lap_timer_load_track_by_name(LapTimer *lt, const char *track_name) {
    if (!lt || !track_name) return false;

    if (strcmp(track_name, "Spa-Francorchamps") == 0) {
        return lap_timer_load_track(lt, &TRACK_SPA_FRANCORCHAMPS);
    } else if (strcmp(track_name, "Nürburgring") == 0 ||
               strcmp(track_name, "Nurburgring") == 0) {
        return lap_timer_load_track(lt, &TRACK_NURBURGRING_GP);
    }

    return false;
}

void lap_timer_update(LapTimer *lt, double lat, double lon,
                     float speed_kmh, uint64_t timestamp_ms) {
    if (!lt || !lt->track_loaded) return;

    lt->state.last_lat = lat;
    lt->state.last_lon = lon;
    lt->state.current_speed_kmh = speed_kmh;

    // Check for start/finish line crossing
    if (lap_timer_check_crossing(lt, lat, lon, &lt->current_track.start_finish)) {

        if (lt->state.in_lap_now) {
            // Lap completed
            uint64_t lap_time_ms = timestamp_ms - lt->state.lap_start_time_ms;

            if (lt->lap_count < MAX_LAPS) {
                LapRecord *lap = &lt->laps[lt->lap_count];
                lap->lap_number = lt->lap_count + 1;
                lap->lap_time_ms = lap_time_ms;
                lap->max_speed_kmh = lt->current_lap.max_speed_kmh;
                lap->avg_speed_kmh = (lt->current_track.track_length_m / 1000.0f) /
                                     (lap_time_ms / 3600000.0f);
                lap->start_lat = lt->current_lap.start_lat;
                lap->start_lon = lt->current_lap.start_lon;
                lap->timestamp_utc = timestamp_ms;
                lap->is_valid = true;

                // Copy sector times
                memcpy(lap->sector_times_ms, lt->current_lap.sector_times_ms,
                       sizeof(lap->sector_times_ms));

                lt->lap_count++;

                // Update best lap
                if (lt->best_lap.lap_time_ms == 0 || lap_time_ms < lt->best_lap.lap_time_ms) {
                    memcpy(&lt->best_lap, lap, sizeof(LapRecord));
                    Serial.printf("[LAP] New best lap: %02d:%02d.%03d\n",
                                 (int)(lap_time_ms / 60000),
                                 (int)((lap_time_ms / 1000) % 60),
                                 (int)(lap_time_ms % 1000));
                }

                // Save last lap
                memcpy(&lt->last_lap, lap, sizeof(LapRecord));

                Serial.printf("[LAP] Lap %u: %02d:%02d.%03d (avg %.1f km/h)\n",
                             lap->lap_number,
                             (int)(lap_time_ms / 60000),
                             (int)((lap_time_ms / 1000) % 60),
                             (int)(lap_time_ms % 1000),
                             lap->avg_speed_kmh);
            }

            // Reset for new lap
            memset(&lt->current_lap, 0, sizeof(LapRecord));
            lt->state.current_sector = 0;
            memset(lt->state.sector_triggered, 0, sizeof(lt->state.sector_triggered));
        }

        // Start new lap
        lt->state.in_lap_now = true;
        lt->state.lap_start_time_ms = timestamp_ms;
        lt->current_lap.start_lat = lat;
        lt->current_lap.start_lon = lon;
        lt->current_lap.max_speed_kmh = speed_kmh;
    }

    if (lt->state.in_lap_now) {
        // Update current lap stats
        if (speed_kmh > lt->current_lap.max_speed_kmh) {
            lt->current_lap.max_speed_kmh = speed_kmh;
        }

        // Check sector crossings
        for (size_t i = 0; i < lt->current_track.sector_count; i++) {
            if (!lt->state.sector_triggered[i] &&
                lap_timer_check_crossing(lt, lat, lon, &lt->current_track.sectors[i])) {

                lt->state.sector_triggered[i] = true;
                lt->current_lap.sector_times_ms[i] = timestamp_ms - lt->state.lap_start_time_ms;
                lt->state.current_sector = i + 1;

                // Calculate sector delta
                if (lt->best_lap.is_valid) {
                    lt->sector_delta_ms[i] = lt->current_lap.sector_times_ms[i] -
                                            lt->best_lap.sector_times_ms[i];
                }
            }
        }

        // Calculate current lap delta
        if (lt->best_lap.is_valid) {
            uint64_t current_time = timestamp_ms - lt->state.lap_start_time_ms;
            // Simple linear interpolation based on time
            float progress = (float)current_time / lt->best_lap.lap_time_ms;
            int32_t expected_time = (int32_t)(lt->best_lap.lap_time_ms * progress);
            lt->current_lap_delta_ms = (int32_t)current_time - expected_time;
        }
    }
}

bool lap_timer_check_crossing(const LapTimer *lt, double lat, double lon,
                              const GPSPoint *point) {
    if (!lt || !point) return false;

    float distance = haversine_distance(lat, lon, point->lat, point->lon);
    return distance <= point->radius_m;
}

void lap_timer_manual_start_lap(LapTimer *lt, uint64_t timestamp_ms) {
    if (!lt) return;

    lt->state.in_lap_now = true;
    lt->state.lap_start_time_ms = timestamp_ms;
    lt->state.current_sector = 0;
    memset(lt->state.sector_triggered, 0, sizeof(lt->state.sector_triggered));
}

int32_t lap_timer_get_current_delta(const LapTimer *lt) {
    return lt ? lt->current_lap_delta_ms : 0;
}

int32_t lap_timer_get_sector_delta(const LapTimer *lt, uint8_t sector) {
    if (!lt || sector >= MAX_SECTORS) return 0;
    return lt->sector_delta_ms[sector];
}

uint64_t lap_timer_get_predicted_time(const LapTimer *lt) {
    return lt ? lt->predicted_lap_time_ms : 0;
}

void lap_timer_reset(LapTimer *lt) {
    if (!lt) return;

    lt->lap_count = 0;
    memset(&lt->best_lap, 0, sizeof(LapRecord));
    memset(&lt->last_lap, 0, sizeof(LapRecord));
    memset(&lt->current_lap, 0, sizeof(LapRecord));
    memset(&lt->laps, 0, sizeof(lt->laps));
    lt->state.in_lap_now = false;
    lt->current_lap_delta_ms = 0;
    lt->total_distance_m = 0;
}

const LapRecord* lap_timer_get_best_lap(const LapTimer *lt) {
    if (!lt || lt->best_lap.lap_time_ms == 0) return NULL;
    return &lt->best_lap;
}

const LapRecord* lap_timer_get_last_lap(const LapTimer *lt) {
    if (!lt || lt->last_lap.lap_time_ms == 0) return NULL;
    return &lt->last_lap;
}

float lap_timer_calculate_distance(double lat1, double lon1, double lat2, double lon2) {
    return haversine_distance(lat1, lon1, lat2, lon2);
}

bool lap_timer_auto_detect_track(LapTimer *lt, double lat, double lon) {
    if (!lt) return false;

    // Check against known tracks
    const TrackMap *tracks[] = {
        &TRACK_SPA_FRANCORCHAMPS,
        &TRACK_NURBURGRING_GP
    };

    for (size_t i = 0; i < sizeof(tracks) / sizeof(tracks[0]); i++) {
        float dist = haversine_distance(lat, lon,
                                       tracks[i]->start_finish.lat,
                                       tracks[i]->start_finish.lon);

        if (dist < 500.0f) {  // Within 500m of start/finish
            lap_timer_load_track(lt, tracks[i]);
            Serial.printf("[LAP] Auto-detected: %s\n", tracks[i]->track_name);
            return true;
        }
    }

    return false;
}

bool lap_timer_export_to_csv(const LapTimer *lt, const char *filepath) {
    // TODO: Implement CSV export
    return false;
}

bool lap_timer_export_to_vbo(const LapTimer *lt, const char *filepath) {
    // TODO: Implement Video BBOX export
    return false;
}
