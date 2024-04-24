#pragma once
#include <cstdint>

/// @brief Simple timer for recurring work
class Timer {
public:
  /// @brief Create a timer class
  /// @param interval Interval in ms at which the @ref trigger function will
  /// return true
  Timer(const uint32_t &interval) : m_interval(interval) {}

  /// @brief Check if the timer is triggered
  /// @param ms Current time in ms
  /// @return True if timer is triggered, false if not
  bool trigger(const uint32_t ms) {
    if (ms >= m_nextTrigger) {
      m_nextTrigger = ms + m_interval;
      return true;
    }
    return false;
  }

private:
  uint32_t m_interval;
  uint32_t m_nextTrigger = 0;
};