from supabase import Client, create_client

from src.config import SUPABASE_SECRET_KEY, SUPABASE_URL

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    return _client


def upsert_batch(table: str, rows: list[dict], on_conflict: str, batch_size: int = 500) -> int:
    """Upsert baris ke Supabase berdasarkan kunci unik (on_conflict).
    Baris baru akan ditambahkan, baris yang sudah ada akan diperbarui.
    """
    if not rows:
        return 0

    client = get_client()
    total = 0
    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        client.table(table).upsert(batch, on_conflict=on_conflict).execute()
        total += len(batch)
    return total
