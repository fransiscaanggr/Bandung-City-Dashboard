# Bandung City Dashboard - Data Pipeline Pendidikan SMP & SD

Pipeline Python untuk mengambil data pendidikan SMP & SD Kota Bandung dari
[opendata.bandung.go.id](https://opendata.bandung.go.id) dan menyimpannya ke Supabase.

## Sumber Data

Semua data diambil dari API publik Dinas Pendidikan:
`https://opendata.bandung.go.id/api/bigdata/dinas_pendidikan/`

| Dataset | Endpoint | Tabel Supabase |
|---|---|---|
| Daftar SMP (negeri & swasta) | `sekolah_menengah_pertama_di_kota_bandung` | `smp_sekolah` |
| Jumlah peserta didik SMP per sekolah & jenis kelamin | `jumlah_peserta_didik_di_sekolah_menengah_pertama_kota` | `smp_peserta_didik` |
| Jumlah guru & tenaga kependidikan (PTK) SMP | `jumlah_guru_dan_tenaga_kependidikan_ptk_sekolah_menen` | `smp_ptk` |
| Daftar SD (negeri & swasta) | `sekolah_dasar_di_kota_bandung` | `sd_sekolah` |
| Jumlah peserta didik SD per sekolah & jenis kelamin | `jumlah_peserta_didik_di_sekolah_dasar_kota_bandung_1` | `sd_peserta_didik` |
| Jumlah guru & tenaga kependidikan (PTK) SD | `jmlh_gr_tng_kpnddkn_ptk_sklh_dsr_d_kt_bndng` | `sd_ptk` |

Catatan: dataset guru/PTK (SMP maupun SD) tidak menyediakan data umur, jadi kolom
umur tidak ada di tabel `smp_ptk`/`sd_ptk`.

Catatan lain: dataset SD tipe datanya kurang konsisten dari sumbernya (`npsn`,
`tahun`, `semester_ajaran`, `longitude` kadang dikirim sebagai angka, kadang
sebagai teks). Pipeline sudah nge-cast semuanya (lihat `to_int`/`to_float` di
`src/pipelines/common.py`), jadi ini bukan hal yang perlu dikhawatirkan.

## Kolom per Tabel

`npsn` disimpan di semua tabel sebagai kunci unik internal (bukan untuk dipakai tim
dashboard), supaya data per sekolah tidak saling menimpa saat upsert.

- `smp_sekolah` / `sd_sekolah`: `kemendagri_nama_kecamatan`, `status_sekolah`, `latitude`, `longitude`, `semester_ajaran`, `tahun`
- `smp_peserta_didik` / `sd_peserta_didik`: `kemendagri_nama_kecamatan`, `jenis_kelamin`, `jumlah_siswa`, `semester_ajaran`, `tahun`
- `smp_ptk` / `sd_ptk`: `kemendagri_nama_kecamatan`, `jenis_ptk`, `status_kepegawaian`, `jumlah_ptk`, `semester_ajaran`, `tahun`

Catatan: tabel `*_sekolah` menyimpan `latitude`/`longitude` per sekolah untuk keperluan
peta sebaran, tapi tidak menyimpan `nama_sekolah` (tidak dibutuhkan untuk chart manapun).

## Struktur Project

```
src/
  config.py              konfigurasi (.env)
  bandung_api.py         fetch data dari API opendata Bandung (pagination + retry)
  supabase_client.py     koneksi Supabase & helper upsert
  pipelines/
    common.py            kolom, normalisasi, & casting tipe data yang dipakai bersama
    sekolah.py           pipeline daftar SMP
    peserta_didik.py     pipeline jumlah peserta didik SMP
    ptk.py                pipeline jumlah guru & tenaga kependidikan SMP
    sd_sekolah.py        pipeline daftar SD
    sd_peserta_didik.py  pipeline jumlah peserta didik SD
    sd_ptk.py             pipeline jumlah guru & tenaga kependidikan SD
  main.py                entrypoint, jalankan semua pipeline (SMP + SD)
scripts/
  import_xlsx.py         importir manual buat file Excel dari dinas
  generate_template.py   generator template Excel kosong
templates/
  template_daftar_sekolah.xlsx
  template_jumlah_siswa.xlsx
  template_jumlah_ptk.xlsx
supabase/
  schema.sql             DDL untuk 9 tabel (6 hasil scraping + 3 import manual)
.github/workflows/
  scrape.yml             jadwal otomatis tiap 6 jam (GitHub Actions)
```

## Setup

1. Install dependency:
   ```
   pip install -r requirements.txt
   ```
2. Pastikan file `.env` berisi:
   ```
   SUPABASE_URL=...
   SUPABASE_SECRET_KEY=...
   ```
3. Jalankan `supabase/schema.sql` di Supabase SQL Editor untuk membuat tabel.

## Menjalankan Pipeline

```
python -m src.main
```

Setiap pipeline akan mengambil seluruh data dari API (dengan pagination), lalu
melakukan **upsert** ke Supabase berdasarkan kunci unik masing-masing tabel:

- `smp_sekolah` / `sd_sekolah`: `(npsn, tahun, semester_ajaran)`
- `smp_peserta_didik` / `sd_peserta_didik`: `(npsn, jenis_kelamin, tahun, semester_ajaran)`
- `smp_ptk` / `sd_ptk`: `(npsn, jenis_ptk, status_kepegawaian, tahun, semester_ajaran)`

Kalau kombinasi kunci itu sudah ada di database, baris akan di-update (bukan duplikat).
Kalau belum ada, baris baru ditambahkan. Dengan begitu proses scraping berulang aman
dijalankan tanpa perlu logic diff manual.

## Penjadwalan Otomatis

Sudah disediakan workflow GitHub Actions ([.github/workflows/scrape.yml](.github/workflows/scrape.yml))
yang menjalankan pipeline setiap 6 jam (`0 */6 * * *`). Tambahkan secret berikut di
repo GitHub (Settings > Secrets and variables > Actions):

- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY`

## Import Manual (Excel)

Kadang Dinas Pendidikan cuma ngasih data lewat file Excel, bukan lewat API. Buat
kasus ini ada `scripts/import_xlsx.py`, dipakai lewat command line:

```
python scripts/import_xlsx.py "nama_file.xlsx" --jenjang SD
python scripts/import_xlsx.py "nama_file.xlsx" --jenjang SMP --tahun 2025 --semester 1
```

Bentuk file dideteksi otomatis dari nama kolom di header, jadi 1 file bisa dikenali
sebagai salah satu dari 3 tipe:

- **Daftar sekolah** (ada kolom `NPSN`) &rarr; tabel `import_sekolah`
- **Jumlah PTK per kecamatan** (ada kolom `JENIS PTK`) &rarr; tabel `import_ptk_kecamatan`
- **Jumlah siswa per kecamatan** (ada kolom `JUMLAH LAKI LAKI`) &rarr; tabel `import_siswa_kecamatan`

`--semester` otomatis kedeteksi dari nama file kalau ada kata "ganjil"/"genap".
Kalau file daftar sekolah (biasanya nggak ada info tahun/semester sama sekali),
`--tahun` dan `--semester` wajib diisi manual.

Template kosong buat isi data baru ada di folder [templates/](templates/)
(dibuat dari `scripts/generate_template.py`), satu bentuk yang sama dipakai
buat SD maupun SMP karena jenjangnya ditentukan lewat flag `--jenjang`, bukan
dari isi file.

### Kenapa nggak nabrak data hasil scraping

Tabel `import_*` ini **terpisah total** dari tabel `smp_*`/`sd_*` hasil scraping,
soalnya levelnya beda: hasil scraping itu per sekolah (npsn dari API), sedangkan
data Excel dari dinas biasanya sudah agregat per kecamatan/kelurahan (nggak ada
npsn). Karena tabelnya beda sendiri, nggak ada mekanisme dedup rumit yang perlu
dijaga, dan data hasil scraping otomatis tetap aman biarpun proses import
dijalankan berkali-kali. Satu-satunya file yang levelnya per sekolah (daftar
sekolah dari Excel) juga tetap masuk `import_sekolah`, bukan `smp_sekolah`/
`sd_sekolah`, biar konsisten dan gampang dilacak baris mana yang asalnya dari
scraping API dan mana yang dari input manual (lihat kolom `sumber_file`).
