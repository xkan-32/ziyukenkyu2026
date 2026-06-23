#ifndef VALVE_H
#define VALVE_H

#include "config.h"

inline uint8_t valveOnLevel() {
  return VALVE_ACTIVE_HIGH ? HIGH : LOW;
}

inline uint8_t valveOffLevel() {
  return VALVE_ACTIVE_HIGH ? LOW : HIGH;
}

inline void beginValvePins() {
  pinMode(VALVE_PIN, OUTPUT);
  pinMode(TEST_LED_PIN, OUTPUT);
}

inline void closeValveHardware() {
  digitalWrite(VALVE_PIN, valveOffLevel());
  digitalWrite(TEST_LED_PIN, LOW);
}

inline void openValveHardware(bool dryRun) {
  if (dryRun) {
    digitalWrite(TEST_LED_PIN, HIGH);
    digitalWrite(VALVE_PIN, valveOffLevel());
    return;
  }

  digitalWrite(TEST_LED_PIN, LOW);
  digitalWrite(VALVE_PIN, valveOnLevel());
}

#endif
