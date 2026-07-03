from src.bandung_api import fetch_all
from src.pipelines.common import base_fields, is_valid_key_row
from src.supabase_client import upsert_batch

ENDPOINT = "jumlah_peserta_didik_di_sekolah_menengah_pertama_kota"
TABLE = "smp_peserta_didik"
ON_CONFLICT = "npsn,jenis_kelamin,tahun,semester_ajaran"


def _clean(row: dict) -> dict:
    return {
        **base_fields(row),
        "jenis_kelamin": (row.get("jenis_kelamin") or "").strip().upper(),
        "jumlah_siswa": row.get("jumlah_siswa") or 0,
        "satuan": row.get("satuan"),
    }


def run() -> int:
    rows = [
        _clean(row)
        for row in fetch_all(ENDPOINT)
        if is_valid_key_row(row) and row.get("jenis_kelamin")
    ]
    return upsert_batch(TABLE, rows, ON_CONFLICT)
