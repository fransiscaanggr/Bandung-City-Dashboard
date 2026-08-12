from datetime import datetime, timezone

from src.bandung_api import fetch_all
from src.pipelines.common import to_int, upper
from src.supabase_client import upsert_batch

DINAS = "dinas_lingkungan_hidup"
ENDPOINT = "jumlah_ritasi_pengangkutan_sampah_di_kota_bandung_2"
TABLE = "sampah_ritasi"
ON_CONFLICT = "sumber_id"


def _clean(row: dict) -> dict:
    return {
        "sumber_id": row.get("id"),
        "bulan": upper(row.get("bulan")),
        "jumlah_ritasi": to_int(row.get("jumlah_ritasi")) or 0,
        "satuan": upper(row.get("satuan")),
        "tahun": to_int(row.get("tahun")),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def run() -> int:
    rows = [
        _clean(row)
        for row in fetch_all(DINAS, ENDPOINT)
        if row.get("id") is not None
        and row.get("bulan")
        and to_int(row.get("tahun")) is not None
    ]
    return upsert_batch(TABLE, rows, ON_CONFLICT)
