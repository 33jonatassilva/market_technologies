"""Persistência SQLite dos Pedidos."""
import json
import os
import sqlite3
import threading

DATA_DIR = os.environ.get("DATA_DIR", "/data")
DB_PATH = os.path.join(DATA_DIR, "pedidos.db")
_lock = threading.Lock()


def _conn():
    os.makedirs(DATA_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH, timeout=15.0)


def init_db():
    with _lock:
        conn = _conn()
        try:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    items TEXT NOT NULL,
                    total REAL NOT NULL,
                    status TEXT NOT NULL,
                    motivo TEXT
                )"""
            )
            conn.commit()
        finally:
            conn.close()


def insert_order(order_id: str, customer_id: str, items: list, total: float):
    with _lock:
        conn = _conn()
        try:
            conn.execute(
                "INSERT INTO orders (order_id, customer_id, items, total, status, motivo) VALUES (?, ?, ?, ?, 'criado', NULL)",
                (order_id, customer_id, json.dumps(items), total),
            )
            conn.commit()
        finally:
            conn.close()


def get_order(order_id: str) -> dict | None:
    with _lock:
        conn = _conn()
        try:
            cur = conn.execute(
                "SELECT order_id, customer_id, items, total, status, motivo FROM orders WHERE order_id = ?",
                (order_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "orderId": row[0],
                "customerId": row[1],
                "items": json.loads(row[2]),
                "total": row[3],
                "status": row[4],
                "motivo": row[5],
            }
        finally:
            conn.close()


def get_all_orders() -> list:
    with _lock:
        conn = _conn()
        try:
            cur = conn.execute(
                "SELECT order_id, customer_id, items, total, status, motivo FROM orders ORDER BY order_id"
            )
            out = []
            for row in cur:
                out.append({
                    "orderId": row[0],
                    "customerId": row[1],
                    "items": json.loads(row[2]),
                    "total": row[3],
                    "status": row[4],
                    "motivo": row[5],
                })
            return out
        finally:
            conn.close()


def update_order_status(order_id: str, status: str, motivo: str = None):
    with _lock:
        conn = _conn()
        try:
            if motivo is not None:
                conn.execute(
                    "UPDATE orders SET status = ?, motivo = ? WHERE order_id = ?",
                    (status, motivo, order_id),
                )
            else:
                conn.execute(
                    "UPDATE orders SET status = ? WHERE order_id = ?",
                    (status, order_id),
                )
            conn.commit()
        finally:
            conn.close()
