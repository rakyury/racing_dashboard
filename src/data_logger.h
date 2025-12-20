#pragma once

#include <stddef.h>

#define LOGGER_LINES 256
#define LOGGER_LINE_LEN 128

typedef struct {
    char lines[LOGGER_LINES][LOGGER_LINE_LEN];
    size_t count;
} DataLogger;

void data_logger_init(DataLogger *logger);
void data_logger_record(DataLogger *logger, const char *text);
void data_logger_flush(const DataLogger *logger);

