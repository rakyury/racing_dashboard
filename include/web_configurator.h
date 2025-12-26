#pragma once

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @file web_configurator.h
 * @brief Web-based Configuration Interface with REST API
 *
 * Features:
 * - WiFi Access Point mode (captive portal)
 * - WiFi Station mode (connect to existing network)
 * - RESTful API for configuration
 * - WebSocket for live telemetry streaming
 * - Single-Page Application (SPA) interface
 * - DBC file upload/download
 * - Screen layout editor
 * - Firmware OTA via web interface
 * - Session management and authentication
 */

// ============================================================================
// Constants
// ============================================================================

#define WEB_MAX_CLIENTS 4
#define WEB_MAX_SSID_LEN 32
#define WEB_MAX_PASSWORD_LEN 64
#define WEB_MAX_PATH_LEN 128
#define WEB_MAX_BODY_SIZE 4096
#define WEB_SESSION_TIMEOUT_S 3600

// ============================================================================
// Enumerations
// ============================================================================

typedef enum {
    WIFI_MODE_OFF,
    WIFI_MODE_AP,                   // Access Point
    WIFI_MODE_STA,                  // Station (client)
    WIFI_MODE_AP_STA                // Both AP and STA
} WiFiMode;

typedef enum {
    HTTP_METHOD_GET,
    HTTP_METHOD_POST,
    HTTP_METHOD_PUT,
    HTTP_METHOD_DELETE,
    HTTP_METHOD_PATCH,
    HTTP_METHOD_OPTIONS
} HTTPMethod;

typedef enum {
    HTTP_STATUS_OK = 200,
    HTTP_STATUS_CREATED = 201,
    HTTP_STATUS_NO_CONTENT = 204,
    HTTP_STATUS_BAD_REQUEST = 400,
    HTTP_STATUS_UNAUTHORIZED = 401,
    HTTP_STATUS_FORBIDDEN = 403,
    HTTP_STATUS_NOT_FOUND = 404,
    HTTP_STATUS_METHOD_NOT_ALLOWED = 405,
    HTTP_STATUS_CONFLICT = 409,
    HTTP_STATUS_INTERNAL_ERROR = 500,
    HTTP_STATUS_NOT_IMPLEMENTED = 501
} HTTPStatus;

typedef enum {
    WS_EVENT_CONNECT,
    WS_EVENT_DISCONNECT,
    WS_EVENT_MESSAGE,
    WS_EVENT_ERROR
} WebSocketEvent;

// ============================================================================
// Structures
// ============================================================================

typedef struct {
    char ssid[WEB_MAX_SSID_LEN];
    char password[WEB_MAX_PASSWORD_LEN];
    uint8_t channel;                // 1-13
    bool hidden;
    uint8_t max_connections;
} WiFiAPConfig;

typedef struct {
    char ssid[WEB_MAX_SSID_LEN];
    char password[WEB_MAX_PASSWORD_LEN];
    bool auto_reconnect;
    uint32_t timeout_ms;
} WiFiSTAConfig;

typedef struct {
    WiFiMode mode;
    WiFiAPConfig ap_config;
    WiFiSTAConfig sta_config;

    // mDNS
    char hostname[32];              // e.g., "racing-dashboard.local"
    bool enable_mdns;

    // Security
    bool enable_auth;
    char admin_username[32];
    char admin_password[64];
    char api_key[64];

    // Server
    uint16_t http_port;             // Default: 80
    uint16_t ws_port;               // Default: 81
    bool enable_cors;

    // Captive portal
    bool enable_captive_portal;
    char portal_redirect_url[WEB_MAX_PATH_LEN];
} WebConfig;

typedef struct {
    char path[WEB_MAX_PATH_LEN];
    char query[256];
    char body[WEB_MAX_BODY_SIZE];
    size_t body_length;
    HTTPMethod method;

    // Headers
    char content_type[64];
    char authorization[128];
    char session_token[64];

    // Client info
    char client_ip[16];
    uint16_t client_port;
} HTTPRequest;

typedef struct {
    HTTPStatus status;
    char content_type[64];
    char body[WEB_MAX_BODY_SIZE];
    size_t body_length;

    // Headers
    bool cors_enabled;
    char location[WEB_MAX_PATH_LEN]; // For redirects
    char set_cookie[128];
} HTTPResponse;

typedef void (*HTTPHandler)(const HTTPRequest *request, HTTPResponse *response, void *user_data);

typedef struct {
    char path[WEB_MAX_PATH_LEN];
    HTTPMethod method;
    HTTPHandler handler;
    void *user_data;
    bool require_auth;
} HTTPRoute;

typedef struct {
    uint32_t client_id;
    char session_token[64];
    uint64_t created_at_ms;
    uint64_t last_activity_ms;
    bool is_authenticated;
    char username[32];
} WebSession;

typedef struct {
    uint32_t client_id;
    char ip_address[16];
    bool is_connected;
    uint64_t connect_time_ms;
    uint32_t messages_sent;
    uint32_t messages_received;
} WebSocketClient;

typedef struct {
    WebConfig config;

    // WiFi state
    bool wifi_connected;
    char ip_address[16];
    int8_t rssi_dbm;                // Signal strength

    // HTTP server
    void *http_server;              // Platform-specific server handle
    HTTPRoute routes[32];
    size_t route_count;

    // WebSocket server
    void *ws_server;
    WebSocketClient ws_clients[WEB_MAX_CLIENTS];
    size_t ws_client_count;

    // Sessions
    WebSession sessions[WEB_MAX_CLIENTS];
    size_t session_count;

    // Statistics
    uint32_t total_requests;
    uint32_t total_errors;
    uint64_t bytes_sent;
    uint64_t bytes_received;
} WebConfigurator;

// ============================================================================
// Public API - Core Functions
// ============================================================================

/**
 * @brief Initialize web configurator
 * @param web Web configurator instance
 * @param config Configuration parameters
 * @return true if successfully initialized
 */
bool web_configurator_init(WebConfigurator *web, const WebConfig *config);

/**
 * @brief Start web server
 * @param web Web configurator instance
 * @return true if server started
 */
bool web_configurator_start(WebConfigurator *web);

/**
 * @brief Stop web server
 * @param web Web configurator instance
 */
void web_configurator_stop(WebConfigurator *web);

/**
 * @brief Update configurator (call from main loop)
 * @param web Web configurator instance
 */
void web_configurator_update(WebConfigurator *web);

/**
 * @brief Get WiFi status
 * @param web Web configurator instance
 * @return true if WiFi connected
 */
bool web_configurator_is_connected(const WebConfigurator *web);

/**
 * @brief Get IP address
 * @param web Web configurator instance
 * @return IP address string (empty if not connected)
 */
const char* web_configurator_get_ip(const WebConfigurator *web);

// ============================================================================
// Public API - HTTP Routing
// ============================================================================

/**
 * @brief Register HTTP route
 * @param web Web configurator instance
 * @param path URL path (e.g., "/api/config")
 * @param method HTTP method
 * @param handler Request handler function
 * @param user_data User data passed to handler
 * @param require_auth Require authentication
 * @return true if route registered
 */
bool web_register_route(WebConfigurator *web, const char *path, HTTPMethod method,
                        HTTPHandler handler, void *user_data, bool require_auth);

/**
 * @brief Send HTTP response
 * @param response Response object
 * @param status HTTP status code
 * @param content_type Content-Type header
 * @param body Response body
 */
void web_send_response(HTTPResponse *response, HTTPStatus status,
                       const char *content_type, const char *body);

/**
 * @brief Send JSON response
 * @param response Response object
 * @param status HTTP status code
 * @param json_body JSON string
 */
void web_send_json(HTTPResponse *response, HTTPStatus status, const char *json_body);

/**
 * @brief Send file response
 * @param response Response object
 * @param filepath Path to file
 * @return true if file sent successfully
 */
bool web_send_file(HTTPResponse *response, const char *filepath);

/**
 * @brief Send error response
 * @param response Response object
 * @param status HTTP status code
 * @param error_message Error message
 */
void web_send_error(HTTPResponse *response, HTTPStatus status, const char *error_message);

// ============================================================================
// Public API - WebSocket
// ============================================================================

/**
 * @brief Broadcast message to all WebSocket clients
 * @param web Web configurator instance
 * @param message Message string
 */
void web_ws_broadcast(WebConfigurator *web, const char *message);

/**
 * @brief Send message to specific WebSocket client
 * @param web Web configurator instance
 * @param client_id Client identifier
 * @param message Message string
 * @return true if sent successfully
 */
bool web_ws_send(WebConfigurator *web, uint32_t client_id, const char *message);

/**
 * @brief Get number of connected WebSocket clients
 * @param web Web configurator instance
 * @return Client count
 */
size_t web_ws_get_client_count(const WebConfigurator *web);

// ============================================================================
// Public API - Session Management
// ============================================================================

/**
 * @brief Create new session
 * @param web Web configurator instance
 * @param username Username
 * @return Session token (empty on failure)
 */
const char* web_session_create(WebConfigurator *web, const char *username);

/**
 * @brief Validate session token
 * @param web Web configurator instance
 * @param token Session token
 * @return true if session is valid
 */
bool web_session_validate(WebConfigurator *web, const char *token);

/**
 * @brief Destroy session
 * @param web Web configurator instance
 * @param token Session token
 */
void web_session_destroy(WebConfigurator *web, const char *token);

/**
 * @brief Update session activity
 * @param web Web configurator instance
 * @param token Session token
 */
void web_session_update_activity(WebConfigurator *web, const char *token);

/**
 * @brief Clean up expired sessions
 * @param web Web configurator instance
 * @return Number of sessions removed
 */
size_t web_session_cleanup_expired(WebConfigurator *web);

// ============================================================================
// Public API - Authentication
// ============================================================================

/**
 * @brief Authenticate user
 * @param web Web configurator instance
 * @param username Username
 * @param password Password
 * @return true if authentication successful
 */
bool web_auth_verify_credentials(const WebConfigurator *web,
                                 const char *username, const char *password);

/**
 * @brief Verify API key
 * @param web Web configurator instance
 * @param api_key API key to verify
 * @return true if API key is valid
 */
bool web_auth_verify_api_key(const WebConfigurator *web, const char *api_key);

/**
 * @brief Generate session token
 * @param token Output buffer (64 bytes)
 */
void web_auth_generate_token(char *token);

// ============================================================================
// Public API - WiFi Management
// ============================================================================

/**
 * @brief Start WiFi Access Point
 * @param web Web configurator instance
 * @param ssid AP SSID
 * @param password AP password (NULL for open network)
 * @return true if AP started
 */
bool web_wifi_start_ap(WebConfigurator *web, const char *ssid, const char *password);

/**
 * @brief Connect to WiFi network
 * @param web Web configurator instance
 * @param ssid Network SSID
 * @param password Network password
 * @return true if connected
 */
bool web_wifi_connect_sta(WebConfigurator *web, const char *ssid, const char *password);

/**
 * @brief Disconnect WiFi
 * @param web Web configurator instance
 */
void web_wifi_disconnect(WebConfigurator *web);

/**
 * @brief Scan for WiFi networks
 * @param networks Output buffer for network list
 * @param max_networks Maximum networks to return
 * @return Number of networks found
 */
size_t web_wifi_scan_networks(char networks[][WEB_MAX_SSID_LEN], size_t max_networks);

/**
 * @brief Get WiFi signal strength
 * @param web Web configurator instance
 * @return RSSI in dBm
 */
int8_t web_wifi_get_rssi(const WebConfigurator *web);

// ============================================================================
// Public API - Utilities
// ============================================================================

/**
 * @brief Parse JSON from request body
 * @param request HTTP request
 * @param key JSON key to extract
 * @param value Output buffer for value
 * @param value_size Output buffer size
 * @return true if key found
 */
bool web_json_get_string(const HTTPRequest *request, const char *key,
                         char *value, size_t value_size);

/**
 * @brief Get JSON integer value
 * @param request HTTP request
 * @param key JSON key
 * @param value Output integer value
 * @return true if key found
 */
bool web_json_get_int(const HTTPRequest *request, const char *key, int *value);

/**
 * @brief Get JSON boolean value
 * @param request HTTP request
 * @param key JSON key
 * @param value Output boolean value
 * @return true if key found
 */
bool web_json_get_bool(const HTTPRequest *request, const char *key, bool *value);

/**
 * @brief Build JSON response
 * @param buffer Output buffer
 * @param buffer_size Buffer size
 * @param format Format string (key:value pairs)
 * @param ... Variable arguments
 * @return Number of bytes written
 */
size_t web_json_build(char *buffer, size_t buffer_size, const char *format, ...);

/**
 * @brief URL decode string
 * @param encoded Encoded string
 * @param decoded Output buffer
 * @param decoded_size Output buffer size
 */
void web_url_decode(const char *encoded, char *decoded, size_t decoded_size);

/**
 * @brief URL encode string
 * @param decoded Plain string
 * @param encoded Output buffer
 * @param encoded_size Output buffer size
 */
void web_url_encode(const char *decoded, char *encoded, size_t encoded_size);

/**
 * @brief Get HTTP method string
 * @param method HTTP method
 * @return Method name
 */
const char* web_http_method_to_string(HTTPMethod method);

/**
 * @brief Get HTTP status string
 * @param status HTTP status code
 * @return Status description
 */
const char* web_http_status_to_string(HTTPStatus status);

#ifdef __cplusplus
}
#endif
