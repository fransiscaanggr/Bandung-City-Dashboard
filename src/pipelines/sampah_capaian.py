from datetime import datetime, timezone

from src.bandung_api import fetch_all
from src.pipelines.common import to_float, to_int, upper
from src.supabase_client import upsert_batch

DINAS = "dinas_lingkungan_hidup"
ENDPOINT = "jumlah_capaian_penanganan_sampah_di_kota_bandung_1"
TABLE = "sampah_capaian"
ON_CONFLICT = "sumber_id"


def _clean(row: dict) -> dict:
    return {
        "sumber_id": row.get("id"),
        "bulan": upper(row.get("bulan")),
        "jumlah_sampah": to_float(row.get("jumlah_sampah")),
        "tahun": to_int(row.get("tahun")),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def run() -> int:
    rows = [
        _clean(row)
        for row in fetch_all(DINAS, ENDPOINT)
        if row.get("id") is not None
        and row.get("bulan")
        and row.get("jumlah_sampah") is not None
        and to_int(row.get("tahun")) is not None
    ]
    return upsert_batch(TABLE, rows, ON_CONFLICT)
