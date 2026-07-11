from datetime import datetime, timezone


def base_fields(row: dict) -> dict:
    """Kolom yang sama di ketiga sumber data Dinas Pendidikan."""
    return {
        "npsn": to_int(row.get("npsn")),
        "kemendagri_nama_kecamatan": row.get("kemendagri_nama_kecamatan"),
        "semester_ajaran": to_int(row.get("semester_ajaran")),
        "tahun": to_int(row.get("tahun")),
        "scraped_at": now_iso(),
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def upper(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text.upper() if text else None


def to_int(value) -> int | None:
    """Sumber data kadang kirim angka sebagai string (mis. tahun/semester/npsn di dataset SD)."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def to_float(value) -> float | None:
    """Sama seperti to_int, buat latitude/longitude yang kadang dikirim sebagai string."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_valid_key_row(row: dict) -> bool:
    """Baris tanpa npsn/tahun/semester_ajaran tidak punya kunci unik yang valid untuk upsert."""
    return (
        to_int(row.get("npsn")) is not None
        and to_int(row.get("tahun")) is not None
        and to_int(row.get("semester_ajaran")) is not None
    )
