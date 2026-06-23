/**
 * komatsuna-ai-agent valve controller
 * Arduino UNO R4 WiFi
 */

#include <limits.h>
#include <string.h>

#include "config.h"
#include "safety.h"
#include "sensor.h"
#include "serial_protocol.h"
#include "valve.h"

String inputBuffer = "";
bool valveOpen = false;
unsigned long dailyWateredMs = 0;
unsigned long dailyWindowStartedMs = 0;

void resetDailyUsageIfNeeded() {
  const unsigned long now = millis();
  if (now - dailyWindowStartedMs >= DAILY_WINDOW_MS) {
    dailyWateredMs = 0;
    dailyWindowStartedMs = now;
  }
}

void closeValve() {
  closeValveHardware();
  valveOpen = false;
}

void openValve() {
  openValveHardware(DRY_RUN_MODE);
  valveOpen = true;
}

void printJsonStringField(const char* key, const char* value, bool trailingComma = true) {
  Serial.print("\"");
  Serial.print(key);
  Serial.print("\":\"");
  Serial.print(value);
  Serial.print("\"");
  if (trailingComma) {
    Serial.print(",");
  }
}

void printJsonBoolField(const char* key, bool value, bool trailingComma = true) {
  Serial.print("\"");
  Serial.print(key);
  Serial.print("\":");
  Serial.print(value ? "true" : "false");
  if (trailingComma) {
    Serial.print(",");
  }
}

void printJsonULongField(const char* key, unsigned long value, bool trailingComma = true) {
  Serial.print("\"");
  Serial.print(key);
  Serial.print("\":");
  Serial.print(value);
  if (trailingComma) {
    Serial.print(",");
  }
}

void printJsonIntField(const char* key, int value, bool trailingComma = true) {
  Serial.print("\"");
  Serial.print(key);
  Serial.print("\":");
  Serial.print(value);
  if (trailingComma) {
    Serial.print(",");
  }
}

void printJsonFloatField(const char* key, float value, bool trailingComma = true) {
  Serial.print("\"");
  Serial.print(key);
  Serial.print("\":");
  Serial.print(value, 1);
  if (trailingComma) {
    Serial.print(",");
  }
}

void respondRead() {
  closeValve();
  resetDailyUsageIfNeeded();
  const SoilReading reading = readSoilReading();

  Serial.print("{");
  printJsonStringField("status", "ok");
  printJsonStringField("command", "read");
  printJsonIntField("soil_moisture_raw", reading.raw);
  printJsonFloatField("soil_moisture_percent", reading.percent);
  printJsonBoolField("is_wet", reading.isWet, false);
  Serial.println("}");
}

void respondStatus() {
  closeValve();
  resetDailyUsageIfNeeded();
  const SoilReading reading = readSoilReading();

  Serial.print("{");
  printJsonStringField("status", "ok");
  printJsonStringField("command", "status");
  printJsonULongField("uptime_ms", millis());
  printJsonBoolField("valve_open", valveOpen);
  printJsonBoolField("dry_run", DRY_RUN_MODE);
  printJsonULongField("daily_watered_ms", dailyWateredMs);
  printJsonULongField("max_single_water_ms", MAX_SINGLE_WATER_MS);
  printJsonULongField("max_daily_water_ms", MAX_DAILY_WATER_MS);
  printJsonFloatField("wet_reject_percent", WET_REJECT_PERCENT);
  printJsonIntField("soil_moisture_raw", reading.raw);
  printJsonFloatField("soil_moisture_percent", reading.percent);
  printJsonBoolField("is_wet", reading.isWet, false);
  Serial.println("}");
}

void respondClose() {
  closeValve();
  resetDailyUsageIfNeeded();

  Serial.print("{");
  printJsonStringField("status", "ok");
  printJsonStringField("command", "close");
  printJsonBoolField("valve_open", valveOpen);
  printJsonStringField("message", "valve_closed", false);
  Serial.println("}");
}

void respondInvalid(const char* command, const char* reason) {
  closeValve();

  Serial.print("{");
  printJsonStringField("status", "error");
  printJsonStringField("command", command);
  printJsonStringField("reason", reason);
  printJsonBoolField("valve_open", valveOpen);
  printJsonStringField("message", "rejected", false);
  Serial.println("}");
}

void respondSafetyReject(const char* reason, unsigned long requestedDurationMs,
                         unsigned long actualDurationMs, unsigned long currentDailyMs,
                         const SoilReading* reading) {
  closeValve();

  Serial.print("{");
  printJsonStringField("status", "rejected_by_safety");
  printJsonStringField("command", "water");
  printJsonStringField("reason", reason);
  if (reading != NULL) {
    printJsonFloatField("moisture_before_percent", reading->percent);
  }
  printJsonULongField("requested_duration_ms", requestedDurationMs);
  printJsonULongField("actual_duration_ms", actualDurationMs);
  if (currentDailyMs > 0 || strcmp(reason, "daily_limit_exceeded") == 0) {
    printJsonULongField("daily_watered_ms", currentDailyMs);
  }
  if (strcmp(reason, "daily_limit_exceeded") == 0) {
    printJsonULongField("max_daily_water_ms", MAX_DAILY_WATER_MS);
  }
  printJsonBoolField("dry_run", DRY_RUN_MODE);
  printJsonStringField("message", "rejected", false);
  Serial.println("}");
}

void respondWaterOk(const SoilReading& before, const SoilReading& after,
                    unsigned long requestedDurationMs, unsigned long actualDurationMs,
                    bool appliedLimit) {
  Serial.print("{");
  printJsonStringField("status", "ok");
  printJsonStringField("command", "water");
  printJsonFloatField("moisture_before_percent", before.percent);
  printJsonFloatField("moisture_after_percent", after.percent);
  printJsonULongField("requested_duration_ms", requestedDurationMs);
  printJsonULongField("actual_duration_ms", actualDurationMs);
  printJsonBoolField("applied_limit", appliedLimit);
  printJsonBoolField("dry_run", DRY_RUN_MODE);
  printJsonStringField("message", appliedLimit ? "watered_with_limit" : "watered", false);
  Serial.println("}");
}

void handleWaterCommand(const String& arg) {
  resetDailyUsageIfNeeded();

  String trimmedArg = arg;
  trimmedArg.trim();

  unsigned long requestedDurationMs = 0;
  if (!parsePositiveDurationMs(trimmedArg, requestedDurationMs)) {
    respondInvalid("water", "invalid_duration_ms");
    return;
  }

  const SoilReading before = readSoilReading();
  if (before.isWet) {
    respondSafetyReject("soil_too_wet", requestedDurationMs, 0, dailyWateredMs, &before);
    return;
  }

  const unsigned long actualDurationMs = clampSingleDuration(requestedDurationMs);
  if (wouldExceedDailyLimit(dailyWateredMs, actualDurationMs)) {
    respondSafetyReject("daily_limit_exceeded", requestedDurationMs, 0, dailyWateredMs, NULL);
    return;
  }

  const bool appliedLimit = actualDurationMs != requestedDurationMs;
  openValve();
  const unsigned long startedMs = millis();
  while (millis() - startedMs < actualDurationMs) {
    delay(WATER_LOOP_DELAY_MS);
  }
  closeValve();
  delay(AFTER_WATER_READ_DELAY_MS);

  dailyWateredMs += actualDurationMs;
  const SoilReading after = readSoilReading();
  respondWaterOk(before, after, requestedDurationMs, actualDurationMs, appliedLimit);
}

void processCommand(String command) {
  command.trim();
  if (command.length() == 0) {
    return;
  }

  if (command == "read") {
    respondRead();
    return;
  }

  if (command == "status") {
    respondStatus();
    return;
  }

  if (command == "close") {
    respondClose();
    return;
  }

  if (command.startsWith("water ")) {
    const String arg = command.substring(6);
    handleWaterCommand(arg);
    return;
  }

  respondInvalid("unknown", "unknown_command");
}

void setup() {
  beginValvePins();
  closeValve();

  analogReadResolution(10);
  Serial.begin(SERIAL_BAUD);
  dailyWindowStartedMs = millis();

  Serial.print("{");
  printJsonStringField("status", "ready");
  printJsonStringField("command", "boot");
  printJsonBoolField("valve_open", valveOpen);
  printJsonBoolField("dry_run", DRY_RUN_MODE);
  printJsonStringField("message", "valve_closed_on_boot", false);
  Serial.println("}");
}

void loop() {
  while (Serial.available() > 0) {
    const char c = static_cast<char>(Serial.read());

    if (c == '\n' || c == '\r') {
      if (inputBuffer.length() > 0) {
        processCommand(inputBuffer);
        inputBuffer = "";
      }
      continue;
    }

    if (inputBuffer.length() >= COMMAND_BUFFER_LIMIT) {
      inputBuffer = "";
      respondInvalid("buffer", "command_too_long");
      continue;
    }

    if (c >= 32 && c <= 126) {
      inputBuffer += c;
    }
  }
}
