#!/bin/bash


set -e

INSTALL_DIR="/opt/soulscan"
VENV_DIR="$INSTALL_DIR/venv"
SERVICE_USER="soulscan"

echo "=== SoulScan Installation Script ==="

# Create user if not exists
if ! id "$SERVICE_USER" &>/dev/null; then
    echo "Creating user: $SERVICE_USER"
    useradd --system --no-create-home --shell /bin/false $SERVICE_USER
fi

# Create directories
echo "Creating installation directory..."
mkdir -p $INSTALL_DIR
mkdir -p $INSTALL_DIR/LogFolder

# Copy project files (adjust source path as needed)
echo "Copying project files..."
cp -r . $INSTALL_DIR/
chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv $VENV_DIR
$VENV_DIR/bin/pip install --upgrade pip
$VENV_DIR/bin/pip install -r $INSTALL_DIR/requirements.txt

# Install systemd services
echo "Installing systemd services..."
cp $INSTALL_DIR/systemd/*.service /etc/systemd/system/
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
