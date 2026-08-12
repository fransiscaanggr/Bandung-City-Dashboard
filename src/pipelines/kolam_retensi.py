from datetime import datetime, timezone

from src.bandung_api import fetch_all
from src.pipelines.common import to_int, upper
from src.supabase_client import upsert_batch

DINAS = "dinas_sumber_daya_air_dan_bina_marga"
ENDPOINT = "jumlah_kolam_retensi_di_kota_bandung_2"
TABLE = "kolam_retensi"
ON_CONFLICT = "sumber_id"


def _clean(row: dict) -> dict:
    return {
        "sumber_id": row.get("id"),
        "bps_nama_kecamatan": upper(row.get("bps_nama_kecamatan")),
        "nama": upper(row.get("nama")),
        "sub_das": upper(row.get("sub_das")),
        "nama_sungai": upper(row.get("nama_sungai")),
        "jumlah_kolam": to_int(row.get("jumlah_kolam")) or 0,
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
        and row.get("nama")
        and to_int(row.get("tahun")) is not None
    ]
    return upsert_batch(TABLE, rows, ON_CONFLICT)
