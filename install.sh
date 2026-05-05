#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "=== SoulScan Installation Script ==="
echo "Project directory: $SCRIPT_DIR"
echo "Venv directory: $VENV_DIR"

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    python3.14 -m venv "$VENV_DIR"
fi

# Install/update dependencies
echo "Installing dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"

echo ""
echo "=== Installation Complete ==="
echo ""
