#pragma once

#include <chrono>
#include <deque>
#include <string>

namespace firmware {

struct LogEntry {
    std::chrono::steady_clock::time_point timestamp;
    std::string message;
};

class DataLogger {
  public:
    explicit DataLogger(size_t max_entries = 256);
    void record(std::string msg);
    void flush() const;

  private:
    size_t max_entries_;
    std::deque<LogEntry> entries_{};
};

} // namespace firmware
