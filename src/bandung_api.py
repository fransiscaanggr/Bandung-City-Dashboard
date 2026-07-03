import logging
import time
from typing import Iterator

import requests

from src.config import BANDUNG_API_BASE_URL

logger = logging.getLogger(__name__)


def fetch_all(endpoint: str, per_page: int = 1000, max_retries: int = 3, timeout: int = 30) -> Iterator[dict]:
    """Ambil semua baris dari satu endpoint API opendata Bandung, dengan pagination otomatis."""
    url = f"{BANDUNG_API_BASE_URL}/{endpoint}"
    page = 1
    while True:
        payload = _get_with_retry(url, {"page": page, "per_page": per_page}, max_retries, timeout)
        rows = payload.get("data") or []
        if not rows:
            break

        yield from rows

        pagination = payload.get("pagination") or {}
        if not pagination.get("has_next"):
            break
        page += 1


def _get_with_retry(url: str, params: dict, max_retries: int, timeout: int) -> dict:
    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_exc = exc
            logger.warning("Percobaan %d/%d gagal untuk %s: %s", attempt, max_retries, url, exc)
            if attempt < max_retries:
                time.sleep(2 * attempt)
    raise last_exc
