#!/bin/bash

SERVICE_NAME="ntm"
CONFIG_FILE="/opt/$SERVICE_NAME/config.toml"
FRPC_CONFIG="/opt/$SERVICE_NAME/bin/frp/frpc.toml"
FRPS_CONFIG="/opt/$SERVICE_NAME/bin/frp/frps.toml"
PYTHON_SCRIPT="/opt/$SERVICE_NAME/$SERVICE_NAME.py"
VENV_PYTHON="/opt/$SERVICE_NAME/venv/bin/python"

# Function to display help message
show_help() {
    echo "Usage: ntm-config [OPTION]"
    echo "Edit configuration files and restart services if changes are detected."
    echo ""
    echo "Options:"
    echo "  -c           Edit the frpc.toml configuration file"
    echo "  -s           Edit the frps.toml configuration file"
    echo "  -h, --help   Display this help message"
    exit 0
}

# Handle command-line arguments
case "$1" in
    -c) CONFIG_FILE="$FRPC_CONFIG" ;;
    -s) CONFIG_FILE="$FRPS_CONFIG" ;;
    -h|--help) show_help ;;
    "") ;;  # No argument, default behavior
    *) echo "Invalid option: $1" && show_help ;;
esac

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file $CONFIG_FILE does not exist."
    exit 1
fi

# Calculate initial checksum
OLD_CHECKSUM=$(sha256sum "$CONFIG_FILE" | awk '{print $1}')

# Open config file in nano
nano "$CONFIG_FILE"

# Calculate new checksum
NEW_CHECKSUM=$(sha256sum "$CONFIG_FILE" | awk '{print $1}')

# Compare checksums
if [ "$OLD_CHECKSUM" != "$NEW_CHECKSUM" ]; then
    echo "Config changed. Restarting $SERVICE_NAME service and Python script..."
    sudo systemctl restart "$SERVICE_NAME"
    
    # Restart the Python script
    pkill -f "$PYTHON_SCRIPT"
    nohup "$VENV_PYTHON" "$PYTHON_SCRIPT" > /dev/null 2>&1 &

    echo "$SERVICE_NAME and Python script have been restarted."
else
    echo "No changes detected. Service and script will not be restarted."
fi
