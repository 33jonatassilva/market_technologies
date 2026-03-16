"""
Serviço de Estoque: consome PedidoCriado, reserva itens (persistido em SQLite),
publica EstoqueReservado ou EstoqueInsuficiente em estoque.reservado.
"""
import json
import logging
import os
import threading
from flask import Flask, jsonify
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

from db import init_db, get_inventory_and_reservations, try_reserve as db_try_reserve

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("estoque")

app = Flask(__name__)
KAFKA_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")

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
            ok, payload = db_try_reserve(order_id, items)
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
    inventory, reservations = get_inventory_and_reservations()
    return jsonify({"inventory": inventory, "reservations": reservations}), 200


def main():
    init_db()
    t = threading.Thread(target=consume_pedidos_criados, daemon=True)
    t.start()
    port = int(os.environ.get("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
