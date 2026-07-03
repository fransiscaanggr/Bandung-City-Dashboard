from datetime import datetime, timezone


def base_fields(row: dict) -> dict:
    """Kolom lokasi & metadata yang sama di ketiga sumber data Dinas Pendidikan."""
    return {
        "source_row_id": row.get("id"),
        "kode_provinsi": row.get("kode_provinsi"),
        "nama_provinsi": row.get("nama_provinsi"),
        "bps_kode_kabupaten_kota": row.get("bps_kode_kabupaten_kota"),
        "bps_nama_kabupaten_kota": row.get("bps_nama_kabupaten_kota"),
        "bps_kode_kecamatan": row.get("bps_kode_kecamatan"),
        "bps_nama_kecamatan": row.get("bps_nama_kecamatan"),
        "bps_kode_desa_kelurahan": row.get("bps_kode_desa_kelurahan"),
        "bps_desa_kelurahan": row.get("bps_desa_kelurahan"),
        "kemendagri_kode_kecamatan": row.get("kemendagri_kode_kecamatan"),
        "kemendagri_nama_kecamatan": row.get("kemendagri_nama_kecamatan"),
        "kemendagri_kode_desa_kelurahan": row.get("kemendagri_kode_desa_kelurahan"),
        "kemendagri_nama_desa_kelurahan": row.get("kemendagri_nama_desa_kelurahan"),
        "npsn": row.get("npsn"),
        "nama_sekolah": _clean_text(row.get("nama_sekolah")),
        "status_sekolah": _upper(row.get("status_sekolah")),
        "semester_ajaran": row.get("semester_ajaran"),
        "tahun_ajaran": row.get("tahun_ajaran"),
        "tahun": row.get("tahun"),
        "scraped_at": now_iso(),
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_text(value) -> str | None:
    if value is None:
        return None
    return str(value).strip()


def _upper(value) -> str | None:
    text = _clean_text(value)
    return text.upper() if text else None


def is_valid_key_row(row: dict) -> bool:
    """Baris tanpa npsn/tahun/semester_ajaran tidak punya kunci unik yang valid untuk upsert."""
    return bool(row.get("npsn")) and row.get("tahun") is not None and row.get("semester_ajaran") is not None
