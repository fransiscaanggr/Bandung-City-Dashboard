from datetime import datetime, timezone

from src.bandung_api import fetch_all
from src.pipelines.common import to_int, upper
from src.supabase_client import upsert_batch

DINAS = "dinas_kependudukan_dan_pencatatan_sipil"
ENDPOINT = "jumlah_kepadatan_penduduk_di_kota_bandung_3"
TABLE = "kepadatan_penduduk"
ON_CONFLICT = "sumber_id"


def _clean(row: dict) -> dict:
    return {
        "sumber_id": row.get("id"),
        "bps_nama_kecamatan": upper(row.get("bps_nama_kecamatan")),
        "kepadatan_penduduk": to_int(row.get("kepadatan_penduduk")) or 0,
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
        and to_int(row.get("tahun")) is not None
    ]
    return upsert_batch(TABLE, rows, ON_CONFLICT)
