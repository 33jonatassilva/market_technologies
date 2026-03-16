"""Persistência SQLite da config do serviço Pagamentos (simularRejeicao)."""
import os
import sqlite3
import threading

DATA_DIR = os.environ.get("DATA_DIR", "/data")
DB_PATH = os.path.join(DATA_DIR, "pagamentos.db")
_lock = threading.Lock()


def _conn():
    os.makedirs(DATA_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH, timeout=15.0)


def init_db():
    with _lock:
        conn = _conn()
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)"
            )
            conn.commit()
        finally:
            conn.close()


def get_simular_rejeicao(default: bool) -> bool:
    with _lock:
        conn = _conn()
        try:
            cur = conn.execute(
                "SELECT value FROM config WHERE key = 'simularRejeicao'"
            )
            row = cur.fetchone()
            if row is None:
                return default
            return row[0].lower() in ("1", "true", "yes")
        finally:
            conn.close()


def set_simular_rejeicao(value: bool):
    with _lock:
        conn = _conn()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO config (key, value) VALUES ('simularRejeicao', ?)",
                ("true" if value else "false",),
            )
            conn.commit()
        finally:
            conn.close()
