#!/bin/bash
# Setup script for Polisen Events Collector

set -e

echo "=== Polisen Events Collector Setup ==="
echo

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please do not run as root. Run as your regular user."
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt --user

# Create log directory
echo "📝 Setting up log files..."
sudo mkdir -p /var/log
sudo touch /var/log/polisen-collector.log
sudo touch /var/log/polisen-collector-cron.log
sudo chown $USER:$USER /var/log/polisen-collector.log
sudo chown $USER:$USER /var/log/polisen-collector-cron.log

# Make script executable
echo "🔧 Making script executable..."
chmod +x collect_events.py

# Test OCI connection
echo "🔍 Testing OCI connection..."
python3 -c "import oci; config = oci.config.from_file(); print('✅ OCI config valid')" || {
    echo "❌ OCI configuration issue. Please check ~/.oci/config"
    exit 1
}

echo
echo "✅ Setup complete!"
echo
echo "Next steps:"
echo "1. Test the collector: python3 collect_events.py"
echo "2. Set up cronjob: crontab -e"
echo "   Add (recommended - 30 min interval based on API rate analysis):"
echo "   */30 * * * * /usr/bin/python3 $(pwd)/collect_events.py >> /var/log/polisen-collector-cron.log 2>&1"
echo
