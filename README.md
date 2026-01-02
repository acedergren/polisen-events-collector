# Polisen Events Collector

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![OCI](https://img.shields.io/badge/cloud-Oracle%20Cloud-red.svg)](https://www.oracle.com/cloud/)

Automated collection of Swedish Police events from the public API for machine learning and data analysis.

**Official Documentation:**
- [API Documentation](https://polisen.se/om-polisen/om-webbplatsen/oppna-data/api-over-polisens-handelser/)
- [API Usage Rules](https://polisen.se/om-polisen/om-webbplatsen/oppna-data/regler-for-oppna-data/)

## Table of Contents

- [Features](#features)
- [Security](#security)
- [Setup](#setup)
- [Storage Structure](#storage-structure)
- [Data Format](#data-format)
- [Accessing Data for ML](#accessing-data-for-ml)
- [Monitoring](#monitoring)
- [API Compliance](#api-compliance)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

**Official Documentation:**
- [API Documentation](https://polisen.se/om-polisen/om-webbplatsen/oppna-data/api-over-polisens-handelser/)
- [API Usage Rules](https://polisen.se/om-polisen/om-webbplatsen/oppna-data/regler-for-oppna-data/)

## Features

- ✅ Polls https://polisen.se/api/events
- ✅ **Fully compliant with Polisen API usage rules**
- ✅ Deduplicates events using ID tracking
- ✅ Stores data in OCI Object Storage (JSONL format)
- ✅ Stockholm region (eu-stockholm-1) for data residency
- ✅ Date-partitioned storage for efficient querying
- ✅ Suitable for machine learning pipelines

## Security

🔐 **Secrets Management**: This project uses **OCI Vault** to securely manage credentials. Vault details are configured via environment variables. No secrets are stored in local config files or committed to git.

**Key Security Features:**
- ✅ All sensitive credentials stored in OCI Vault
- ✅ Instance Principal authentication for production
- ✅ Strict .gitignore to prevent credential commits
- ✅ Minimal local config (vault access only)

**For detailed security setup, see [SECURITY.md](SECURITY.md)**

## Setup

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone https://github.com/acedergren/polisen-events-collector.git
cd polisen-events-collector

# Install production dependencies
pip3 install -r requirements.txt

# (Optional) Install development dependencies for testing
pip3 install -r requirements-dev.txt
```

### 2. Configure Environment Variables

**This project is machine-agnostic and uses environment variables for all configuration.**

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Required Environment Variables:**
- `OCI_NAMESPACE` - Your OCI Object Storage namespace
- `OCI_COMPARTMENT_ID` - OCI compartment OCID  
- `API_CONTACT_EMAIL` - Your email (included in User-Agent header per Polisen API rules)

**Optional Environment Variables:**
- `OCI_BUCKET_NAME` - Bucket name (default: `polisen-events-collector`)
- `OCI_REGION` - OCI region (default: `eu-stockholm-1`)
- `USE_VAULT` - Use OCI Vault for credentials (default: `true`)
- `LOG_DIR` - Log directory path (default: `./logs`)
- `LOG_LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR (default: `INFO`)

**Example .env file:**
```bash
# OCI Configuration
OCI_NAMESPACE=oraseemeaswedemo
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..aaaaaaaaxxxxx
OCI_REGION=eu-stockholm-1

# Application Configuration
API_CONTACT_EMAIL=your-email@example.com
USE_VAULT=true
LOG_LEVEL=INFO
```

### 3. Configure OCI Vault (Recommended for Production)

**For secure credential management, this project uses OCI Vault:**

1. Create required secrets in your OCI Vault:
   - `oci-user-ocid`
   - `oci-tenancy-ocid`
   - `oci-fingerprint`
   - `oci-private-key`

2. See [SECURITY.md](SECURITY.md) for detailed vault setup instructions

**Alternative (Local Development Only):**  
Set `USE_VAULT=false` in `.env` and use local `~/.oci/config` file.

### 4. Test the Script

```bash
# Test with your configuration
python3 collect_events.py

# Check logs
tail -f logs/polisen-collector.log
```

### 5. Set Up Automated Collection

**Recommended: Every 30 minutes** (based on API analysis showing ~3.7 events/hour)

**Option A: Automated Installation (Recommended)**
```bash
./install-scheduler.sh
```
This script automatically detects and configures either systemd timer (preferred) or cron.

**Option B: Manual Installation**

**Using systemd (recommended for modern systems):**
```bash
sudo cp polisen-collector.service /etc/systemd/system/
sudo cp polisen-collector.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now polisen-collector.timer

# Check status
sudo systemctl status polisen-collector.timer
```

**Using cron:**
```bash
sudo cp polisen-collector.cron /etc/cron.d/polisen-collector
sudo chmod 644 /etc/cron.d/polisen-collector
```

## Storage Structure

```
polisen-events-collector/
├── events/
│   └── YYYY/
│       └── MM/
│           └── DD/
│               └── events-{timestamp}.jsonl
└── metadata/
    └── last_seen.json
```

## Data Format

Each JSONL file contains one event per line:

```json
{"id": 620014, "datetime": "2026-01-02 19:56:53 +01:00", "name": "02 januari 18.30, Misshandel, Linköping", "summary": "Bråk på buss i Linköping.", "url": "/aktuellt/handelser/2026/januari/2/02-januari-18.30-misshandel-linkoping/", "type": "Misshandel", "location": {"name": "Linköping", "gps": "58.410807,15.621373"}}
```

## Accessing Data for ML

### Using OCI CLI

```bash
# List all events for a specific date
oci os object list --bucket-name polisen-events-collector --prefix "events/2026/01/02/"

# Download a specific file
oci os object get --bucket-name polisen-events-collector --name "events/2026/01/02/events-1735840000.jsonl" --file local-events.jsonl

# Download all events for a month
oci os object bulk-download --bucket-name polisen-events-collector --download-dir ./data --prefix "events/2026/01/"
```

### Using Python

```python
import oci
import json

config = oci.config.from_file()
client = oci.object_storage.ObjectStorageClient(config)

# Get events file
obj = client.get_object('oraseemeaswedemo', 'polisen-events-collector', 'events/2026/01/02/events-1735840000.jsonl')
content = obj.data.content.decode('utf-8')

# Parse JSONL
events = [json.loads(line) for line in content.strip().split('\n')]
```

## Monitoring

### View Collection Logs
```bash
# Application logs
tail -f logs/polisen-collector.log

# Cron/systemd output logs  
tail -f logs/polisen-collector-cron.log
```

### Check Scheduler Status

**Systemd:**
```bash
# Timer status
sudo systemctl status polisen-collector.timer

# Service status
sudo systemctl status polisen-collector.service

# View logs
sudo journalctl -u polisen-collector.service -f

# List next run times
systemctl list-timers polisen-collector.timer
```

**Cron:**
```bash
# View installed job
cat /etc/cron.d/polisen-collector

# Check cron logs (Ubuntu/Debian)
grep CRON /var/log/syslog | grep polisen | tail -20
```

## API Compliance

This collector fully complies with [Polisen's API usage rules](https://polisen.se/om-polisen/om-webbplatsen/oppna-data/regler-for-oppna-data/):

### Rate Limits (All ✓)
- **Minimum interval**: 10 seconds between calls → We use **30 minutes (1800s)**
- **Hourly limit**: 60 calls/hour → We make **2 calls/hour**
- **Daily limit**: 1440 calls/day → We make **~48 calls/day**

### Technical Requirements (All ✓)
- ✅ Proper User-Agent header identifying the application
- ✅ HTTPS only (enforced)
- ✅ Respects 404 responses
- ✅ No web scraping (uses official API)

### Important Notes
- **GPS Coordinates**: Approximate midpoint of municipality/county, not exact incident location
- **Event Updates**: Notiser can be updated; initial information may change
- **No Personal Data**: The API does not contain personal information
- **Publication Timing**: Events typically published within hours of occurrence

### Contact Information
Update the `USER_AGENT` constant in `collect_events.py` with your contact information before deployment.

## Configuration

All configuration is managed through environment variables in the `.env` file:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OCI_NAMESPACE` | OCI Object Storage namespace | Yes | - |
| `OCI_COMPARTMENT_ID` | OCI compartment OCID | Yes | - |
| `OCI_BUCKET_NAME` | Object Storage bucket name | No | `polisen-events-collector` |
| `OCI_REGION` | OCI region | No | `eu-stockholm-1` |
| `API_CONTACT_EMAIL` | Contact email for User-Agent | Yes | - |
| `API_USER_AGENT` | Full User-Agent string | No | Auto-generated |
| `POLISEN_API_URL` | Polisen API endpoint | No | `https://polisen.se/api/events` |
| `USE_VAULT` | Use OCI Vault for credentials | No | `true` |
| `LOG_DIR` | Log directory path | No | `./logs` |
| `LOG_LEVEL` | Logging level | No | `INFO` |

**Machine Agnosticism**: All machine-specific configuration is externalized to environment variables.  
No code changes are needed to run on different machines or environments.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Data provided by [Polisen (Swedish Police)](https://polisen.se)
- Hosted on Oracle Cloud Infrastructure (OCI)
