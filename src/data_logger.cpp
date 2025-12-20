#include "data_logger.h"

#include <iostream>

namespace firmware {

DataLogger::DataLogger(size_t max_entries) : max_entries_(max_entries) {}

void DataLogger::record(std::string msg) {
    if (entries_.size() >= max_entries_) entries_.pop_front();
    entries_.push_back({std::chrono::steady_clock::now(), std::move(msg)});
}

void DataLogger::flush() const {
    for (const auto &e : entries_) {
        std::cout << "[LOG] " << e.message << "\n";
    }
}

} // namespace firmware
