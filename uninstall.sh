#!/bin/bash

SERVICE_NAME="ntm"
INSTALL_DIR="/opt/$SERVICE_NAME"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
LOG_FILE="/var/log/$SERVICE_NAME.log"
COMMAND_SCRIPT="/usr/local/bin/ntm-config"

echo "Uninstalling $SERVICE_NAME..."

# Step 1: Stop and disable the service
sudo systemctl stop $SERVICE_NAME
sudo systemctl disable $SERVICE_NAME

# Step 2: Remove service files
sudo rm -rf $INSTALL_DIR
sudo rm -f $SERVICE_FILE
sudo rm -f $LOG_FILE
sudo rm -f $COMMAND_SCRIPT

# Step 3: Reload systemd
sudo systemctl daemon-reload

echo "$SERVICE_NAME has been uninstalled."
echo "The command 'ntm-config' has been removed."
