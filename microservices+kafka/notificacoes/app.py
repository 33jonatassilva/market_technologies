"""
Serviço de Notificações: consome PedidoConfirmado de pedidos.confirmados,
simula envio de e-mail/SMS (log em stdout). Buffer de notificações persistido em SQLite.
"""
import json
import logging
import os
import threading
from datetime import datetime
from flask import Flask, jsonify
from kafka import KafkaConsumer

from db import init_db, add_notification, get_notifications

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notificacoes")

app = Flask(__name__)
KAFKA_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")

TOPIC_PEDIDOS_CONFIRMADOS = "pedidos.confirmados"


def consume_pedidos_confirmados():
    consumer = KafkaConsumer(
        TOPIC_PEDIDOS_CONFIRMADOS,
        bootstrap_servers=KAFKA_SERVERS,
        group_id="notificacoes-pedidos",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
    )
    for message in consumer:
        try:
            data = message.value
            if data.get("eventType") != "PedidoConfirmado":
                continue
            order_id = data.get("orderId")
            customer_id = data.get("customerId", "cliente")
            total = data.get("total", 0)
            created_at = datetime.utcnow().isoformat() + "Z"
            add_notification(order_id, customer_id, total, created_at)
            logger.info(
                "[NOTIFICAÇÃO] Pedido confirmado - orderId=%s customerId=%s total=%s -> E-mail/SMS enviado (simulado)",
                order_id,
                customer_id,
                total,
            )
        except Exception as e:
            logger.exception("Erro ao processar pedidos.confirmados: %s", e)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "notificacoes"}), 200


@app.route("/notificacoes", methods=["GET"])
def listar_notificacoes():
    notifications = get_notifications()
    return jsonify({"notifications": notifications}), 200


def main():
    init_db()
    t = threading.Thread(target=consume_pedidos_confirmados, daemon=True)
    t.start()
    port = int(os.environ.get("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
