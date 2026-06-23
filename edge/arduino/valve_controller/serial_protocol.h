#ifndef SERIAL_PROTOCOL_H
#define SERIAL_PROTOCOL_H

#include <Arduino.h>
#include <limits.h>
#include <ctype.h>

inline bool parsePositiveDurationMs(const String& value, unsigned long& parsed) {
  if (value.length() == 0) {
    return false;
  }

  unsigned long result = 0;
  for (size_t i = 0; i < value.length(); ++i) {
    const char c = value.charAt(i);
    if (!isdigit(static_cast<unsigned char>(c))) {
      return false;
    }

    const unsigned long digit = static_cast<unsigned long>(c - '0');
    if (result > (ULONG_MAX - digit) / 10UL) {
      return false;
    }
    result = result * 10UL + digit;
  }

  if (result == 0) {
    return false;
  }

  parsed = result;
  return true;
}

#endif
