import logging
import sys

from src.pipelines import (
    kepadatan_penduduk,
    kepala_keluarga,
    luas_kecamatan,
    peserta_didik,
    ptk,
    rumah_sakit,
    sampah_capaian,
    sampah_kompensasi,
    sampah_produksi,
    sampah_ritasi,
    sd_peserta_didik,
    sd_ptk,
    sd_sekolah,
    sekolah,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PIPELINES = [
    ("Daftar SMP Kota Bandung", sekolah.run),
    ("Jumlah Peserta Didik SMP", peserta_didik.run),
    ("Jumlah Guru & Tenaga Kependidikan (PTK) SMP", ptk.run),
    ("Daftar SD Kota Bandung", sd_sekolah.run),
    ("Jumlah Peserta Didik SD", sd_peserta_didik.run),
    ("Jumlah Guru & Tenaga Kependidikan (PTK) SD", sd_ptk.run),
    ("Rumah Sakit Kota Bandung", rumah_sakit.run),
    ("Kepadatan Penduduk per Kecamatan", kepadatan_penduduk.run),
    ("Jumlah Kepala Keluarga per Kecamatan", kepala_keluarga.run),
    ("Luas Wilayah per Kecamatan", luas_kecamatan.run),
    ("Produksi Sampah Menurut Jenisnya", sampah_produksi.run),
    ("Ritasi Pengangkutan Sampah", sampah_ritasi.run),
    ("Capaian Penanganan Sampah", sampah_capaian.run),
    ("Kompensasi Penanganan Sampah", sampah_kompensasi.run),
]


def main() -> int:
    failed = []
    for name, run_pipeline in PIPELINES:
        logger.info("Menjalankan pipeline: %s", name)
        try:
            count = run_pipeline()
            logger.info("Selesai: %s -> %d baris di-upsert", name, count)
        except Exception:
            logger.exception("Gagal menjalankan pipeline: %s", name)
            failed.append(name)

    if failed:
        logger.error("Pipeline gagal: %s", ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
