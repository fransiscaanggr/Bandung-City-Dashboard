from datetime import datetime, timezone

from src.bandung_api import fetch_all
from src.pipelines.common import to_float, to_int, upper
from src.supabase_client import upsert_batch

DINAS = "dinas_lingkungan_hidup"
ENDPOINT = "jumlah_produksi_sampah_menurut_jenisnya_di_kota_ban_2"
TABLE = "sampah_produksi"
ON_CONFLICT = "sumber_id"


def _clean(row: dict) -> dict:
    return {
        "sumber_id": row.get("id"),
        "jenis_sampah": upper(row.get("jenis_sampah")),
        "produksi_sampah": to_float(row.get("produksi_sampah")),
        "tahun": to_int(row.get("tahun")),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def run() -> int:
    rows = [
        _clean(row)
        for row in fetch_all(DINAS, ENDPOINT)
        if row.get("id") is not None
        and row.get("jenis_sampah")
        and row.get("produksi_sampah") is not None
        and to_int(row.get("tahun")) is not None
    ]
    return upsert_batch(TABLE, rows, ON_CONFLICT)
