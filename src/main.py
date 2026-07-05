import logging
import sys

from src.pipelines import peserta_didik, ptk, sekolah

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PIPELINES = [
    ("Daftar SMP Kota Bandung", sekolah.run),
    ("Jumlah Peserta Didik SMP", peserta_didik.run),
    ("Jumlah Guru & Tenaga Kependidikan (PTK) SMP", ptk.run),
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
