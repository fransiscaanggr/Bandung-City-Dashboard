from datetime import datetime, timezone


def base_fields(row: dict) -> dict:
    """Kolom yang sama di ketiga sumber data Dinas Pendidikan."""
    return {
        "npsn": row.get("npsn"),
        "kemendagri_nama_kecamatan": row.get("kemendagri_nama_kecamatan"),
        "semester_ajaran": row.get("semester_ajaran"),
        "tahun": row.get("tahun"),
        "scraped_at": now_iso(),
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def upper(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text.upper() if text else None


def is_valid_key_row(row: dict) -> bool:
    """Baris tanpa npsn/tahun/semester_ajaran tidak punya kunci unik yang valid untuk upsert."""
    return bool(row.get("npsn")) and row.get("tahun") is not None and row.get("semester_ajaran") is not None
