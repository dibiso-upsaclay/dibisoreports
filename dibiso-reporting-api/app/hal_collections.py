"""
Local copy of the list of HAL collections, used by the webapp to autocomplete collection codes.

The list comes from the HAL OAI-PMH endpoint (verb=ListSets, sets prefixed with "collection:"). It is stored as a
JSON file next to the users database and refreshed every night.
"""
import asyncio
import json
import logging
import os
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

OAI_URL = "https://api.archives-ouvertes.fr/oai/hal/"
OAI_NS = "{http://www.openarchives.org/OAI/2.0/}"
COLLECTION_PREFIX = "collection:"
COLLECTIONS_PATH = Path(os.getenv("USERS_DATABASE_DIRECTORY") or ".") / "hal_collections.json"
REFRESH_HOUR = int(os.getenv("HAL_COLLECTIONS_REFRESH_HOUR", "3"))
MIN_QUERY_LENGTH = 3

_lock = threading.Lock()
_collections: list[dict] = []


def fetch_collections() -> list[dict]:
    """Download all "collection:" sets from the HAL OAI-PMH repository as [{"code", "name"}]."""
    collections = []
    params = {"verb": "ListSets"}
    while True:
        response = requests.get(OAI_URL, params=params, timeout=120)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        list_sets = root.find(f"{OAI_NS}ListSets")
        if list_sets is None:
            raise ValueError("Unexpected OAI-PMH response: no ListSets element")
        for oai_set in list_sets.findall(f"{OAI_NS}set"):
            spec = (oai_set.findtext(f"{OAI_NS}setSpec") or "").strip()
            if spec.startswith(COLLECTION_PREFIX):
                collections.append({
                    "code": spec[len(COLLECTION_PREFIX):],
                    "name": (oai_set.findtext(f"{OAI_NS}setName") or "").strip(),
                })
        token = (list_sets.findtext(f"{OAI_NS}resumptionToken") or "").strip()
        if not token:
            return collections
        params = {"verb": "ListSets", "resumptionToken": token}


def refresh_collections() -> int:
    """Fetch the collections from HAL and replace the local copy. Returns the number of collections."""
    collections = fetch_collections()
    if not collections:
        raise ValueError("No HAL collection found in the OAI-PMH response")
    COLLECTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = COLLECTIONS_PATH.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(collections, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp_path, COLLECTIONS_PATH)
    global _collections
    with _lock:
        _collections = collections
    logger.info(f"HAL collections list refreshed: {len(collections)} collections.")
    return len(collections)


def _load_from_disk() -> None:
    global _collections
    if not COLLECTIONS_PATH.exists():
        return
    try:
        collections = json.loads(COLLECTIONS_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Could not read {COLLECTIONS_PATH}: {e}")
        return
    with _lock:
        _collections = collections


def search_collections(query: str, limit: int = 20) -> list[dict]:
    """
    Return the collections whose code or name contains the query (case insensitive), codes starting with the
    query first. Returns nothing if the query is shorter than MIN_QUERY_LENGTH characters.
    """
    query = query.strip().lower()
    if len(query) < MIN_QUERY_LENGTH:
        return []
    with _lock:
        collections = _collections
    starts, contains_code, contains_name = [], [], []
    for coll in collections:
        code = coll["code"].lower()
        if code.startswith(query):
            starts.append(coll)
        elif query in code:
            contains_code.append(coll)
        elif query in coll["name"].lower():
            contains_name.append(coll)
    return (starts + contains_code + contains_name)[:limit]


def _seconds_until_next_refresh() -> float:
    now = datetime.now()
    target = now.replace(hour=REFRESH_HOUR, minute=0, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


async def collections_refresh_loop():
    """
    Background task: load the local copy at startup (fetching it if it is missing or older than a day), then
    refresh it every night. A failed refresh is retried an hour later.
    """
    await asyncio.to_thread(_load_from_disk)
    stale = not COLLECTIONS_PATH.exists() or time.time() - COLLECTIONS_PATH.stat().st_mtime > 24 * 3600
    delay = 0 if stale else _seconds_until_next_refresh()
    while True:
        try:
            await asyncio.sleep(delay)
            await asyncio.to_thread(refresh_collections)
            delay = _seconds_until_next_refresh()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Error refreshing HAL collections list (retry in 1 hour): {e}")
            delay = 3600
