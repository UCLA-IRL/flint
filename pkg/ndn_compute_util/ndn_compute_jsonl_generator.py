import json
import random
from datetime import datetime, timedelta
import string
from typing import Dict, Any
import os


def generate_random_string(length: int) -> str:
    """Generate a random string of specified length."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_date() -> str:
    """Generate a random date within the last year."""
    start_date = datetime.now() - timedelta(days=365)
    random_days = random.randint(0, 365)
    random_date = start_date + timedelta(days=random_days)
    return random_date.isoformat()


def generate_record() -> Dict[str, Any]:
    """Generate a single record with dummy data."""
    return {
        "id": generate_random_string(16),
        "timestamp": generate_random_date(),
        "user_id": generate_random_string(8),
        "event_type": random.choice(["page_view", "click", "purchase", "login", "logout"]),
        "device": random.choice(["mobile", "desktop", "tablet"]),
        "browser": random.choice(["chrome", "firefox", "safari", "edge"]),
        "location": {
            "country": random.choice(["US", "UK", "CA", "DE", "FR", "JP", "AU"]),
            "city": random.choice(["New York", "London", "Toronto", "Berlin", "Paris", "Tokyo", "Sydney"]),
            "latitude": random.uniform(-90, 90),
            "longitude": random.uniform(-180, 180)
        },
        "session_duration": random.randint(1, 3600),
        "metadata": {
            "platform_version": f"{random.randint(1, 10)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            "user_agent": generate_random_string(50),
            "screen_resolution": f"{random.choice([1920, 2560, 3840])}x{random.choice([1080, 1440, 2160])}",
            "language_preference": random.choice(["en - US", "en - GB", "es - ES", "de - DE", "fr - FR", "ja - JP"])
        }
    }


def generate_kv_record() -> Dict[str, Any]:
    """Generate a single key-value record with key: 0, value: dummy data."""
    return {
        "key": 0,
        "value": generate_record()
    }


def generate_large_jsonl(filename: str, target_size_mb: float) -> None:
    """
    Generate a large JSONL file with dummy data.

    Args:
        filename: Name of the output file
        target_size_mb: Desired file size in megabytes
    """
    target_size_bytes = target_size_mb * 1024 * 1024
    current_size = 0
    records_written = 0

    print(f"Generating JSONL file of approximately {target_size_mb}MB...")

    with open(filename, 'w') as f:
        while current_size < target_size_bytes:
            record = generate_record()
            json_line = json.dumps(record) + '\n'
            f.write(json_line)

            current_size = os.path.getsize(filename)
            records_written += 1

            if records_written % 100000 == 0:
                print(f"Progress: {(current_size / target_size_bytes) * 100:.2f}% complete")
                print(f"Records written: {records_written:,}")
                print(f"Current file size: {current_size / (1024 * 1024):.2f}MB")

    final_size_mb = os.path.getsize(filename) / (1024 * 1024)
    print(f"\nFile generation complete!")
    print(f"Final file size: {final_size_mb:.2f}MB")
    print(f"Total records written: {records_written:,}")
