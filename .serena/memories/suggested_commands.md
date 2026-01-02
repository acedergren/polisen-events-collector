# Suggested Commands

## Setup
```bash
# Install dependencies
pip3 install -r requirements.txt --user

# Run automated setup
./setup.sh
```

## Running the Collector
```bash
# Manual test run
python3 collect_events.py

# View logs
tail -f /var/log/polisen-collector.log
tail -f /var/log/polisen-collector-cron.log
```

## Cronjob Setup
```bash
# Edit crontab
crontab -e

# Add this line for 30-minute polling (recommended):
*/30 * * * * /usr/bin/python3 /home/alex/projects/polisen-events-collector/collect_events.py >> /var/log/polisen-collector-cron.log 2>&1

# View current cronjobs
crontab -l

# Check cronjob execution logs
grep CRON /var/log/syslog | tail -20
```

## OCI Object Storage Commands
```bash
# List events for a specific date
oci os object list --bucket-name polisen-events-collector --prefix "events/2026/01/02/"

# Download a specific file
oci os object get --bucket-name polisen-events-collector --name "events/2026/01/02/events-1735840000.jsonl" --file local-events.jsonl

# Download all events for a month
oci os object bulk-download --bucket-name polisen-events-collector --download-dir ./data --prefix "events/2026/01/"

# View metadata
oci os object get --bucket-name polisen-events-collector --name "metadata/last_seen.json" --file -
```

## System Utilities (Linux)
- `ls`, `cd`, `mkdir`, `rm` - File operations
- `grep`, `find` - Search tools
- `tail`, `cat`, `less` - View files
- `chmod`, `chown` - Permissions
- `python3` - Python interpreter
