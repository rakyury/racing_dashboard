/**
 * @file rd_gps.h
 * @brief Racing Dashboard - GPS Module Interface
 */

#ifndef RD_GPS_H
#define RD_GPS_H

#include "rd_types.h"

// =============================================================================
// GPS Configuration
// =============================================================================

// GPS receiver types
typedef enum {
    RD_GPS_TYPE_UBLOX = 0,              // u-blox receivers (NEO-M8, NEO-M9, etc.)
    RD_GPS_TYPE_NMEA,                   // Generic NMEA receiver
    RD_GPS_TYPE_MTK,                    // MediaTek GPS
} RD_GPS_Type_t;

// GPS update rate
typedef enum {
    RD_GPS_RATE_1HZ = 1,
    RD_GPS_RATE_5HZ = 5,
    RD_GPS_RATE_10HZ = 10,
    RD_GPS_RATE_20HZ = 20,
    RD_GPS_RATE_25HZ = 25,              // u-blox max with RTK
} RD_GPS_Rate_t;

// GPS fix type
typedef enum {
    RD_GPS_FIX_NONE = 0,
    RD_GPS_FIX_2D,
    RD_GPS_FIX_3D,
    RD_GPS_FIX_DGPS,
    RD_GPS_FIX_RTK_FLOAT,
    RD_GPS_FIX_RTK_FIXED,
} RD_GPS_FixType_t;

// =============================================================================
// GPS Data Structures
// =============================================================================

/**
 * @brief GPS configuration
 */
typedef struct {
    RD_GPS_Type_t type;                 // GPS receiver type
    RD_GPS_Rate_t update_rate;          // Update rate
    uint32_t baudrate;                  // UART baudrate
    uint8_t uart_num;                   // UART port number
    bool enable_sbas;                   // Enable SBAS
    bool enable_galileo;                // Enable Galileo (Europe)
    bool enable_glonass;                // Enable GLONASS (Russia)
    bool enable_beidou;                 // Enable BeiDou (China)
} RD_GPS_Config_t;

/**
 * @brief GPS position data
 */
typedef struct {
    double latitude;                    // Latitude in degrees
    double longitude;                   // Longitude in degrees
    float altitude;                     // Altitude in meters (MSL)
    float geoid_height;                 // Geoid separation in meters
} RD_GPS_Position_t;

/**
 * @brief GPS velocity data
 */
typedef struct {
    float speed;                        // Ground speed in m/s
    float heading;                      // True heading in degrees
    float climb_rate;                   // Vertical velocity in m/s
} RD_GPS_Velocity_t;

/**
 * @brief GPS accuracy data
 */
typedef struct {
    float hdop;                         // Horizontal DOP
    float vdop;                         // Vertical DOP
    float pdop;                         // Position DOP
    float h_accuracy;                   // Horizontal accuracy in meters
    float v_accuracy;                   // Vertical accuracy in meters
    float speed_accuracy;               // Speed accuracy in m/s
    float heading_accuracy;             // Heading accuracy in degrees
} RD_GPS_Accuracy_t;

/**
 * @brief GPS time data
 */
typedef struct {
    uint16_t year;
    uint8_t month;
    uint8_t day;
    uint8_t hour;
    uint8_t minute;
    uint8_t second;
    uint16_t millisecond;
    bool valid;
} RD_GPS_Time_t;

/**
 * @brief Complete GPS data
 */
typedef struct {
    RD_GPS_Position_t position;
    RD_GPS_Velocity_t velocity;
    RD_GPS_Accuracy_t accuracy;
    RD_GPS_Time_t time;
    RD_GPS_FixType_t fix_type;
    uint8_t satellites;
    uint8_t satellites_used;
    bool fix_valid;
    uint32_t update_count;
    uint32_t timestamp;                 // System timestamp of last update
} RD_GPS_Data_t;

/**
 * @brief GPS status
 */
typedef struct {
    bool initialized;
    bool connected;
    RD_GPS_FixType_t fix_type;
    uint8_t satellites;
    uint32_t messages_received;
    uint32_t parse_errors;
    uint32_t last_fix_time;
} RD_GPS_Status_t;

// =============================================================================
// GPS Callback
// =============================================================================

/**
 * @brief GPS data update callback
 */
typedef void (*RD_GPS_Callback_t)(const RD_GPS_Data_t *data, void *user_data);

// =============================================================================
// Public API
// =============================================================================

/**
 * @brief Initialize GPS module
 * @param config GPS configuration
 * @return RD_OK on success
 */
RD_Error_t RD_GPS_Init(const RD_GPS_Config_t *config);

/**
 * @brief Deinitialize GPS module
 */
void RD_GPS_Deinit(void);

/**
 * @brief Get current GPS data
 * @param data Output GPS data
 * @return RD_OK on success
 */
RD_Error_t RD_GPS_GetData(RD_GPS_Data_t *data);

/**
 * @brief Get GPS position
 * @param position Output position
 * @return RD_OK on success
 */
RD_Error_t RD_GPS_GetPosition(RD_GPS_Position_t *position);

/**
 * @brief Get GPS velocity
 * @param velocity Output velocity
 * @return RD_OK on success
 */
RD_Error_t RD_GPS_GetVelocity(RD_GPS_Velocity_t *velocity);

/**
 * @brief Get current GPS fix type
 * @return Fix type
 */
RD_GPS_FixType_t RD_GPS_GetFixType(void);

/**
 * @brief Get number of satellites used
 * @return Number of satellites
 */
uint8_t RD_GPS_GetSatellites(void);

/**
 * @brief Check if GPS has valid fix
 * @return true if fix is valid
 */
bool RD_GPS_HasFix(void);

/**
 * @brief Get GPS speed in m/s
 * @return Speed in m/s
 */
float RD_GPS_GetSpeed(void);

/**
 * @brief Get GPS speed in km/h
 * @return Speed in km/h
 */
float RD_GPS_GetSpeedKMH(void);

/**
 * @brief Get GPS heading
 * @return Heading in degrees (0-360)
 */
float RD_GPS_GetHeading(void);

/**
 * @brief Get GPS status
 * @param status Output status
 * @return RD_OK on success
 */
RD_Error_t RD_GPS_GetStatus(RD_GPS_Status_t *status);

/**
 * @brief Register data update callback
 * @param callback Callback function
 * @param user_data User data
 * @return RD_OK on success
 */
RD_Error_t RD_GPS_RegisterCallback(RD_GPS_Callback_t callback, void *user_data);

/**
 * @brief Set GPS update rate
 * @param rate Update rate
 * @return RD_OK on success
 */
RD_Error_t RD_GPS_SetUpdateRate(RD_GPS_Rate_t rate);

/**
 * @brief Send cold start command
 * @return RD_OK on success
 */
RD_Error_t RD_GPS_ColdStart(void);

/**
 * @brief Send warm start command
 * @return RD_OK on success
 */
RD_Error_t RD_GPS_WarmStart(void);

/**
 * @brief Send hot start command
 * @return RD_OK on success
 */
RD_Error_t RD_GPS_HotStart(void);

/**
 * @brief Process GPS data (call from task/main loop)
 */
void RD_GPS_Process(void);

// =============================================================================
// Distance and Geometry Helpers
// =============================================================================

/**
 * @brief Calculate distance between two GPS points (Haversine)
 * @param lat1 Latitude of point 1
 * @param lon1 Longitude of point 1
 * @param lat2 Latitude of point 2
 * @param lon2 Longitude of point 2
 * @return Distance in meters
 */
float RD_GPS_Distance(double lat1, double lon1, double lat2, double lon2);

/**
 * @brief Calculate bearing between two GPS points
 * @param lat1 Latitude of point 1
 * @param lon1 Longitude of point 1
 * @param lat2 Latitude of point 2
 * @param lon2 Longitude of point 2
 * @return Bearing in degrees (0-360)
 */
float RD_GPS_Bearing(double lat1, double lon1, double lat2, double lon2);

/**
 * @brief Check if point is inside polygon
 * @param lat Latitude
 * @param lon Longitude
 * @param polygon Array of polygon vertices (lat, lon pairs)
 * @param num_vertices Number of vertices
 * @return true if inside polygon
 */
bool RD_GPS_PointInPolygon(double lat, double lon,
                           const double *polygon, uint8_t num_vertices);

#endif // RD_GPS_H
