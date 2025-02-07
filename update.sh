#!/bin/bash

SERVICE_NAME="ntm"
INSTALL_DIR="/opt/$SERVICE_NAME"
PYTHON_BIN="$INSTALL_DIR/venv/bin/python"

echo "Updating $SERVICE_NAME..."

# Step 1: Stop the service
sudo systemctl stop $SERVICE_NAME

# Step 2: Update the module and main script
sudo cp -r core $INSTALL_DIR/
sudo cp ntm.py $INSTALL_DIR/

# Step 3: Update dependencies
source $INSTALL_DIR/venv/bin/activate
if [ -f "requirements.txt" ]; then
    pip install --upgrade -r requirements.txt
fi
deactivate

# Step 4: Restart the service
sudo systemctl start $SERVICE_NAME

echo "$SERVICE_NAME has been updated successfully!"
