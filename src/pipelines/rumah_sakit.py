from datetime import datetime, timezone

from src.bandung_api import fetch_all
from src.pipelines.common import to_float, to_int, upper
from src.supabase_client import upsert_batch

DINAS = "dinas_kesehatan"
ENDPOINT = "rumah_sakit_di_kota_bandung_1"
TABLE = "rumah_sakit"
ON_CONFLICT = "sumber_id"


def _clean(row: dict) -> dict:
    return {
        "sumber_id": row.get("id"),
        "nama_rs": (row.get("nama_rs") or "").strip() or None,
        "kemendagri_nama_kecamatan": upper(row.get("kemendagri_nama_kecamatan")),
        "jenis_rs": upper(row.get("jenis_rs")),
        "status_rs": upper(row.get("status_rs")),
        "kelas": upper(row.get("kelas")),
        "latitude": to_float(row.get("lat")),
        "longitude": to_float(row.get("long")),
        "tahun": to_int(row.get("tahun")),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def run() -> int:
    rows = [
        _clean(row)
        for row in fetch_all(DINAS, ENDPOINT)
        if row.get("id") is not None
        and row.get("kemendagri_nama_kecamatan")
        and row.get("jenis_rs")
        and row.get("status_rs")
        and to_int(row.get("tahun")) is not None
    ]
    return upsert_batch(TABLE, rows, ON_CONFLICT)
