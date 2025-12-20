#include "data_logger.h"

#include <stdio.h>
#include <string.h>

void data_logger_init(DataLogger *logger) { logger->count = 0; }

void data_logger_record(DataLogger *logger, const char *text) {
    if (logger->count >= LOGGER_LINES) return;
    strncpy(logger->lines[logger->count], text, LOGGER_LINE_LEN - 1);
    logger->lines[logger->count][LOGGER_LINE_LEN - 1] = '\0';
    logger->count++;
}

void data_logger_flush(const DataLogger *logger) {
    for (size_t i = 0; i < logger->count; ++i) {
        printf("[LOG] %s\n", logger->lines[i]);
    }
}

