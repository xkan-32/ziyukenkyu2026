#ifndef SENSOR_H
#define SENSOR_H

#include "config.h"

// 土壌水分センサー読み取り（プレースホルダー — 校正後に換算式を実装）
inline float readSoilMoisturePercent() {
  int raw = analogRead(SOIL_MOISTURE_PIN);
  // TODO: 校正値に基づく換算
  float percent = map(raw, 0, 1023, 0, 100);
  return percent;
}

#endif
