from src.bandung_api import fetch_all
from src.pipelines.common import base_fields, is_valid_key_row, upper
from src.supabase_client import upsert_batch

ENDPOINT = "jumlah_guru_dan_tenaga_kependidikan_ptk_sekolah_menen"
TABLE = "smp_ptk"
ON_CONFLICT = "npsn,status_kepegawaian,tahun,semester_ajaran"


def _clean(row: dict) -> dict:
    return {
        **base_fields(row),
        "status_kepegawaian": upper(row.get("status_kepegawaian")),
        "jumlah_ptk": row.get("jumlah_ptk") or 0,
    }


def _merge_by_key(rows: list[dict]) -> list[dict]:
    """Sumber data punya baris terpisah per jenis_ptk (guru/kepala sekolah/tendik).
    Karena jenis_ptk tidak disimpan, baris dengan npsn+status_kepegawaian+tahun+semester
    yang sama harus dijumlahkan disini, supaya upsert tidak saling menimpa jumlah_ptk.
    """
    merged: dict[tuple, dict] = {}
    for row in rows:
        key = (row["npsn"], row["status_kepegawaian"], row["tahun"], row["semester_ajaran"])
        if key in merged:
            merged[key]["jumlah_ptk"] += row["jumlah_ptk"]
        else:
            merged[key] = dict(row)
    return list(merged.values())


def run() -> int:
    rows = [
        _clean(row)
        for row in fetch_all(ENDPOINT)
        if is_valid_key_row(row) and row.get("status_kepegawaian")
    ]
    return upsert_batch(TABLE, _merge_by_key(rows), ON_CONFLICT)
