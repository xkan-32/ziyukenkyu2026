# Arduino UNO R4 WiFi — valve_controller
# WSL2 + arduino-cli 用ビルド/書き込みターゲット

ARDUINO_CLI ?= arduino-cli
FQBN        ?= arduino:renesas_uno:unor4wifi
SKETCH_DIR  := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
REPO_ROOT   := $(abspath $(SKETCH_DIR)/../../..)
ATTACH_USB  := $(REPO_ROOT)/tools/attach_arduino_usb.sh

.PHONY: compile upload monitor attach-usb board-list setup

compile:
	$(ARDUINO_CLI) compile --fqbn $(FQBN) "$(SKETCH_DIR)"

upload: attach-usb
	@port="$$( $(ARDUINO_CLI) board list | awk '/serial|Serial|ACM|USB/{print $$1; exit}' )"; \
	if [ -z "$$port" ]; then \
	  echo "error: シリアルポートが見つかりません。attach-usb を確認してください。" >&2; \
	  exit 1; \
	fi; \
	echo "Uploading to $$port ..."; \
	$(ARDUINO_CLI) upload -p "$$port" --fqbn $(FQBN) "$(SKETCH_DIR)"

monitor: attach-usb
	@port="$$( $(ARDUINO_CLI) board list | awk '/serial|Serial|ACM|USB/{print $$1; exit}' )"; \
	if [ -z "$$port" ]; then \
	  echo "error: シリアルポートが見つかりません。" >&2; \
	  exit 1; \
	fi; \
	$(ARDUINO_CLI) monitor -p "$$port" -c baudrate=115200

attach-usb:
	@bash "$(ATTACH_USB)"

board-list:
	$(ARDUINO_CLI) board list

setup:
	$(ARDUINO_CLI) core update-index
	$(ARDUINO_CLI) core install arduino:renesas_uno
