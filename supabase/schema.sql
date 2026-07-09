-- Data SMP Kota Bandung, sumbernya opendata.bandung.go.id (API Dinas Pendidikan).
-- Kolomnya sengaja dikit, cuma yang kepake buat metrik/chart dashboard.
-- npsn disimpan biar upsert per sekolah gak numpuk/timpa data sekolah lain,
-- walau kolom ini gak dipake langsung sama tim dashboard.
--
-- File ini aman di-run berkali-kali (pakai IF NOT EXISTS, gak ada drop table).
-- Kalau mau ubah struktur tabel yang udah jalan, jangan drop+recreate lagi,
-- soalnya tim dashboard udah bikin view yang nempel ke tabel-tabel ini
-- (view_smp_sekolah_bersih, view_smp_map_pivot, dll). Pakai ALTER TABLE aja.

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
create table if not exists smp_sekolah (
  id bigint generated always as identity primary key,
  npsn bigint not null,
  kemendagri_nama_kecamatan text,
  status_sekolah text not null check (status_sekolah in ('NEGERI', 'SWASTA')),
  latitude double precision,
  longitude double precision,
  semester_ajaran smallint not null,
  tahun smallint not null,
  scraped_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (npsn, tahun, semester_ajaran)
);

create index if not exists idx_smp_sekolah_kecamatan on smp_sekolah (kemendagri_nama_kecamatan);
create index if not exists idx_smp_sekolah_status on smp_sekolah (status_sekolah);
create index if not exists idx_smp_sekolah_tahun on smp_sekolah (tahun, semester_ajaran);

drop trigger if exists trg_smp_sekolah_updated_at on smp_sekolah;
create trigger trg_smp_sekolah_updated_at
  before update on smp_sekolah
  for each row execute function set_updated_at();

-- =========================================================
-- 2. Jumlah Peserta Didik SMP (per sekolah, per jenis kelamin)
-- =========================================================
create table if not exists smp_peserta_didik (
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

create index if not exists idx_smp_peserta_didik_kecamatan on smp_peserta_didik (kemendagri_nama_kecamatan);
create index if not exists idx_smp_peserta_didik_tahun on smp_peserta_didik (tahun, semester_ajaran);

drop trigger if exists trg_smp_peserta_didik_updated_at on smp_peserta_didik;
create trigger trg_smp_peserta_didik_updated_at
  before update on smp_peserta_didik
  for each row execute function set_updated_at();

-- =========================================================
-- 3. Jumlah Guru & Tenaga Kependidikan (PTK) SMP
-- =========================================================
create table if not exists smp_ptk (
  id bigint generated always as identity primary key,
  npsn bigint not null,
  kemendagri_nama_kecamatan text,
  jenis_ptk text not null check (jenis_ptk in ('GURU', 'KEPALA SEKOLAH', 'TENDIK')),
  status_kepegawaian text not null check (status_kepegawaian in ('ASN', 'NON ASN')),
  jumlah_ptk integer not null default 0,
  semester_ajaran smallint not null,
  tahun smallint not null,
  scraped_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (npsn, jenis_ptk, status_kepegawaian, tahun, semester_ajaran)
);

create index if not exists idx_smp_ptk_kecamatan on smp_ptk (kemendagri_nama_kecamatan);
create index if not exists idx_smp_ptk_tahun on smp_ptk (tahun, semester_ajaran);

drop trigger if exists trg_smp_ptk_updated_at on smp_ptk;
create trigger trg_smp_ptk_updated_at
  before update on smp_ptk
  for each row execute function set_updated_at();
