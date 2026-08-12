# Bandung City Dashboard - Data Pipeline

Pipeline Python untuk mengambil data Kota Bandung (pendidikan SMP & SD, rumah sakit,
kependudukan, persampahan, kolam retensi) dari
[opendata.bandung.go.id](https://opendata.bandung.go.id) dan menyimpannya ke Supabase.

## Sumber Data

Data diambil dari 5 dinas/instansi berbeda. Base URL-nya sama, cuma beda nama dinas:
`https://opendata.bandung.go.id/api/bigdata/<nama_dinas>/<endpoint>`

| Dataset | Dinas | Endpoint | Tabel Supabase |
|---|---|---|---|
| Daftar SMP (negeri & swasta) | dinas_pendidikan | `sekolah_menengah_pertama_di_kota_bandung` | `smp_sekolah` |
| Jumlah peserta didik SMP per sekolah & jenis kelamin | dinas_pendidikan | `jumlah_peserta_didik_di_sekolah_menengah_pertama_kota` | `smp_peserta_didik` |
| Jumlah guru & tenaga kependidikan (PTK) SMP | dinas_pendidikan | `jumlah_guru_dan_tenaga_kependidikan_ptk_sekolah_menen` | `smp_ptk` |
| Daftar SD (negeri & swasta) | dinas_pendidikan | `sekolah_dasar_di_kota_bandung` | `sd_sekolah` |
| Jumlah peserta didik SD per sekolah & jenis kelamin | dinas_pendidikan | `jumlah_peserta_didik_di_sekolah_dasar_kota_bandung_1` | `sd_peserta_didik` |
| Jumlah guru & tenaga kependidikan (PTK) SD | dinas_pendidikan | `jmlh_gr_tng_kpnddkn_ptk_sklh_dsr_d_kt_bndng` | `sd_ptk` |
| Rumah sakit | dinas_kesehatan | `rumah_sakit_di_kota_bandung_1` | `rumah_sakit` |
| Kepadatan penduduk per kecamatan | dinas_kependudukan_dan_pencatatan_sipil | `jumlah_kepadatan_penduduk_di_kota_bandung_3` | `kepadatan_penduduk` |
| Jumlah kepala keluarga per kecamatan, per jenis kelamin | dinas_kependudukan_dan_pencatatan_sipil | `jumlah_kepala_keluarga_di_kota_bandung_berdasarkan__3` | `kepala_keluarga` |
| Luas wilayah per kecamatan | badan_pusat_statistik_kota_bandung | `luas_kecamatan_di_kota_bandung` | `luas_kecamatan` |
| Produksi sampah menurut jenisnya (kota-wide) | dinas_lingkungan_hidup | `jumlah_produksi_sampah_menurut_jenisnya_di_kota_ban_2` | `sampah_produksi` |
| Ritasi pengangkutan sampah per bulan | dinas_lingkungan_hidup | `jumlah_ritasi_pengangkutan_sampah_di_kota_bandung_2` | `sampah_ritasi` |
| Capaian penanganan sampah per bulan | dinas_lingkungan_hidup | `jumlah_capaian_penanganan_sampah_di_kota_bandung_1` | `sampah_capaian` |
| Kompensasi penanganan sampah per bulan | dinas_lingkungan_hidup | `jumlah_kompensasi_penanganan_sampah_di_kota_bandung_1` | `sampah_kompensasi` |
| Jumlah kolam retensi per kecamatan/sub-DAS | dinas_sumber_daya_air_dan_bina_marga | `jumlah_kolam_retensi_di_kota_bandung_2` | `kolam_retensi` |
| Volume tampungan kolam retensi | dinas_sumber_daya_air_dan_bina_marga | `volume_tampungan_kolam_retensi_di_kota_bandung_1` | `kolam_retensi_volume` |

Catatan: dataset guru/PTK (SMP maupun SD) tidak menyediakan data umur, jadi kolom
umur tidak ada di tabel `smp_ptk`/`sd_ptk`.

Catatan lain: dataset SD tipe datanya kurang konsisten dari sumbernya (`npsn`,
`tahun`, `semester_ajaran`, `longitude` kadang dikirim sebagai angka, kadang
sebagai teks). Pipeline sudah nge-cast semuanya (lihat `to_int`/`to_float` di
`src/pipelines/common.py`), jadi ini bukan hal yang perlu dikhawatirkan.

Catatan soal rumah sakit: endpoint yang benar itu `rumah_sakit_di_kota_bandung_1`
(ada suffix `_1`), bukan `rumah_sakit_di_kota_bandung` yang lebih pendek namanya.
Endpoint yang pendek itu versi lama, datanya lebih sedikit (35 baris) dan nggak
punya `latitude`/`longitude`/`tahun`. Endpoint `_1` punya semuanya, plus dua
kolom kategori yang beda maknanya jadi jangan ketuker:
- `jenis_rs`: spesialisasi RS (Rumah Sakit Umum, RS Khusus Ibu dan Anak, dst)
- `status_rs`: kepemilikan (`PEMERINTAH DAERAH`, `PEMERINTAH PUSAT`, `SWASTA`, `TNI/POLRI`)

Kalau butuh KPI "Total RS Negeri", jumlahkan `status_rs` selain `SWASTA`.

Pipeline ambil semua histori yang tersedia dari sumbernya: tahun 2023, 2024, dan 2025.

Catatan soal data sampah: semuanya data kota-wide (Kota Bandung), gak ada dimensi
kecamatan di sumbernya. `sampah_produksi` cuma punya `jenis_sampah` + `tahun` (gak ada
`bulan`). `sampah_ritasi`, `sampah_capaian`, `sampah_kompensasi` punya `bulan` + `tahun`.

## Kolom per Tabel

`npsn` disimpan di semua tabel sebagai kunci unik internal (bukan untuk dipakai tim
dashboard), supaya data per sekolah tidak saling menimpa saat upsert.

- `smp_sekolah` / `sd_sekolah`: `kemendagri_nama_kecamatan`, `status_sekolah`, `latitude`, `longitude`, `semester_ajaran`, `tahun`
- `smp_peserta_didik` / `sd_peserta_didik`: `kemendagri_nama_kecamatan`, `jenis_kelamin`, `jumlah_siswa`, `satuan`, `semester_ajaran`, `tahun`
- `smp_ptk` / `sd_ptk`: `kemendagri_nama_kecamatan`, `jenis_ptk`, `status_kepegawaian`, `jumlah_ptk`, `satuan`, `semester_ajaran`, `tahun`

Catatan: tabel `*_sekolah` menyimpan `latitude`/`longitude` per sekolah untuk keperluan
peta sebaran, tapi tidak menyimpan `nama_sekolah` (tidak dibutuhkan untuk chart manapun).
Gak ada kolom `satuan` di `*_sekolah` karena gak ada kolom angka yang butuh satuan disitu.

`rumah_sakit` juga punya kunci unik internal sendiri (`sumber_id`, dari `id` di API),
dengan kolom yang dipakai tim dashboard: `bps_nama_kecamatan`, `jenis_rs`, `status_rs`,
`kelas`, `latitude`, `longitude`, `tahun`. Kecamatan-nya pakai versi BPS (`bps_nama_kecamatan`),
bukan kemendagri seperti tabel sekolah, karena diminta begitu. Gak ada kolom `satuan`
karena datasetnya gak punya kolom angka.

`kepadatan_penduduk`, `kepala_keluarga`, dan `luas_kecamatan` juga pakai `bps_nama_kecamatan`
dan `sumber_id` (kunci unik internal), semuanya data per kecamatan (bukan per sekolah):

- `kepadatan_penduduk`: `bps_nama_kecamatan`, `kepadatan_penduduk`, `satuan` (JIWA/KM2), `tahun`
- `kepala_keluarga`: `bps_nama_kecamatan`, `jenis_kelamin`, `jumlah_kk`, `satuan` (KEPALA KELUARGA), `tahun`
- `luas_kecamatan`: `bps_nama_kecamatan`, `luas_wilayah`, `satuan` (KILOMETER PERSEGI), `tahun` (cuma ada tahun 2022 di sumbernya)

Tabel `sampah_*` juga pakai `sumber_id` (kunci unik internal), tapi gak ada `bps_nama_kecamatan`
karena datanya kota-wide:

- `sampah_produksi`: `jenis_sampah`, `produksi_sampah`, `satuan` (TON/HARI), `tahun`
- `sampah_ritasi`: `bulan`, `jumlah_ritasi`, `satuan` (RIT), `tahun`
- `sampah_capaian`: `bulan`, `jumlah_sampah`, `satuan` (TON), `tahun`
- `sampah_kompensasi`: `bulan`, `kategori_kompensasi`, `jumlah_kompensasi`, `satuan` (RUPIAH), `tahun`

`kolam_retensi` dan `kolam_retensi_volume` juga pakai `bps_nama_kecamatan` + `sumber_id`:

- `kolam_retensi`: `bps_nama_kecamatan`, `nama`, `sub_das`, `nama_sungai`, `jumlah_kolam`, `satuan` (KOLAM), `tahun`
- `kolam_retensi_volume`: `bps_nama_kecamatan`, `nama`, `sub_das`, `nama_sungai`, `volume_tampungan_total`, `satuan` (METER KUBIK), `tahun`

Kolom `satuan` diambil langsung dari API (bukan di-hardcode), tapi nilainya selalu
konsisten satu nilai per tabel karena memang begitu adanya di sumber datanya.

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
    rumah_sakit.py       pipeline daftar rumah sakit
    kepadatan_penduduk.py  pipeline kepadatan penduduk per kecamatan
    kepala_keluarga.py     pipeline jumlah kepala keluarga per kecamatan
    luas_kecamatan.py      pipeline luas wilayah per kecamatan
    sampah_produksi.py     pipeline produksi sampah menurut jenisnya
    sampah_ritasi.py       pipeline ritasi pengangkutan sampah
    sampah_capaian.py      pipeline capaian penanganan sampah
    sampah_kompensasi.py   pipeline kompensasi penanganan sampah
    kolam_retensi.py       pipeline jumlah kolam retensi
    kolam_retensi_volume.py pipeline volume tampungan kolam retensi
  main.py                entrypoint, jalankan semua pipeline
scripts/
  import_xlsx.py         importir manual buat file Excel dari dinas
  generate_template.py   generator template Excel kosong
templates/
  template_daftar_sekolah.xlsx
  template_jumlah_siswa.xlsx
  template_jumlah_ptk.xlsx
supabase/
  schema.sql             DDL untuk 19 tabel (16 hasil scraping + 3 import manual)
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
- `rumah_sakit` / `kepadatan_penduduk` / `kepala_keluarga` / `luas_kecamatan` / `sampah_*` / `kolam_retensi*`: `(sumber_id)`

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
