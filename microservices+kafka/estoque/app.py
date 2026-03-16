"""
Serviço de Estoque: consome PedidoCriado, reserva itens (em memória),
publica EstoqueReservado ou EstoqueInsuficiente em estoque.reservado.
"""
import json
import logging
import os
import threading
from flask import Flask, jsonify
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("estoque")

app = Flask(__name__)
KAFKA_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")

# Estoque em memória: productId -> quantidade disponível; reservas: orderId -> { productId -> qty }
inventory = {"P1": 100, "P2": 50, "P3": 30}
reservations = {}
lock = threading.Lock()

TOPIC_PEDIDOS_CRIADOS = "pedidos.criados"
TOPIC_ESTOQUE_RESERVADO = "estoque.reservado"


def get_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        retries=3,
    )


def try_reserve(order_id: str, items: list) -> tuple[bool, dict]:
    """Tenta reservar itens. Retorna (sucesso, payload do evento)."""
    with lock:
        for item in items:
            pid = item.get("productId", "P1")
            qty = int(item.get("quantity", 1))
            if inventory.get(pid, 0) < qty:
                return False, {
                    "eventType": "EstoqueInsuficiente",
                    "orderId": order_id,
                    "reserved": False,
                    "reason": f"Produto {pid} sem quantidade suficiente",
                }
        # Efetua reserva
        reservations[order_id] = {}
        for item in items:
            pid = item.get("productId", "P1")
            qty = int(item.get("quantity", 1))
            inventory[pid] = inventory.get(pid, 0) - qty
            reservations[order_id][pid] = reservations[order_id].get(pid, 0) + qty
        return True, {
            "eventType": "EstoqueReservado",
            "orderId": order_id,
            "reserved": True,
            "items": items,
        }


def consume_pedidos_criados():
    consumer = KafkaConsumer(
        TOPIC_PEDIDOS_CRIADOS,
        bootstrap_servers=KAFKA_SERVERS,
        group_id="estoque-pedidos",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
    )
    producer = get_producer()
    for message in consumer:
        try:
            data = message.value
            if data.get("eventType") != "PedidoCriado":
                continue
            order_id = data.get("orderId")
            items = data.get("items", [])
            if not order_id or not items:
                continue
            ok, payload = try_reserve(order_id, items)
            producer.send(TOPIC_ESTOQUE_RESERVADO, key=order_id, value=payload)
            producer.flush()
            logger.info(
                "Estoque %s para pedido %s", "reservado" if ok else "insuficiente", order_id
            )
        except Exception as e:
            logger.exception("Erro ao processar pedidos.criados: %s", e)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "estoque"}), 200


@app.route("/estoque", methods=["GET"])
def listar_estoque():
    with lock:
        return jsonify({"inventory": dict(inventory), "reservations": dict(reservations)}), 200


def main():
    t = threading.Thread(target=consume_pedidos_criados, daemon=True)
    t.start()
    port = int(os.environ.get("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
