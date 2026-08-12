from datetime import datetime, timezone

from src.bandung_api import fetch_all
from src.pipelines.common import to_float, to_int, upper
from src.supabase_client import upsert_batch

DINAS = "badan_pusat_statistik_kota_bandung"
ENDPOINT = "luas_kecamatan_di_kota_bandung"
TABLE = "luas_kecamatan"
ON_CONFLICT = "sumber_id"


def _clean(row: dict) -> dict:
    return {
        "sumber_id": row.get("id"),
        "bps_nama_kecamatan": upper(row.get("bps_nama_kecamatan")),
        "luas_wilayah": to_float(row.get("luas_wilayah")),
        "satuan": upper(row.get("satuan")),
        "tahun": to_int(row.get("tahun")),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def run() -> int:
    rows = [
        _clean(row)
        for row in fetch_all(DINAS, ENDPOINT)
        if row.get("id") is not None
        and row.get("bps_nama_kecamatan")
        and row.get("luas_wilayah") is not None
        and to_int(row.get("tahun")) is not None
    ]
    return upsert_batch(TABLE, rows, ON_CONFLICT)
