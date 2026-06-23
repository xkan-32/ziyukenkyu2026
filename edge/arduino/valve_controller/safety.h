#ifndef SAFETY_H
#define SAFETY_H

#include "config.h"
#include "sensor.h"
#include "valve.h"

// wet 判定時は水やりを拒否
inline bool isSafeToWater(float moisturePercent) {
  return moisturePercent < WET_THRESHOLD_PERCENT;
}

// 要求時間が最大開放時間を超えないよう制限
inline unsigned long clampDuration(unsigned long durationMs) {
  if (durationMs > MAX_VALVE_OPEN_MS) {
    return MAX_VALVE_OPEN_MS;
  }
  return durationMs;
}

#endif
