"""Persistência SQLite do Estoque: inventário e reservas."""
import os
import sqlite3
import threading

DATA_DIR = os.environ.get("DATA_DIR", "/data")
DB_PATH = os.path.join(DATA_DIR, "estoque.db")
_lock = threading.Lock()

DEFAULT_INVENTORY = {"P1": 100, "P2": 50, "P3": 30}


def _conn():
    os.makedirs(DATA_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH, timeout=15.0)


def init_db():
    with _lock:
        conn = _conn()
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS inventory (product_id TEXT PRIMARY KEY, quantity INTEGER NOT NULL)"
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS reservations (
                    order_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    PRIMARY KEY (order_id, product_id)
                )"""
            )
            conn.commit()
            cur = conn.execute("SELECT COUNT(*) FROM inventory")
            if cur.fetchone()[0] == 0:
                for pid, qty in DEFAULT_INVENTORY.items():
                    conn.execute(
                        "INSERT INTO inventory (product_id, quantity) VALUES (?, ?)",
                        (pid, qty),
                    )
                conn.commit()
                import logging
                logging.getLogger("estoque").info("Estoque inicializado com valores padrão")
        finally:
            conn.close()


def get_inventory_and_reservations():
    """Retorna (inventory dict, reservations dict)."""
    with _lock:
        conn = _conn()
        try:
            inv = {}
            for row in conn.execute("SELECT product_id, quantity FROM inventory"):
                inv[row[0]] = row[1]
            res = {}
            for row in conn.execute(
                "SELECT order_id, product_id, quantity FROM reservations"
            ):
                oid, pid, qty = row[0], row[1], row[2]
                if oid not in res:
                    res[oid] = {}
                res[oid][pid] = res[oid].get(pid, 0) + qty
            return inv, res
        finally:
            conn.close()


def try_reserve(order_id: str, items: list) -> tuple[bool, dict]:
    """
    Tenta reservar itens. Idempotente: se order_id já reservado, retorna (True, payload)
    sem debitar de novo. Caso contrário debita do inventário e insere em reservations.
    Retorna (sucesso, payload do evento).
    """
    with _lock:
        conn = _conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.execute(
                "SELECT 1 FROM reservations WHERE order_id = ? LIMIT 1", (order_id,)
            )
            if cur.fetchone() is not None:
                conn.rollback()
                return True, {
                    "eventType": "EstoqueReservado",
                    "orderId": order_id,
                    "reserved": True,
                    "items": items,
                    "idempotent": True,
                }
            inv = {}
            for row in conn.execute("SELECT product_id, quantity FROM inventory"):
                inv[row[0]] = row[1]
            for item in items:
                pid = item.get("productId", "P1")
                qty = int(item.get("quantity", 1))
                if inv.get(pid, 0) < qty:
                    conn.rollback()
                    return False, {
                        "eventType": "EstoqueInsuficiente",
                        "orderId": order_id,
                        "reserved": False,
                        "reason": f"Produto {pid} sem quantidade suficiente",
                    }
            for item in items:
                pid = item.get("productId", "P1")
                qty = int(item.get("quantity", 1))
                conn.execute(
                    "UPDATE inventory SET quantity = quantity - ? WHERE product_id = ?",
                    (qty, pid),
                )
                conn.execute(
                    """INSERT INTO reservations (order_id, product_id, quantity)
                       VALUES (?, ?, ?) ON CONFLICT(order_id, product_id) DO UPDATE SET
                       quantity = quantity + ?""",
                    (order_id, pid, qty, qty),
                )
            conn.commit()
            return True, {
                "eventType": "EstoqueReservado",
                "orderId": order_id,
                "reserved": True,
                "items": items,
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
