#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
    echo "ERROR: this script needs root. Run with: sudo bash setup_logrotate.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_ROOT="$SCRIPT_DIR/LogFolder"
CONFIG_FILE="/etc/logrotate.d/soulscan"

echo "=== SoulScan Logrotate Setup ==="
echo "Project directory: $SCRIPT_DIR"
echo "Log root:          $LOG_ROOT"
echo "Config file:       $CONFIG_FILE"

if ! command -v logrotate >/dev/null 2>&1; then
    echo ""
    echo "ERROR: logrotate not installed. Install it first:"
    echo "  apt install logrotate    # Debian/Ubuntu"
    echo "  yum install logrotate    # RHEL/CentOS"
    exit 1
fi

echo ""
echo "Writing $CONFIG_FILE..."

# Hourly cadence + 100M size ceiling: rotates at the top of each hour OR
# whenever a file exceeds 100M, whichever comes first. Counts are sized for
# 7 days at hourly granularity (168) and 30 days for supervisor (720).
cat > "$CONFIG_FILE" <<EOF
$LOG_ROOT/data-fetcher/*.log {
    hourly
    maxsize 100M
    rotate 168
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su root root
}

$LOG_ROOT/supervisor/*.log {
    hourly
    maxsize 100M
    rotate 720
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su root root
}

$LOG_ROOT/osr/*.log {
    hourly
    maxsize 100M
    rotate 168
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su root root
}

$LOG_ROOT/cex/*.log {
    hourly
    maxsize 100M
    rotate 168
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su root root
}

$LOG_ROOT/cex-market-data/*.log {
    hourly
    maxsize 100M
    rotate 168
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su root root
}

$LOG_ROOT/cex-contracts/*.log {
    hourly
    maxsize 100M
    rotate 168
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su root root
}
EOF

chmod 644 "$CONFIG_FILE"

echo "Validating config..."
logrotate -d "$CONFIG_FILE" >/dev/null

# logrotate's `hourly` directive is meaningless unless the OS invokes
# logrotate once an hour. Default cron only runs it daily — switch the
# scheduler to hourly.
echo ""
echo "Configuring logrotate to run hourly..."

if systemctl list-unit-files logrotate.timer >/dev/null 2>&1 && systemctl is-enabled logrotate.timer >/dev/null 2>&1; then
    # systemd timer path (modern distros: Debian 11+, Ubuntu 22+, RHEL 9+)
    OVERRIDE_DIR="/etc/systemd/system/logrotate.timer.d"
    OVERRIDE_FILE="$OVERRIDE_DIR/override.conf"
    mkdir -p "$OVERRIDE_DIR"
    cat > "$OVERRIDE_FILE" <<EOF
[Timer]
OnCalendar=
OnCalendar=hourly
EOF
    systemctl daemon-reload
    systemctl restart logrotate.timer
    echo "  systemd: installed override at $OVERRIDE_FILE"
    echo "  next firings:"
    systemctl list-timers logrotate.timer --no-pager | head -3
elif [ -f /etc/cron.daily/logrotate ]; then
    # cron path (older distros)
    mv /etc/cron.daily/logrotate /etc/cron.hourly/logrotate
    echo "  cron: moved /etc/cron.daily/logrotate → /etc/cron.hourly/logrotate"
elif [ -f /etc/cron.hourly/logrotate ]; then
    echo "  cron: /etc/cron.hourly/logrotate already in place — nothing to do"
else
    echo "  WARNING: could not detect logrotate scheduler (no systemd timer, no cron entry)."
    echo "  Add a cron job manually, e.g.:"
    echo "    echo '0 * * * * root /usr/sbin/logrotate /etc/logrotate.conf' > /etc/cron.d/logrotate-hourly"
fi

echo ""
echo "=== Logrotate config installed ==="
echo ""
echo "To force a rotation now (testing):"
echo "  sudo logrotate -f $CONFIG_FILE"
echo ""
echo "Cadence: hourly OR when a file exceeds 100M, whichever comes first."
