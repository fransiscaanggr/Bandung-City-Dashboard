# Bandung City Dashboard - Data Pipeline Pendidikan SMP

Pipeline Python untuk mengambil data pendidikan SMP Kota Bandung dari
[opendata.bandung.go.id](https://opendata.bandung.go.id) dan menyimpannya ke Supabase.

## Sumber Data

Semua data diambil dari API publik Dinas Pendidikan:
`https://opendata.bandung.go.id/api/bigdata/dinas_pendidikan/`

| Dataset | Endpoint | Tabel Supabase |
|---|---|---|
| Daftar SMP (negeri & swasta) | `sekolah_menengah_pertama_di_kota_bandung` | `smp_sekolah` |
| Jumlah peserta didik per sekolah & jenis kelamin | `jumlah_peserta_didik_di_sekolah_menengah_pertama_kota` | `smp_peserta_didik` |
| Jumlah guru & tenaga kependidikan (PTK) | `jumlah_guru_dan_tenaga_kependidikan_ptk_sekolah_menen` | `smp_ptk` |

Catatan: dataset guru/PTK tidak menyediakan data umur, jadi kolom umur tidak ada di tabel `smp_ptk`.

## Kolom per Tabel

`npsn` disimpan di ketiga tabel sebagai kunci unik internal (bukan untuk dipakai tim
dashboard), supaya data per sekolah tidak saling menimpa saat upsert.

- `smp_sekolah`: `kemendagri_nama_kecamatan`, `status_sekolah`, `semester_ajaran`, `tahun`
- `smp_peserta_didik`: `kemendagri_nama_kecamatan`, `jenis_kelamin`, `jumlah_siswa`, `semester_ajaran`, `tahun`
- `smp_ptk`: `kemendagri_nama_kecamatan`, `jenis_ptk`, `status_kepegawaian`, `jumlah_ptk`, `semester_ajaran`, `tahun`

Catatan: `smp_sekolah` tidak menyimpan `latitude`/`longitude`/`nama_sekolah`, jadi
chart peta sebaran sekolah tidak bisa dibuat dari tabel ini.

## Struktur Project

```
src/
  config.py              konfigurasi (.env)
  bandung_api.py         fetch data dari API opendata Bandung (pagination + retry)
  supabase_client.py     koneksi Supabase & helper upsert
  pipelines/
    common.py            kolom & normalisasi yang dipakai bersama
    sekolah.py           pipeline daftar sekolah
    peserta_didik.py     pipeline jumlah peserta didik
    ptk.py                pipeline jumlah guru & tenaga kependidikan
  main.py                entrypoint, jalankan semua pipeline
supabase/
  schema.sql             DDL untuk 3 tabel di atas
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

- `smp_sekolah`: `(npsn, tahun, semester_ajaran)`
- `smp_peserta_didik`: `(npsn, jenis_kelamin, tahun, semester_ajaran)`
- `smp_ptk`: `(npsn, jenis_ptk, status_kepegawaian, tahun, semester_ajaran)`

Kalau kombinasi kunci itu sudah ada di database, baris akan di-update (bukan duplikat).
Kalau belum ada, baris baru ditambahkan. Dengan begitu proses scraping berulang aman
dijalankan tanpa perlu logic diff manual.

## Penjadwalan Otomatis

Sudah disediakan workflow GitHub Actions ([.github/workflows/scrape.yml](.github/workflows/scrape.yml))
yang menjalankan pipeline setiap 6 jam (`0 */6 * * *`). Tambahkan secret berikut di
repo GitHub (Settings > Secrets and variables > Actions):

- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY`
