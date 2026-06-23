#ifndef CONFIG_H
#define CONFIG_H

// ピン定義
const int VALVE_PIN = 2;
const int SOIL_MOISTURE_PIN = A0;

// 土壌水分閾値（%）— 校正後に調整
const float WET_THRESHOLD_PERCENT = 70.0;

// バルブ最大開放時間（ミリ秒）
const unsigned long MAX_VALVE_OPEN_MS = 10000;

// シリアル設定
const unsigned long SERIAL_BAUD = 115200;

#endif
