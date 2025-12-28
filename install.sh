#!/bin/bash

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo "=== SoulScan Installation Script ==="
echo "Project directory: $SCRIPT_DIR"
echo "Venv directory: $VENV_DIR"

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    python3.12 -m venv "$VENV_DIR"
fi

# Install/update dependencies
echo "Installing dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"

# Create LogFolder if not exists
mkdir -p "$SCRIPT_DIR/LogFolder"
mkdir -p "$SCRIPT_DIR/LogFolder/osr"
mkdir -p "$SCRIPT_DIR/LogFolder/scanner"
mkdir -p "$SCRIPT_DIR/LogFolder/data-fetcher"
mkdir -p "$SCRIPT_DIR/LogFolder/supervisor"


# Install systemd services
echo "Installing systemd services..."
cp "$SCRIPT_DIR/systemd/"*.service /etc/systemd/system/
systemctl daemon-reload

# Enable services
echo "Enabling services..."
systemctl enable soulscan-metadata-fetcher
systemctl enable soulscan-state-fetcher
systemctl enable soulscan-smart-router
systemctl enable soulscan-scanner

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Start all services:"
echo "  sudo systemctl start soulscan-metadata-fetcher"
echo "  sudo systemctl start soulscan-state-fetcher"
echo "  sudo systemctl start soulscan-smart-router"
echo "  sudo systemctl start soulscan-scanner"
echo ""
echo "Or start all at once:"
echo "  sudo systemctl start soulscan-{metadata-fetcher,state-fetcher,smart-router,scanner}"
echo ""
echo "View logs:"
echo "  journalctl -u soulscan-scanner -f"
echo ""
echo "Check status:"
echo "  systemctl status soulscan-*"
