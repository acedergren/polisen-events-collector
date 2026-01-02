#!/bin/bash
# Installation script for Polisen Events Collector scheduler

set -e

echo "=== Polisen Events Collector - Scheduler Installation ==="
echo

# Check what scheduling system is available
if command -v systemctl &> /dev/null; then
    echo "✓ systemd detected - Installing systemd timer (recommended)"
    echo

    # Copy service and timer files
    sudo cp polisen-collector.service /etc/systemd/system/
    sudo cp polisen-collector.timer /etc/systemd/system/

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

    # Copy cron file
    sudo cp polisen-collector.cron /etc/cron.d/polisen-collector
    sudo chmod 644 /etc/cron.d/polisen-collector

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
