from src.bandung_api import fetch_all
from src.pipelines.common import base_fields, is_valid_key_row
from src.supabase_client import upsert_batch

ENDPOINT = "sekolah_menengah_pertama_di_kota_bandung"
TABLE = "smp_sekolah"
ON_CONFLICT = "npsn,tahun,semester_ajaran"


def _clean(row: dict) -> dict:
    return {
        **base_fields(row),
        "alamat": row.get("alamat"),
        "latitude": row.get("latitude"),
        "longitude": row.get("longitude"),
        "no_telepon": row.get("no_telepon"),
    }


def run() -> int:
    rows = [_clean(row) for row in fetch_all(ENDPOINT) if is_valid_key_row(row)]
    return upsert_batch(TABLE, rows, ON_CONFLICT)
