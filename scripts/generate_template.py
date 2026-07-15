"""Generate template Excel buat import manual, satu bentuk dipakai bareng SD & SMP.

Kolomnya sengaja disamain persis sama nama kolom yang dikenali scripts/import_xlsx.py,
jadi file yang diisi dari template ini bisa langsung diimport tanpa ubah apa-apa.
"""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "templates"

HEADER_FONT = Font(bold=True)


def write_sheet(path: Path, headers: list[str], example_row: list) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(headers)
    for cell in ws[1]:
        cell.font = HEADER_FONT
    ws.append(example_row)
    for col in ws.columns:
        width = max(len(str(c.value)) for c in col if c.value is not None)
        ws.column_dimensions[col[0].column_letter].width = max(width + 2, 12)
    OUTPUT_DIR.mkdir(exist_ok=True)
    wb.save(path)
    print("dibuat:", path)


def main() -> None:
    write_sheet(
        OUTPUT_DIR / "template_daftar_sekolah.xlsx",
        ["NAMA SEKOLAH", "STATUS SEKOLAH", "NPSN", "NO. TELP", "ALAMAT", "KELURAHAN", "KECAMATAN"],
        ["SDN CONTOH 01", "Negeri", 20200001, "0221234567", "Jl. Contoh No. 1", "Contoh Kelurahan", "Kec. Contoh"],
    )

    write_sheet(
        OUTPUT_DIR / "template_jumlah_siswa.xlsx",
        ["KECAMATAN SEKOLAH", "KELURAHAN SEKOLAH", "STATUS SEKOLAH", "JUMLAH LAKI LAKI", "JUMLAH PEREMPUAN"],
        ["Kec. Contoh", "Contoh Kelurahan", "Negeri", 100, 90],
    )

    write_sheet(
        OUTPUT_DIR / "template_jumlah_ptk.xlsx",
        [
            "STATUS SEKOLAH",
            "KECAMATAN SEKOLAH",
            "JENIS PTK",
            "JENIS PTK DETAIL",
            "STATUS KEPEGAWAIAN",
            "STATUS KEPEGAWAIAN DETAIL",
            "JUMLAH PTK",
        ],
        ["Negeri", "Kec. Contoh", "Guru", "Guru Kelas", "ASN", "PNS", 12],
    )


if __name__ == "__main__":
    main()
