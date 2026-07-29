from datetime import datetime, timezone

from src.bandung_api import fetch_all
from src.pipelines.common import upper
from src.supabase_client import upsert_batch

DINAS = "dinas_kesehatan"
ENDPOINT = "rumah_sakit_di_kota_bandung"
TABLE = "rumah_sakit"
ON_CONFLICT = "sumber_id"


def _clean(row: dict) -> dict:
    return {
        "sumber_id": row.get("id"),
        "kecamatan": upper(row.get("kecamatan")),
        "jenis_rumah_sakit": upper(row.get("jenis_rumah_sakit")),
        "kelas": upper(row.get("kelas")),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def run() -> int:
    rows = [
        _clean(row)
        for row in fetch_all(DINAS, ENDPOINT)
        if row.get("id") is not None and row.get("kecamatan") and row.get("jenis_rumah_sakit")
    ]
    return upsert_batch(TABLE, rows, ON_CONFLICT)
