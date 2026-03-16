"""Persistência SQLite do buffer de notificações."""
import os
import sqlite3
import threading

DATA_DIR = os.environ.get("DATA_DIR", "/data")
DB_PATH = os.path.join(DATA_DIR, "notificacoes.db")
BUFFER_SIZE = 50
_lock = threading.Lock()


def _conn():
    os.makedirs(DATA_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH, timeout=15.0)


def init_db():
    with _lock:
        conn = _conn()
        try:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    customer_id TEXT NOT NULL,
                    total REAL NOT NULL,
                    created_at TEXT NOT NULL
                )"""
            )
            conn.commit()
        finally:
            conn.close()


def add_notification(order_id: str, customer_id: str, total: float, created_at: str):
    with _lock:
        conn = _conn()
        try:
            conn.execute(
                "INSERT INTO notifications (order_id, customer_id, total, created_at) VALUES (?, ?, ?, ?)",
                (order_id, customer_id, total, created_at),
            )
            n = conn.execute("SELECT COUNT(*) FROM notifications").fetchone()[0]
            if n > BUFFER_SIZE:
                conn.execute(
                    "DELETE FROM notifications WHERE id IN (SELECT id FROM notifications ORDER BY id ASC LIMIT ?)",
                    (n - BUFFER_SIZE,),
                )
            conn.commit()
        finally:
            conn.close()


def get_notifications() -> list:
    with _lock:
        conn = _conn()
        try:
            cur = conn.execute(
                "SELECT order_id, customer_id, total, created_at FROM notifications ORDER BY id DESC LIMIT ?",
                (BUFFER_SIZE,),
            )
            return [
                {
                    "orderId": row[0],
                    "customerId": row[1],
                    "total": row[2],
                    "timestamp": row[3],
                }
                for row in cur
            ]
        finally:
            conn.close()
