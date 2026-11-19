"""HTTP client for the simulated clinic. Tests can replace `hospital_client`."""

import httpx

from app.core.config import settings


def hospital_client():
    client = httpx.Client(base_url=settings.hospital_base_url, timeout=5.0)
    try:
        yield client
    finally:
        client.close()
