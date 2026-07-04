#!/usr/bin/env bash

source ~/AI/ziyukenkyu2026/edge/raspberry-pi/.ssh-env

SSHPASS="$RASPI_PASS" sshpass -e ssh \
  -o StrictHostKeyChecking=accept-new \
  "${RASPI_USER}@${RASPI_HOST}"
