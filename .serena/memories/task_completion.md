# Task Completion Checklist

When a coding task is completed, perform these steps:

## 1. Manual Testing
```bash
# Test the collector script
python3 collect_events.py

# Check logs for errors
tail -f /var/log/polisen-collector.log
```

## 2. Verify OCI Storage
```bash
# Check that events were saved
oci os object list --bucket-name polisen-events-collector --prefix "events/" | head -20

# Verify metadata updated
oci os object get --bucket-name polisen-events-collector --name "metadata/last_seen.json" --file -
```

## 3. Verify Executable Permissions
```bash
# Ensure scripts are executable
chmod +x collect_events.py setup.sh
```

## 4. Update Documentation
- Update README.md if functionality changed
- Update comments in code for significant changes

## No Formal CI/CD
This project does not have:
- Automated tests
- Linting checks
- Code formatting tools
- Git hooks

Changes are validated through manual testing only.
