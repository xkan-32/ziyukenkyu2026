#ifndef SENSOR_H
#define SENSOR_H

#include "config.h"

struct SoilReading {
  int raw;
  float percent;
  bool isWet;
};

inline float clampPercent(float value) {
  if (value < 0.0f) {
    return 0.0f;
  }
  if (value > 100.0f) {
    return 100.0f;
  }
  return value;
}

inline float convertRawToPercent(int raw) {
  const long span = static_cast<long>(SOIL_SENSOR_DRY_RAW) - static_cast<long>(SOIL_SENSOR_WET_RAW);
  if (span == 0) {
    return 0.0f;
  }

  const float percent =
      (static_cast<float>(SOIL_SENSOR_DRY_RAW - raw) * 100.0f) / static_cast<float>(span);
  return clampPercent(percent);
}

inline SoilReading readSoilReading() {
  const size_t samples = SENSOR_READ_SAMPLES == 0 ? 1 : SENSOR_READ_SAMPLES;
  unsigned long totalRaw = 0;

  for (size_t i = 0; i < samples; ++i) {
    totalRaw += static_cast<unsigned long>(analogRead(SOIL_MOISTURE_PIN));
    if (i + 1 < samples) {
      delay(SENSOR_READ_INTERVAL_MS);
    }
  }

  SoilReading reading;
  reading.raw = static_cast<int>(totalRaw / samples);
  reading.percent = convertRawToPercent(reading.raw);
  reading.isWet = reading.percent >= WET_REJECT_PERCENT;
  return reading;
}

#endif
