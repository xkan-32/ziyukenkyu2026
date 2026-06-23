/**
 * komatsuna-ai-agent — ソレノイドバルブ・土壌水分コントローラ
 * Arduino UNO R4 WiFi
 *
 * プレースホルダー実装。安全制御の骨格のみ。
 */

#include "config.h"
#include "sensor.h"
#include "valve.h"
#include "safety.h"
#include "serial_protocol.h"

String inputBuffer = "";

// JSON 風レスポンスを返す
void sendJsonResponse(const char* status, float moistureBefore, float moistureAfter,
                      unsigned long durationMs, const char* message) {
  Serial.print("{\"status\":\"");
  Serial.print(status);
  Serial.print("\",\"moisture_before\":");
  Serial.print(moistureBefore, 1);
  Serial.print(",\"moisture_after\":");
  Serial.print(moistureAfter, 1);
  Serial.print(",\"duration_ms\":");
  Serial.print(durationMs);
  Serial.print(",\"message\":\"");
  Serial.print(message);
  Serial.println("\"}");
}

void handleReadCommand() {
  float moisture = readSoilMoisturePercent();
  sendJsonResponse("ok", moisture, moisture, 0, "read");
}

void handleWaterCommand(unsigned long requestedDurationMs) {
  float moistureBefore = readSoilMoisturePercent();

  // 安全チェック: wet 判定時は拒否
  if (!isSafeToWater(moistureBefore)) {
    sendJsonResponse("rejected", moistureBefore, moistureBefore, 0, "soil too wet");
    return;
  }

  // 最大開放時間を超えないよう制限
  unsigned long durationMs = clampDuration(requestedDurationMs);

  openValve();
  unsigned long startMs = millis();
  while (millis() - startMs < durationMs) {
    // ウォッチドッグ的に最大時間を再確認
    if (millis() - startMs >= MAX_VALVE_OPEN_MS) {
      break;
    }
    delay(10);
  }
  closeValve();

  float moistureAfter = readSoilMoisturePercent();
  sendJsonResponse("ok", moistureBefore, moistureAfter, durationMs, "watered");
}

void processCommand(String command) {
  command.trim();
  if (command.length() == 0) {
    return;
  }

  if (command == "read") {
    handleReadCommand();
    return;
  }

  if (command.startsWith("water ")) {
    unsigned long durationMs = command.substring(6).toInt();
    if (durationMs == 0) {
      sendJsonResponse("error", readSoilMoisturePercent(), 0, 0, "invalid duration");
      return;
    }
    handleWaterCommand(durationMs);
    return;
  }

  sendJsonResponse("error", readSoilMoisturePercent(), 0, 0, "unknown command");
}

void setup() {
  pinMode(VALVE_PIN, OUTPUT);
  closeValve();  // 起動時にバルブを閉じる

  Serial.begin(SERIAL_BAUD);
  while (!Serial) {
    ;  // USB シリアル接続待ち
  }

  Serial.println("{\"status\":\"ready\",\"message\":\"valve closed on boot\"}");
}

void loop() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (inputBuffer.length() > 0) {
        processCommand(inputBuffer);
        inputBuffer = "";
      }
    } else {
      inputBuffer += c;
    }
  }
}
