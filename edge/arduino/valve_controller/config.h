#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

const uint8_t VALVE_PIN = 2;
const uint8_t SOIL_MOISTURE_PIN = A0;
const uint8_t TEST_LED_PIN = LED_BUILTIN;

const bool DRY_RUN_MODE = true;
const bool VALVE_ACTIVE_HIGH = true;
const unsigned long SERIAL_BAUD = 115200;
const size_t COMMAND_BUFFER_LIMIT = 64;

// Calibrate these raw values with the real sensor before live watering.
const int SOIL_SENSOR_DRY_RAW = 472;
const int SOIL_SENSOR_WET_RAW = 256;
const float WET_REJECT_PERCENT = 75.0f;
const size_t SENSOR_READ_SAMPLES = 10;
const unsigned long SENSOR_READ_INTERVAL_MS = 10UL;
const unsigned long AFTER_WATER_READ_DELAY_MS = 1000UL;

const unsigned long MAX_SINGLE_WATER_MS = 5000UL;
const unsigned long MAX_DAILY_WATER_MS = 30000UL;
const unsigned long DAILY_WINDOW_MS = 24UL * 60UL * 60UL * 1000UL;
const unsigned long WATER_LOOP_DELAY_MS = 10UL;

#endif
