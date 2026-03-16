"""
Serviço de Pedidos: cria pedidos (persistidos em SQLite), publica PedidoCriado,
consome estoque.reservado e pagamentos.processados; atualiza status e publica PedidoConfirmado.
"""
import json
import logging
import os
import threading
import uuid
from flask import Flask, request, jsonify
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

from db import (
    init_db,
    insert_order,
    get_order,
    get_all_orders,
    update_order_status,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pedidos")

app = Flask(__name__)
KAFKA_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")

TOPIC_PEDIDOS_CRIADOS = "pedidos.criados"
TOPIC_ESTOQUE_RESERVADO = "estoque.reservado"
TOPIC_PAGAMENTOS_PROCESSADOS = "pagamentos.processados"
TOPIC_PEDIDOS_CONFIRMADOS = "pedidos.confirmados"


def get_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        retries=3,
    )


def publish_pedido_criado(producer, order_id: str, payload: dict):
    producer.send(
        TOPIC_PEDIDOS_CRIADOS,
        key=order_id,
        value={
            "eventType": "PedidoCriado",
            "orderId": order_id,
            "customerId": payload["customerId"],
            "items": payload["items"],
            "total": payload["total"],
        },
    )
    producer.flush()
    logger.info("Publicado PedidoCriado orderId=%s", order_id)


def publish_pedido_confirmado(producer, order_id: str, customer_id: str, total: float):
    producer.send(
        TOPIC_PEDIDOS_CONFIRMADOS,
        key=order_id,
        value={
            "eventType": "PedidoConfirmado",
            "orderId": order_id,
            "customerId": customer_id,
            "total": total,
        },
    )
    producer.flush()
    logger.info("Publicado PedidoConfirmado orderId=%s", order_id)


def consume_estoque_reservado():
    consumer = KafkaConsumer(
        TOPIC_ESTOQUE_RESERVADO,
        bootstrap_servers=KAFKA_SERVERS,
        group_id="pedidos-estoque",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
    )
    for message in consumer:
        try:
            data = message.value
            event_type = data.get("eventType", "")
            order_id = data.get("orderId")
            if not order_id:
                continue
            if get_order(order_id) is None:
                continue
            if event_type == "EstoqueInsuficiente":
                update_order_status(order_id, "cancelado", "estoque_insuficiente")
                logger.info("Pedido %s cancelado: estoque insuficiente", order_id)
        except Exception as e:
            logger.exception("Erro ao processar estoque.reservado: %s", e)


def consume_pagamentos_processados():
    consumer = KafkaConsumer(
        TOPIC_PAGAMENTOS_PROCESSADOS,
        bootstrap_servers=KAFKA_SERVERS,
        group_id="pedidos-pagamentos",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
    )
    producer = get_producer()
    for message in consumer:
        try:
            data = message.value
            approved = data.get("approved", False)
            order_id = data.get("orderId")
            if not order_id:
                continue
            o = get_order(order_id)
            if o is None:
                continue
            if approved:
                update_order_status(order_id, "confirmado")
                publish_pedido_confirmado(
                    producer, order_id, o["customerId"], o["total"]
                )
            else:
                update_order_status(order_id, "cancelado", "pagamento_recusado")
                logger.info("Pedido %s cancelado: pagamento recusado", order_id)
        except Exception as e:
            logger.exception("Erro ao processar pagamentos.processados: %s", e)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "pedidos"}), 200


@app.route("/pedidos", methods=["GET"])
def listar_pedidos():
    return jsonify(get_all_orders()), 200


@app.route("/pedidos", methods=["POST"])
def criar_pedido():
    body = request.get_json() or {}
    customer_id = body.get("customerId") or "cliente-anonimo"
    items = body.get("items") or [{"productId": "P1", "quantity": 1}]
    total = float(body.get("total", 0))
    if total <= 0:
        total = sum(item.get("quantity", 1) * 10.0 for item in items)

    order_id = str(uuid.uuid4())
    insert_order(order_id, customer_id, items, total)
    try:
        producer = get_producer()
        publish_pedido_criado(
            producer,
            order_id,
            {"customerId": customer_id, "items": items, "total": total},
        )
    except KafkaError as e:
        logger.exception("Falha ao publicar PedidoCriado: %s", e)
        update_order_status(order_id, "erro_kafka")
        return jsonify({"error": "Falha ao publicar evento"}), 503
    return jsonify({"orderId": order_id, "status": "criado"}), 201


@app.route("/pedidos/<order_id>", methods=["GET"])
def obter_pedido(order_id):
    o = get_order(order_id)
    if o is None:
        return jsonify({"error": "Pedido não encontrado"}), 404
    return jsonify(o), 200


def main():
    init_db()
    t1 = threading.Thread(target=consume_estoque_reservado, daemon=True)
    t2 = threading.Thread(target=consume_pagamentos_processados, daemon=True)
    t1.start()
    t2.start()
    port = int(os.environ.get("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
