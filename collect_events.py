#!/usr/bin/env python3
"""
Polisen Events Collector
Polls the Swedish Police API and stores new events in OCI Object Storage
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import List, Dict, Optional, Set

import requests
import oci

from secrets_manager import get_oci_config_from_vault

# Configuration - Load from environment variables for machine agnosticism
API_URL = os.getenv("POLISEN_API_URL", "https://polisen.se/api/events")
BUCKET_NAME = os.getenv("OCI_BUCKET_NAME", "polisen-events-collector")
NAMESPACE = os.getenv("OCI_NAMESPACE")  # Required
METADATA_FILE = "metadata/last_seen.json"
COMPARTMENT_ID = os.getenv("OCI_COMPARTMENT_ID")  # Required
OCI_REGION = os.getenv("OCI_REGION", "eu-stockholm-1")  # Stockholm region for data residency

# Validate required environment variables
if not NAMESPACE:
    raise ValueError("OCI_NAMESPACE environment variable is required")
if not COMPARTMENT_ID:
    raise ValueError("OCI_COMPARTMENT_ID environment variable is required")

# Security: Validate API_URL uses HTTPS only
if not API_URL.startswith("https://"):
    raise ValueError("POLISEN_API_URL must use HTTPS protocol for security")

# Polling Configuration (based on API analysis - 2026-01-02)
# Current event rate: ~3.7 events/hour (1.8 events per 30 minutes)
# Recommended polling interval: Every 30 minutes
# Rationale: At this rate, the API's 500-event buffer takes ~5.6 days to fill.
#            Polling every 30 minutes ensures we never miss events without spamming the API.
#
# API Usage Rules (https://polisen.se/om-polisen/om-webbplatsen/oppna-data/regler-for-oppna-data/):
# - Must include User-Agent header identifying the application
# - Minimum 10 seconds between calls (we use 30 minutes = 1800 seconds ✓)
# - Maximum 60 calls per hour (we make 2 calls per hour ✓)
# - Maximum 1440 calls per day (we make ~48 calls per day ✓)
# - Must use HTTPS (we do ✓)

# User-Agent for API requests (required by Polisen API terms)
# Can be overridden with API_USER_AGENT environment variable
API_CONTACT_EMAIL = os.getenv("API_CONTACT_EMAIL", "your-email@example.com")
USER_AGENT = os.getenv(
    "API_USER_AGENT",
    f"PolisEnEventsCollector/1.0 (Data Collection for ML Analysis; Contact: {API_CONTACT_EMAIL})"
)

# Set up logging
# Use project-relative path or environment variable
LOG_DIR = os.getenv("LOG_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs"))
os.makedirs(LOG_DIR, exist_ok=True)

# Get log level from environment (default: INFO)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, LOG_LEVEL, logging.INFO)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'polisen-collector.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class PolisenCollector:
    """Collects and stores Swedish Police events"""

    def __init__(self, use_vault: bool = True):
        """
        Initialize OCI client and configuration
        
        Args:
            use_vault: If True, load credentials from OCI Vault (secure, recommended).
                      If False, use local config file (legacy, for testing only).
        """
        try:
            if use_vault:
                logger.info("Loading OCI credentials from vault (secure mode)")
                self.config = get_oci_config_from_vault()
                # Override region for object storage
                self.config["region"] = OCI_REGION
            else:
                logger.warning("Using local config file (INSECURE - only for testing!)")
                self.config = oci.config.from_file()
                self.config["region"] = OCI_REGION
            
            self.object_storage = oci.object_storage.ObjectStorageClient(self.config)
            logger.info(f"OCI client initialized successfully (region: {OCI_REGION})")
        except Exception as e:
            logger.error(f"Failed to initialize OCI client: {e}")
            raise

    def fetch_events(self) -> List[Dict]:
        """Fetch events from the Polisen API with required User-Agent header"""
        headers = {
            'User-Agent': USER_AGENT
        }
        try:
            logger.info(f"Fetching events from {API_URL}")
            # Security: verify=True is the default, but we explicitly set it for clarity
            # This ensures SSL/TLS certificate validation is always performed
            response = requests.get(API_URL, headers=headers, timeout=30, verify=True)
            response.raise_for_status()
            events = response.json()
            
            # Security: Validate response structure
            if not isinstance(events, list):
                raise ValueError("API response is not a list of events")
            
            logger.info(f"Fetched {len(events)} events from API")
            return events
        except requests.RequestException as e:
            logger.error(f"Failed to fetch events: {e}")
            raise
        except (ValueError, KeyError) as e:
            logger.error(f"Invalid API response format: {e}")
            raise

    def get_last_seen_ids(self) -> Set[int]:
        """Retrieve the set of last seen event IDs from OCI"""
        try:
            obj = self.object_storage.get_object(
                NAMESPACE,
                BUCKET_NAME,
                METADATA_FILE
            )
            data = json.loads(obj.data.content.decode('utf-8'))
            logger.info(f"Loaded {len(data.get('seen_ids', []))} previously seen event IDs")
            return set(data.get('seen_ids', []))
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                logger.info("No previous metadata found, starting fresh")
                return set()
            logger.error(f"Failed to retrieve metadata: {e}")
            raise

    def update_last_seen_ids(self, seen_ids: Set[int]):
        """Update the metadata file with seen event IDs"""
        # Keep only the most recent 1000 IDs to prevent unbounded growth
        # Since API returns max 500, this gives us a buffer
        seen_ids_list = sorted(seen_ids, reverse=True)[:1000]

        metadata = {
            'seen_ids': seen_ids_list,
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'total_tracked': len(seen_ids_list)
        }

        try:
            self.object_storage.put_object(
                NAMESPACE,
                BUCKET_NAME,
                METADATA_FILE,
                json.dumps(metadata, indent=2).encode('utf-8')
            )
            logger.info(f"Updated metadata with {len(seen_ids_list)} tracked IDs")
        except Exception as e:
            logger.error(f"Failed to update metadata: {e}")
            raise

    @staticmethod
    def normalize_datetime(datetime_str: str) -> str:
        """
        Normalize datetime string to handle single-digit hours.
        Converts '2026-01-02 9:38:09 +01:00' to '2026-01-02 09:38:09 +01:00'
        """
        import re
        # Match pattern: YYYY-MM-DD H:MM:SS +HH:MM (single digit hour)
        pattern = r'(\d{4}-\d{2}-\d{2}) (\d):(\d{2}:\d{2} [+-]\d{2}:\d{2})'
        match = re.match(pattern, datetime_str)
        if match:
            date_part, hour, rest = match.groups()
            return f"{date_part} 0{hour}:{rest}"
        return datetime_str

    def save_events(self, events: List[Dict]):
        """Save events to OCI Object Storage in JSONL format, partitioned by date"""
        if not events:
            logger.info("No new events to save")
            return

        # Group events by date for partitioning
        events_by_date = {}
        for event in events:
            # Security: Validate event has required fields
            if not isinstance(event, dict) or 'id' not in event or 'datetime' not in event:
                logger.warning(f"Skipping invalid event structure: {event}")
                continue
            
            # Parse the datetime field: "2026-01-02 19:56:53 +01:00"
            try:
                normalized_dt = self.normalize_datetime(event['datetime'])
                event_dt = datetime.fromisoformat(normalized_dt)
                date_key = event_dt.strftime('%Y/%m/%d')

                if date_key not in events_by_date:
                    events_by_date[date_key] = []
                events_by_date[date_key].append(event)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse datetime for event {event.get('id')}: {e}")
                continue

        # Save each date partition
        for date_path, date_events in events_by_date.items():
            timestamp = int(datetime.now(timezone.utc).timestamp())
            object_name = f"events/{date_path}/events-{timestamp}.jsonl"

            # Create JSONL content
            jsonl_content = '\n'.join(json.dumps(event, ensure_ascii=False) for event in date_events)

            try:
                self.object_storage.put_object(
                    NAMESPACE,
                    BUCKET_NAME,
                    object_name,
                    jsonl_content.encode('utf-8')
                )
                logger.info(f"Saved {len(date_events)} events to {object_name}")
            except Exception as e:
                logger.error(f"Failed to save events to {object_name}: {e}")
                raise

    def run(self):
        """Main execution method"""
        logger.info("=" * 60)
        logger.info("Starting Polisen Events Collection")
        logger.info("=" * 60)

        try:
            # Fetch current events
            all_events = self.fetch_events()

            # Get previously seen event IDs
            seen_ids = self.get_last_seen_ids()

            # Filter for new events only
            new_events = [event for event in all_events if event['id'] not in seen_ids]

            logger.info(f"Found {len(new_events)} new events out of {len(all_events)} total")

            if new_events:
                # Save new events
                self.save_events(new_events)

                # Update seen IDs
                new_ids = {event['id'] for event in all_events}
                updated_seen_ids = seen_ids.union(new_ids)
                self.update_last_seen_ids(updated_seen_ids)

                logger.info(f"Successfully processed {len(new_events)} new events")
            else:
                logger.info("No new events found")

            logger.info("Collection completed successfully")

        except Exception as e:
            logger.error(f"Collection failed: {e}", exc_info=True)
            sys.exit(1)


if __name__ == "__main__":
    # Use vault by default (secure)
    # Set USE_VAULT=false environment variable to use local config (testing only)
    use_vault = os.getenv("USE_VAULT", "true").lower() != "false"
    
    collector = PolisenCollector(use_vault=use_vault)
    collector.run()
