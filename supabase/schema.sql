-- Schema untuk pipeline data pendidikan SMP Kota Bandung
-- Sumber: opendata.bandung.go.id (API Dinas Pendidikan)
-- Kolom dibatasi hanya yang dipakai untuk metrik & chart dashboard.
-- npsn tetap disimpan sebagai kunci unik supaya upsert per sekolah tidak
-- saling menimpa, meski tidak ditampilkan sebagai data ke tim dashboard.

create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- =========================================================
-- 1. Daftar SMP Kota Bandung (negeri & swasta)
-- =========================================================
drop table if exists smp_sekolah;
create table smp_sekolah (
  id bigint generated always as identity primary key,
  npsn bigint not null,
  kemendagri_nama_kecamatan text,
  status_sekolah text not null check (status_sekolah in ('NEGERI', 'SWASTA')),
  semester_ajaran smallint not null,
  tahun smallint not null,
  scraped_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (npsn, tahun, semester_ajaran)
);

create index idx_smp_sekolah_kecamatan on smp_sekolah (kemendagri_nama_kecamatan);
create index idx_smp_sekolah_status on smp_sekolah (status_sekolah);
create index idx_smp_sekolah_tahun on smp_sekolah (tahun, semester_ajaran);

create trigger trg_smp_sekolah_updated_at
  before update on smp_sekolah
  for each row execute function set_updated_at();

-- =========================================================
-- 2. Jumlah Peserta Didik SMP (per sekolah, per jenis kelamin)
-- =========================================================
drop table if exists smp_peserta_didik;
create table smp_peserta_didik (
  id bigint generated always as identity primary key,
  npsn bigint not null,
  kemendagri_nama_kecamatan text,
  jenis_kelamin text not null check (jenis_kelamin in ('LAKI-LAKI', 'PEREMPUAN')),
  jumlah_siswa integer not null default 0,
  semester_ajaran smallint not null,
  tahun smallint not null,
  scraped_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (npsn, jenis_kelamin, tahun, semester_ajaran)
);

create index idx_smp_peserta_didik_kecamatan on smp_peserta_didik (kemendagri_nama_kecamatan);
create index idx_smp_peserta_didik_tahun on smp_peserta_didik (tahun, semester_ajaran);

create trigger trg_smp_peserta_didik_updated_at
  before update on smp_peserta_didik
  for each row execute function set_updated_at();

-- =========================================================
-- 3. Jumlah Guru & Tenaga Kependidikan (PTK) SMP
-- Catatan: jumlah_ptk adalah total guru+kepala sekolah+tendik digabung
-- per status kepegawaian (jenis_ptk tidak disimpan terpisah).
-- =========================================================
drop table if exists smp_ptk;
create table smp_ptk (
  id bigint generated always as identity primary key,
  npsn bigint not null,
  kemendagri_nama_kecamatan text,
  status_kepegawaian text not null check (status_kepegawaian in ('ASN', 'NON ASN')),
  jumlah_ptk integer not null default 0,
  semester_ajaran smallint not null,
  tahun smallint not null,
  scraped_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (npsn, status_kepegawaian, tahun, semester_ajaran)
);

create index idx_smp_ptk_kecamatan on smp_ptk (kemendagri_nama_kecamatan);
create index idx_smp_ptk_tahun on smp_ptk (tahun, semester_ajaran);

create trigger trg_smp_ptk_updated_at
  before update on smp_ptk
  for each row execute function set_updated_at();
