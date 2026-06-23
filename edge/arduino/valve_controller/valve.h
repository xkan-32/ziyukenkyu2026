#ifndef VALVE_H
#define VALVE_H

#include "config.h"

inline void closeValve() {
  digitalWrite(VALVE_PIN, LOW);
}

inline void openValve() {
  digitalWrite(VALVE_PIN, HIGH);
}

#endif
