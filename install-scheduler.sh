#!/bin/bash
# Installation script for Polisen Events Collector scheduler

set -e

# Get current directory and user
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_USER="${USER}"

echo "=== Polisen Events Collector - Scheduler Installation ==="
echo "Project directory: $PROJECT_DIR"
echo "User: $CURRENT_USER"
echo

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"

# Check what scheduling system is available
if command -v systemctl &> /dev/null; then
    echo "✓ systemd detected - Installing systemd timer (recommended)"
    echo

    # Generate service file from template
    sed -e "s|{{USER}}|$CURRENT_USER|g" \
        -e "s|{{PROJECT_DIR}}|$PROJECT_DIR|g" \
        polisen-collector.service.template > /tmp/polisen-collector.service

    # Copy service and timer files
    sudo cp /tmp/polisen-collector.service /etc/systemd/system/
    sudo cp polisen-collector.timer /etc/systemd/system/
    rm /tmp/polisen-collector.service

    # Reload systemd
    sudo systemctl daemon-reload

    # Enable and start the timer
    sudo systemctl enable polisen-collector.timer
    sudo systemctl start polisen-collector.timer

    echo "✅ Systemd timer installed and started"
    echo
    echo "Management commands:"
    echo "  Status:  sudo systemctl status polisen-collector.timer"
    echo "  Stop:    sudo systemctl stop polisen-collector.timer"
    echo "  Start:   sudo systemctl start polisen-collector.timer"
    echo "  Logs:    sudo journalctl -u polisen-collector.service -f"
    echo "  Manual:  sudo systemctl start polisen-collector.service"
    echo

elif [ -d "/etc/cron.d" ]; then
    echo "✓ cron detected - Installing cron job"
    echo

    # Generate cron file from template
    sed -e "s|{{USER}}|$CURRENT_USER|g" \
        -e "s|{{PROJECT_DIR}}|$PROJECT_DIR|g" \
        polisen-collector.cron.template > /tmp/polisen-collector.cron

    # Copy cron file
    sudo cp /tmp/polisen-collector.cron /etc/cron.d/polisen-collector
    sudo chmod 644 /etc/cron.d/polisen-collector
    rm /tmp/polisen-collector.cron

    echo "✅ Cron job installed"
    echo
    echo "Management commands:"
    echo "  View:    cat /etc/cron.d/polisen-collector"
    echo "  Remove:  sudo rm /etc/cron.d/polisen-collector"
    echo "  Logs:    tail -f logs/polisen-collector-cron.log"
    echo

else
    echo "❌ Neither systemd nor cron found"
    echo "Please install manually or contact support"
    exit 1
fi

echo "Next run will occur within 30 minutes (or 2 minutes if systemd)"
echo "Check logs: tail -f logs/polisen-collector-cron.log"
