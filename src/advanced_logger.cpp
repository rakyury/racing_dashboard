#include "advanced_logger.h"
#include <Arduino.h>
#include <SD.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>

// ============================================================================
// Private Helper Functions
// ============================================================================

static bool create_log_directory(const char *path) {
    // Extract directory from path
    char dir[MAX_LOG_FILENAME];
    strncpy(dir, path, sizeof(dir) - 1);

    char *last_slash = strrchr(dir, '/');
    if (last_slash) {
        *last_slash = '\0';
        return SD.mkdir(dir);
    }
    return true;
}

static void generate_filename(AdvancedLogger *logger, char *output, size_t size) {
    const char *ext = ".bin";
    if (logger->config.format == LOG_FORMAT_CSV) ext = ".csv";
    else if (logger->config.format == LOG_FORMAT_COMPRESSED_ZLIB) ext = ".bin.gz";
    else if (logger->config.format == LOG_FORMAT_PARQUET) ext = ".parquet";

    snprintf(output, size, "%s_%lu%s",
             logger->config.output_path,
             logger->config.rotation.file_counter++,
             ext);
}

// ============================================================================
// Ring Buffer Management
// ============================================================================

static bool ring_buffer_init(RingBuffer *rb, size_t capacity) {
    rb->samples = (LogSample*)malloc(capacity * sizeof(LogSample));
    if (!rb->samples) return false;

    rb->capacity = capacity;
    rb->count = 0;
    rb->write_index = 0;
    rb->read_index = 0;
    rb->is_full = false;
    return true;
}

static void ring_buffer_free(RingBuffer *rb) {
    if (rb->samples) {
        free(rb->samples);
        rb->samples = NULL;
    }
}

static bool ring_buffer_push(RingBuffer *rb, const LogSample *sample) {
    memcpy(&rb->samples[rb->write_index], sample, sizeof(LogSample));

    rb->write_index = (rb->write_index + 1) % rb->capacity;

    if (rb->is_full) {
        rb->read_index = (rb->read_index + 1) % rb->capacity;
    } else {
        rb->count++;
        if (rb->count == rb->capacity) {
            rb->is_full = true;
        }
    }

    return true;
}

// ============================================================================
// Public API Implementation
// ============================================================================

bool advanced_logger_init(AdvancedLogger *logger, const AdvancedLogConfig *config) {
    if (!logger || !config) return false;

    memset(logger, 0, sizeof(AdvancedLogger));
    memcpy(&logger->config, config, sizeof(AdvancedLogConfig));

    logger->state = LOG_STATE_STOPPED;

    // Initialize ring buffer for pre-trigger
    if (config->trigger.pre_trigger_duration_ms > 0) {
        size_t pre_trigger_samples =
            (config->trigger.pre_trigger_duration_ms * config->default_sample_rate_hz) / 1000;

        if (!ring_buffer_init(&logger->ring_buffer, pre_trigger_samples)) {
            strncpy(logger->last_error, "Failed to allocate ring buffer", sizeof(logger->last_error));
            return false;
        }
    }

    // Allocate write buffer
    logger->write_buffer = (uint8_t*)malloc(config->buffer_size_kb * 1024);
    if (!logger->write_buffer) {
        ring_buffer_free(&logger->ring_buffer);
        strncpy(logger->last_error, "Failed to allocate write buffer", sizeof(logger->last_error));
        return false;
    }

    logger->write_buffer_used = 0;

    return true;
}

void advanced_logger_deinit(AdvancedLogger *logger) {
    if (!logger) return;

    if (logger->state == LOG_STATE_RECORDING) {
        advanced_logger_stop(logger);
    }

    ring_buffer_free(&logger->ring_buffer);

    if (logger->write_buffer) {
        free(logger->write_buffer);
        logger->write_buffer = NULL;
    }
}

bool advanced_logger_start(AdvancedLogger *logger, const char *session_name) {
    if (!logger || logger->state == LOG_STATE_RECORDING) return false;

    // Generate filename
    char filepath[MAX_LOG_FILENAME];
    generate_filename(logger, filepath, sizeof(filepath));

    // Create directory if needed
    create_log_directory(filepath);

    // Open file
    File file = SD.open(filepath, FILE_WRITE);
    if (!file) {
        snprintf(logger->last_error, sizeof(logger->last_error),
                "Failed to open file: %s", filepath);
        logger->state = LOG_STATE_ERROR;
        return false;
    }

    logger->file_handle = new File(file);
    logger->state = LOG_STATE_RECORDING;
    logger->session_start_time_ms = millis();
    logger->recording_start_time_ms = millis();
    logger->total_samples_written = 0;
    logger->current_file_size_bytes = 0;

    // Write CSV header if needed
    if (logger->config.format == LOG_FORMAT_CSV) {
        file.println("timestamp_ms,channel,value,is_digital");
    }

    Serial.printf("[LOGGER] Started: %s\n", filepath);
    return true;
}

bool advanced_logger_stop(AdvancedLogger *logger) {
    if (!logger || logger->state != LOG_STATE_RECORDING) return false;

    // Flush remaining data
    advanced_logger_flush(logger);

    // Close file
    if (logger->file_handle) {
        File *file = (File*)logger->file_handle;
        file->close();
        delete file;
        logger->file_handle = NULL;
    }

    logger->state = LOG_STATE_STOPPED;

    uint64_t duration_s = (millis() - logger->session_start_time_ms) / 1000;
    Serial.printf("[LOGGER] Stopped. Duration: %llu s, Samples: %u\n",
                  duration_s, logger->total_samples_written);

    return true;
}

void advanced_logger_pause(AdvancedLogger *logger) {
    if (logger && logger->state == LOG_STATE_RECORDING) {
        logger->state = LOG_STATE_PAUSED;
    }
}

void advanced_logger_resume(AdvancedLogger *logger) {
    if (logger && logger->state == LOG_STATE_PAUSED) {
        logger->state = LOG_STATE_RECORDING;
    }
}

bool advanced_logger_log_sample(AdvancedLogger *logger, const char *channel,
                                float value, uint64_t timestamp_ms, bool is_digital) {
    if (!logger || !channel) return false;

    // Check if channel is in whitelist
    if (logger->config.use_whitelist) {
        bool found = false;
        for (size_t i = 0; i < logger->config.channel_count; i++) {
            if (strcmp(logger->config.channels[i].channel_name, channel) == 0 &&
                logger->config.channels[i].enabled) {
                found = true;
                break;
            }
        }
        if (!found) return false;
    }

    // Create sample
    LogSample sample;
    sample.timestamp_ms = timestamp_ms;
    sample.gps_timestamp_utc = 0; // TODO: sync with GPS
    sample.sample_number = logger->total_samples_written;
    strncpy(sample.channel_name, channel, sizeof(sample.channel_name) - 1);
    sample.value = value;
    sample.is_digital = is_digital;

    // Handle pre-trigger buffer
    if (logger->state == LOG_STATE_ARMED || logger->state == LOG_STATE_PRE_TRIGGER) {
        ring_buffer_push(&logger->ring_buffer, &sample);

        // Check trigger condition
        if (logger->config.trigger.mode == TRIGGER_MODE_THRESHOLD &&
            strcmp(channel, logger->config.trigger.channel_name) == 0) {

            bool triggered = logger->config.trigger.threshold_rising ?
                            (value > logger->config.trigger.threshold_value) :
                            (value < logger->config.trigger.threshold_value);

            if (triggered && !logger->config.trigger.is_triggered) {
                logger->config.trigger.is_triggered = true;
                advanced_logger_start(logger, NULL);

                // Flush pre-trigger buffer
                // TODO: Write ring buffer contents to file
            }
        }
        return true;
    }

    if (logger->state != LOG_STATE_RECORDING) return false;

    // Write to buffer
    if (logger->config.format == LOG_FORMAT_CSV) {
        char line[256];
        snprintf(line, sizeof(line), "%llu,%s,%.6f,%d\n",
                timestamp_ms, channel, value, is_digital ? 1 : 0);

        size_t len = strlen(line);
        if (logger->write_buffer_used + len < logger->config.buffer_size_kb * 1024) {
            memcpy(logger->write_buffer + logger->write_buffer_used, line, len);
            logger->write_buffer_used += len;
        }
    } else {
        // Binary format
        if (logger->write_buffer_used + sizeof(LogSample) < logger->config.buffer_size_kb * 1024) {
            memcpy(logger->write_buffer + logger->write_buffer_used, &sample, sizeof(LogSample));
            logger->write_buffer_used += sizeof(LogSample);
        }
    }

    logger->total_samples_written++;

    // Auto flush if buffer full
    if (logger->write_buffer_used >= (logger->config.buffer_size_kb * 1024) * 0.8) {
        advanced_logger_flush(logger);
    }

    return true;
}

size_t advanced_logger_log_from_bus(AdvancedLogger *logger, const SignalBus *bus,
                                    uint64_t timestamp_ms) {
    // TODO: Implement when SignalBus is available
    return 0;
}

bool advanced_logger_flush(AdvancedLogger *logger) {
    if (!logger || !logger->file_handle || logger->write_buffer_used == 0) {
        return false;
    }

    File *file = (File*)logger->file_handle;

    size_t written = file->write(logger->write_buffer, logger->write_buffer_used);

    if (written == logger->write_buffer_used) {
        logger->current_file_size_bytes += written;
        logger->total_bytes_written += written;
        logger->write_buffer_used = 0;

        file->flush();
        return true;
    }

    return false;
}

bool advanced_logger_add_channel(AdvancedLogger *logger, const char *channel_name,
                                 float sample_rate_hz) {
    if (!logger || !channel_name || logger->config.channel_count >= MAX_LOG_CHANNELS) {
        return false;
    }

    LogChannel *ch = &logger->config.channels[logger->config.channel_count++];
    strncpy(ch->channel_name, channel_name, sizeof(ch->channel_name) - 1);
    ch->enabled = true;
    ch->sample_rate_hz = (sample_rate_hz > 0) ? sample_rate_hz : logger->config.default_sample_rate_hz;
    ch->last_value = 0;
    ch->last_sample_time_ms = 0;

    return true;
}

bool advanced_logger_set_trigger(AdvancedLogger *logger, TriggerMode mode,
                                 const char *channel, float threshold,
                                 bool rising, uint32_t pre_trigger_ms) {
    if (!logger) return false;

    logger->config.trigger.mode = mode;
    if (channel) {
        strncpy(logger->config.trigger.channel_name, channel,
                sizeof(logger->config.trigger.channel_name) - 1);
    }
    logger->config.trigger.threshold_value = threshold;
    logger->config.trigger.threshold_rising = rising;
    logger->config.trigger.pre_trigger_duration_ms = pre_trigger_ms;
    logger->config.trigger.is_armed = false;
    logger->config.trigger.is_triggered = false;

    return true;
}

void advanced_logger_arm_trigger(AdvancedLogger *logger) {
    if (logger) {
        logger->state = LOG_STATE_ARMED;
        logger->config.trigger.is_armed = true;
        logger->config.trigger.is_triggered = false;
    }
}

void advanced_logger_manual_trigger(AdvancedLogger *logger) {
    if (logger && logger->config.trigger.mode == TRIGGER_MODE_MANUAL) {
        logger->config.trigger.is_triggered = true;
        advanced_logger_start(logger, NULL);
    }
}

LogState advanced_logger_get_state(const AdvancedLogger *logger) {
    return logger ? logger->state : LOG_STATE_ERROR;
}

float advanced_logger_get_compression_ratio(const AdvancedLogger *logger) {
    return logger ? logger->compression_ratio : 0.0f;
}

float advanced_logger_get_throughput(const AdvancedLogger *logger) {
    return logger ? logger->write_throughput_kbps : 0.0f;
}

uint32_t advanced_logger_get_sample_count(const AdvancedLogger *logger) {
    return logger ? logger->total_samples_written : 0;
}

uint64_t advanced_logger_get_session_duration(const AdvancedLogger *logger) {
    if (!logger || logger->session_start_time_ms == 0) return 0;
    return millis() - logger->session_start_time_ms;
}

const char* advanced_logger_get_last_error(const AdvancedLogger *logger) {
    return logger ? logger->last_error : "";
}

void advanced_logger_clear_error(AdvancedLogger *logger) {
    if (logger) {
        logger->last_error[0] = '\0';
        logger->error_count = 0;
    }
}

bool advanced_logger_export_to_csv(const char *binary_path, const char *csv_path) {
    File in_file = SD.open(binary_path, FILE_READ);
    if (!in_file) return false;

    File out_file = SD.open(csv_path, FILE_WRITE);
    if (!out_file) {
        in_file.close();
        return false;
    }

    // Write CSV header
    out_file.println("timestamp_ms,channel,value,is_digital");

    // Read and convert binary samples
    LogSample sample;
    while (in_file.read((uint8_t*)&sample, sizeof(LogSample)) == sizeof(LogSample)) {
        out_file.printf("%llu,%s,%.6f,%d\n",
                       sample.timestamp_ms,
                       sample.channel_name,
                       sample.value,
                       sample.is_digital ? 1 : 0);
    }

    in_file.close();
    out_file.close();

    return true;
}
