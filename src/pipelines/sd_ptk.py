from src.bandung_api import fetch_all
from src.pipelines.common import base_fields, is_valid_key_row, upper
from src.supabase_client import upsert_batch

ENDPOINT = "jmlh_gr_tng_kpnddkn_ptk_sklh_dsr_d_kt_bndng"
TABLE = "sd_ptk"
ON_CONFLICT = "npsn,jenis_ptk,status_kepegawaian,tahun,semester_ajaran"


def _clean(row: dict) -> dict:
    return {
        **base_fields(row),
        "jenis_ptk": upper(row.get("jenis_ptk")),
        "status_kepegawaian": upper(row.get("status_kepegawaian")),
        "jumlah_ptk": row.get("jumlah_ptk") or 0,
    }


def run() -> int:
    rows = [
        _clean(row)
        for row in fetch_all(ENDPOINT)
        if is_valid_key_row(row) and row.get("jenis_ptk") and row.get("status_kepegawaian")
    ]
    return upsert_batch(TABLE, rows, ON_CONFLICT)
