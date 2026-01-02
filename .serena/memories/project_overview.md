# Polisen Events Collector - Project Overview

## Purpose
Automated collection script that polls the Swedish Police public API (https://polisen.se/api/events) and stores events in Oracle Cloud Infrastructure (OCI) Object Storage for later machine learning analysis.

## Key Features
- Polls API for latest 500 events (incrementally filled by API)
- Deduplicates events using ID tracking
- Stores data in JSONL format (one JSON object per line)
- Date-partitioned storage structure (YYYY/MM/DD)
- Designed to run as a cronjob

## Tech Stack
- **Language**: Python 3
- **Dependencies**: 
  - `oci` - Oracle Cloud Infrastructure SDK
  - `requests` - HTTP client for API polling
- **Storage**: OCI Object Storage (bucket: `polisen-events-collector`)
- **Deployment**: Cronjob (recommended: every 30 minutes)

## Storage Structure
```
polisen-events-collector/
├── events/YYYY/MM/DD/events-{timestamp}.jsonl
└── metadata/last_seen.json
```

## Event Rate
- Current rate: ~3.7 events/hour
- Expected events per 30min poll: ~1.8 events
- API buffer (500 events) fills in ~5.6 days
- **Safe polling interval: 30 minutes**

## API Compliance
Fully compliant with Polisen API usage rules:
- ✅ User-Agent header required (identifies application)
- ✅ Min 10s between calls → We use 30min (1800s)
- ✅ Max 60 calls/hour → We make 2/hour
- ✅ Max 1440 calls/day → We make ~48/day
- ✅ HTTPS only
- Important: Update USER_AGENT constant with your contact info
