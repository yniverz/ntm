#!/bin/bash

SERVICE_NAME="ntm"
INSTALL_DIR="/opt/$SERVICE_NAME"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
LOG_FILE="/var/log/$SERVICE_NAME.log"
CONFIG_FILE="$INSTALL_DIR/core/config.toml"
COMMAND_FILE="core/ntm-config"
COMMAND_SCRIPT="/usr/local/bin/ntm-config"
PYTHON_BIN=$(which python3)

echo "Installing $SERVICE_NAME..."

# Step 1: Ensure Python is installed
sudo apt update && sudo apt install -y python3 python3-venv python3-pip

# Step 2: Create the installation directory
sudo mkdir -p $INSTALL_DIR
sudo cp -r core $INSTALL_DIR/  # Copy the entire core module
# sudo cp $SERVICE_NAME.py $INSTALL_DIR/  # Copy the main script
sudo cp config.template.toml $CONFIG_FILE  # Copy config file if it exists
sudo chmod +x $INSTALL_DIR/core/$SERVICE_NAME.py

# Step 5: Create a systemd service file
echo "[Unit]
Description=$SERVICE_NAME Daemon
After=network.target

[Service]
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/core/$SERVICE_NAME.py
WorkingDirectory=$INSTALL_DIR/core
Restart=always
User=$(whoami)
StandardOutput=append:$LOG_FILE
StandardError=append:$LOG_FILE

[Install]
WantedBy=multi-user.target" | sudo tee $SERVICE_FILE


# Step 6: Create a command to edit config and restart service if modified
sudo cp $COMMAND_FILE $COMMAND_SCRIPT
sudo chmod +x $COMMAND_SCRIPT

# Step 3: Set up a virtual environment
cd $INSTALL_DIR
python3 -m venv venv
source venv/bin/activate

# Step 4: Install dependencies
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
deactivate

# Step 7: Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo "$SERVICE_NAME has been installed and started successfully!"
echo "You can edit the config file using: ntm-config"
echo "Logs can be found in $LOG_FILE."
