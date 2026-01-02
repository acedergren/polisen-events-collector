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

# Create log directory with secure permissions
echo "📝 Setting up log files..."
LOG_DIR="${LOG_DIR:-./logs}"
mkdir -p "$LOG_DIR"
chmod 750 "$LOG_DIR"

# Set up log files in user directory (no sudo needed)
touch "$LOG_DIR/polisen-collector.log"
touch "$LOG_DIR/polisen-collector-cron.log"
chmod 640 "$LOG_DIR/polisen-collector.log"
chmod 640 "$LOG_DIR/polisen-collector-cron.log"

# Make script executable
echo "🔧 Making script executable..."
chmod +x collect_events.py

# Test OCI connection (only if USE_VAULT=false)
if [ "${USE_VAULT:-true}" = "false" ]; then
    echo "🔍 Testing OCI connection..."
    python3 -c "import oci; config = oci.config.from_file(); print('✅ OCI config valid')" || {
        echo "❌ OCI configuration issue. Please check ~/.oci/config"
        exit 1
    }
else
    echo "ℹ️  Using OCI Vault for credentials (secure mode)"
fi

echo
echo "✅ Setup complete!"
echo
echo "Next steps:"
echo "1. Configure .env file: cp .env.example .env && nano .env"
echo "2. Test the collector: python3 collect_events.py"
echo "3. Set up scheduler: ./install-scheduler.sh"
echo
