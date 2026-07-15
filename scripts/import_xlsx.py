"""Importir manual buat file Excel dari Dinas Pendidikan (di luar hasil scraping API).

Dipakai kalau ada update data yang cuma tersedia lewat file Excel (bukan API),
misal statistik per kecamatan yang diminta langsung ke dinas. Mendukung 3 bentuk
file: daftar sekolah, jumlah siswa per kecamatan, dan jumlah PTK per kecamatan.
Bentuk file dideteksi otomatis dari nama kolom di header.

Contoh pemakaian:
    python scripts/import_xlsx.py "Data Sekolah Dasar.xlsx" --jenjang SD --tahun 2025 --semester 1
    python scripts/import_xlsx.py "Statistik Jumlah PTK...Ganjil SD.xlsx" --jenjang SD
    python scripts/import_xlsx.py "Statistik Jumlah Siswa...Genap SD.xlsx" --jenjang SD

Semester bisa dideteksi otomatis dari nama file kalau ada kata "ganjil"/"genap",
kalau tidak ada, wajib dikasih lewat --semester.
"""

import argparse
import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from python_calamine import CalamineWorkbook

from src.supabase_client import upsert_batch

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def clean_text(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def clean_upper(value) -> str | None:
    text = clean_text(value)
    return text.upper() if text else None


def clean_area_name(value) -> str | None:
    """Buang prefix 'Kec.'/'Kel.' dan samakan ke uppercase."""
    text = clean_text(value)
    if not text:
        return None
    text = re.sub(r"^(kec\.?|kelurahan|kel\.?)\s*", "", text, flags=re.IGNORECASE)
    return text.strip().upper()


def to_int(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def detect_semester_from_filename(filename: str) -> int | None:
    lower = filename.lower()
    if "ganjil" in lower:
        return 1
    if "genap" in lower:
        return 2
    return None


def read_rows(path: Path) -> list[list]:
    workbook = CalamineWorkbook.from_path(str(path))
    sheet = workbook.get_sheet_by_name(workbook.sheet_names[0])
    return sheet.to_python()


def find_header(rows: list[list]) -> tuple[int, dict[str, int]]:
    """Cari baris header (baris pertama yang punya >= 3 kolom berisi teks)."""
    for i, row in enumerate(rows):
        filled = [str(c).strip() for c in row if c not in (None, "")]
        if len(filled) >= 3:
            columns = {str(c).strip().upper(): idx for idx, c in enumerate(row) if c not in (None, "")}
            return i, columns
    raise ValueError("Tidak ketemu baris header di file ini")


def import_sekolah(rows: list, header_idx: int, columns: dict, jenjang: str, tahun: int, semester: int, sumber_file: str) -> int:
    telp_key = next((k for k in ("NO. TELP", "NO TELP") if k in columns), None)

    out_rows = []
    for row in rows[header_idx + 1 :]:
        if not row or not row[columns["NPSN"]]:
            continue
        npsn = to_int(row[columns["NPSN"]])
        if npsn is None:
            continue
        out_rows.append(
            {
                "jenjang": jenjang,
                "npsn": npsn,
                "nama_sekolah": clean_text(row[columns["NAMA SEKOLAH"]]),
                "status_sekolah": clean_upper(row[columns["STATUS SEKOLAH"]]),
                "no_telp": clean_text(row[columns[telp_key]]) if telp_key else None,
                "alamat": clean_text(row[columns["ALAMAT"]]) if "ALAMAT" in columns else None,
                "kelurahan": clean_area_name(row[columns["KELURAHAN"]]) if "KELURAHAN" in columns else None,
                "kecamatan": clean_area_name(row[columns["KECAMATAN"]]) if "KECAMATAN" in columns else None,
                "semester_ajaran": semester,
                "tahun": tahun,
                "sumber_file": sumber_file,
            }
        )
    return upsert_batch("import_sekolah", out_rows, "jenjang,npsn,tahun,semester_ajaran")


def import_siswa_kecamatan(rows: list, header_idx: int, columns: dict, jenjang: str, tahun: int | None, semester: int | None, sumber_file: str) -> int:
    out_rows = []
    for row in rows[header_idx + 1 :]:
        if not row or row[columns["KECAMATAN SEKOLAH"]] is None:
            continue

        row_tahun, row_semester = tahun, semester
        if "SEMESTER" in columns:
            raw = to_int(row[columns["SEMESTER"]])
            if raw is not None:
                row_tahun = raw // 10
                row_semester = raw % 10

        if row_tahun is None or row_semester is None:
            continue

        out_rows.append(
            {
                "jenjang": jenjang,
                "kecamatan": clean_area_name(row[columns["KECAMATAN SEKOLAH"]]),
                "kelurahan": clean_area_name(row[columns["KELURAHAN SEKOLAH"]]) if "KELURAHAN SEKOLAH" in columns else None,
                "status_sekolah": clean_upper(row[columns["STATUS SEKOLAH"]]),
                "jumlah_laki": to_int(row[columns["JUMLAH LAKI LAKI"]]) or 0,
                "jumlah_perempuan": to_int(row[columns["JUMLAH PEREMPUAN"]]) or 0,
                "semester_ajaran": row_semester,
                "tahun": row_tahun,
                "sumber_file": sumber_file,
            }
        )
    return upsert_batch(
        "import_siswa_kecamatan", out_rows, "jenjang,kecamatan,kelurahan,status_sekolah,tahun,semester_ajaran"
    )


def import_ptk_kecamatan(rows: list, header_idx: int, columns: dict, jenjang: str, tahun: int | None, semester: int | None, sumber_file: str) -> int:
    out_rows = []
    for row in rows[header_idx + 1 :]:
        if not row or row[columns["KECAMATAN SEKOLAH"]] is None:
            continue

        row_tahun = tahun
        if "TAHUN" in columns:
            row_tahun = to_int(row[columns["TAHUN"]]) or tahun

        if row_tahun is None or semester is None:
            continue

        out_rows.append(
            {
                "jenjang": jenjang,
                "kecamatan": clean_area_name(row[columns["KECAMATAN SEKOLAH"]]),
                "status_sekolah": clean_upper(row[columns["STATUS SEKOLAH"]]),
                "jenis_ptk": clean_upper(row[columns["JENIS PTK"]]),
                "jenis_ptk_detail": clean_text(row[columns["JENIS PTK DETAIL"]]) if "JENIS PTK DETAIL" in columns else None,
                "status_kepegawaian": clean_upper(row[columns["STATUS KEPEGAWAIAN"]]),
                "status_kepegawaian_detail": clean_text(row[columns["STATUS KEPEGAWAIAN DETAIL"]])
                if "STATUS KEPEGAWAIAN DETAIL" in columns
                else None,
                "jumlah_ptk": to_int(row[columns["JUMLAH PTK"]]) or 0,
                "semester_ajaran": semester,
                "tahun": row_tahun,
                "sumber_file": sumber_file,
            }
        )
    return upsert_batch(
        "import_ptk_kecamatan",
        out_rows,
        "jenjang,kecamatan,status_sekolah,jenis_ptk,jenis_ptk_detail,status_kepegawaian,status_kepegawaian_detail,tahun,semester_ajaran",
    )


def run(path: Path, jenjang: str, tahun: int | None, semester: int | None) -> None:
    rows = read_rows(path)
    header_idx, columns = find_header(rows)
    sumber_file = path.name

    if semester is None:
        semester = detect_semester_from_filename(path.name)

    if "NPSN" in columns:
        if tahun is None or semester is None:
            raise ValueError("File daftar sekolah tidak punya kolom tahun/semester, wajib dikasih lewat --tahun dan --semester")
        count = import_sekolah(rows, header_idx, columns, jenjang, tahun, semester, sumber_file)
        logger.info("import_sekolah: %d baris di-upsert", count)
    elif "JENIS PTK" in columns:
        if semester is None:
            raise ValueError("Tidak bisa deteksi semester dari nama file, kasih manual lewat --semester")
        count = import_ptk_kecamatan(rows, header_idx, columns, jenjang, tahun, semester, sumber_file)
        logger.info("import_ptk_kecamatan: %d baris di-upsert", count)
    elif "JUMLAH LAKI LAKI" in columns:
        count = import_siswa_kecamatan(rows, header_idx, columns, jenjang, tahun, semester, sumber_file)
        logger.info("import_siswa_kecamatan: %d baris di-upsert", count)
    else:
        raise ValueError(f"Bentuk file tidak dikenali. Kolom yang ketemu: {list(columns.keys())}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import file Excel Dinas Pendidikan ke Supabase")
    parser.add_argument("file", type=Path, help="Path ke file .xlsx")
    parser.add_argument("--jenjang", required=True, choices=["SD", "SMP"])
    parser.add_argument("--tahun", type=int, default=None)
    parser.add_argument("--semester", type=int, default=None, choices=[1, 2])
    args = parser.parse_args()

    run(args.file, args.jenjang, args.tahun, args.semester)


if __name__ == "__main__":
    main()
