#ifndef SAFETY_H
#define SAFETY_H

#include "config.h"

inline unsigned long clampSingleDuration(unsigned long requestedDurationMs) {
  if (requestedDurationMs > MAX_SINGLE_WATER_MS) {
    return MAX_SINGLE_WATER_MS;
  }
  return requestedDurationMs;
}

inline bool wouldExceedDailyLimit(unsigned long currentDailyMs, unsigned long additionalMs) {
  if (currentDailyMs >= MAX_DAILY_WATER_MS) {
    return true;
  }
  return additionalMs > (MAX_DAILY_WATER_MS - currentDailyMs);
}

#endif
