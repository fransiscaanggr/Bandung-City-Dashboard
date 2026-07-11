from src.bandung_api import fetch_all
from src.pipelines.common import base_fields, is_valid_key_row, to_float, upper
from src.supabase_client import upsert_batch

ENDPOINT = "sekolah_dasar_di_kota_bandung"
TABLE = "sd_sekolah"
ON_CONFLICT = "npsn,tahun,semester_ajaran"


def _clean(row: dict) -> dict:
    return {
        **base_fields(row),
        "status_sekolah": upper(row.get("status_sekolah")),
        "latitude": to_float(row.get("latitude")),
        "longitude": to_float(row.get("longitude")),
    }


def run() -> int:
    rows = [_clean(row) for row in fetch_all(ENDPOINT) if is_valid_key_row(row)]
    return upsert_batch(TABLE, rows, ON_CONFLICT)
