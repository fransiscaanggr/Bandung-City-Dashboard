from src.bandung_api import fetch_all
from src.pipelines.common import base_fields, is_valid_key_row
from src.supabase_client import upsert_batch

ENDPOINT = "jumlah_guru_dan_tenaga_kependidikan_ptk_sekolah_menen"
TABLE = "smp_ptk"
ON_CONFLICT = "npsn,jenis_ptk,status_kepegawaian,tahun,semester_ajaran"


def _clean(row: dict) -> dict:
    return {
        **base_fields(row),
        "jenis_ptk": (row.get("jenis_ptk") or "").strip().upper(),
        "status_kepegawaian": (row.get("status_kepegawaian") or "").strip().upper(),
        "jumlah_ptk": row.get("jumlah_ptk") or 0,
        "satuan": row.get("satuan"),
    }


def run() -> int:
    rows = [
        _clean(row)
        for row in fetch_all(ENDPOINT)
        if is_valid_key_row(row) and row.get("jenis_ptk") and row.get("status_kepegawaian")
    ]
    return upsert_batch(TABLE, rows, ON_CONFLICT)
