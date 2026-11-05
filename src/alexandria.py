"""Minimal client for Firecrawl Alexandria capabilities through the Firecrawl API."""
import os
import time
import uuid

import requests

URL = "https://api.firecrawl.dev/v2/scrape"


def call(provider: str, capability: str, options: dict) -> dict:
    """Run one Alexandria capability and return the full JSON response.

    The same x-request-id is reused on retries so a retried call is never billed twice.
    """
    key = os.environ.get("FIRECRAWL_API_KEY")
    if not key:
        raise SystemExit("Set FIRECRAWL_API_KEY to fetch live data. The repo ships data/raw, so you can skip this.")
    request_id = str(uuid.uuid4())
    body = {"alexandria": {"provider": provider, "capability": capability, "options": options}}
    for attempt in range(4):
        r = requests.post(
            URL,
            headers={"Authorization": f"Bearer {key}", "x-request-id": request_id},
            json=body,
            timeout=180,
        )
        if r.status_code in (409, 429, 503) and attempt < 3:
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        data = r.json()
        if not data.get("success"):
            raise RuntimeError(f"{provider}/{capability} failed: {data.get('error')}")
        item = data["data"]["alexandria"][0]
        if item.get("error"):
            raise RuntimeError(f"{provider}/{capability} item error: {item['error']}")
        return data
    raise RuntimeError("retries exhausted")


def credits(response: dict) -> int:
    return response["data"]["alexandria"][0].get("creditsCost", 0)
