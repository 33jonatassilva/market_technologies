"""
Serviço de Pagamentos: consome EstoqueReservado de estoque.reservado,
simula processamento e publica PagamentoAprovado ou PagamentoRecusado em pagamentos.processados.
Config (simularRejeicao) persistida em SQLite.
"""
import json
import logging
import os
import threading
import random
from flask import Flask, request, jsonify
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

from db import init_db, get_simular_rejeicao, set_simular_rejeicao

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pagamentos")

app = Flask(__name__)
KAFKA_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")

TOPIC_ESTOQUE_RESERVADO = "estoque.reservado"
TOPIC_PAGAMENTOS_PROCESSADOS = "pagamentos.processados"

_config_lock = threading.Lock()


def get_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        retries=3,
    )


def consume_estoque_reservado():
    consumer = KafkaConsumer(
        TOPIC_ESTOQUE_RESERVADO,
        bootstrap_servers=KAFKA_SERVERS,
        group_id="pagamentos-estoque",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
    )
    producer = get_producer()
    for message in consumer:
        try:
            data = message.value
            if data.get("eventType") != "EstoqueReservado" or not data.get("reserved"):
                continue
            order_id = data.get("orderId")
            if not order_id:
                continue
            simular = get_simular_rejeicao(
                os.environ.get("PAGAMENTOS_SIMULAR_REJEICAO", "false").lower() == "true"
            )
            approved = random.random() > 0.2 if simular else True
            payload = {
                "eventType": "PagamentoAprovado" if approved else "PagamentoRecusado",
                "orderId": order_id,
                "approved": approved,
            }
            producer.send(TOPIC_PAGAMENTOS_PROCESSADOS, key=order_id, value=payload)
            producer.flush()
            logger.info("Pagamento %s para pedido %s", "aprovado" if approved else "recusado", order_id)
        except Exception as e:
            logger.exception("Erro ao processar estoque.reservado: %s", e)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "pagamentos"}), 200


@app.route("/config", methods=["GET"])
def get_config():
    default = os.environ.get("PAGAMENTOS_SIMULAR_REJEICAO", "false").lower() == "true"
    simular = get_simular_rejeicao(default)
    return jsonify({"simularRejeicao": simular}), 200


@app.route("/config", methods=["POST"])
def post_config():
    body = request.get_json() or {}
    if "simularRejeicao" in body:
        value = bool(body["simularRejeicao"])
        set_simular_rejeicao(value)
        logger.info("Simulação de rejeição de pagamento: %s", value)
    simular = get_simular_rejeicao(False)
    return jsonify({"simularRejeicao": simular}), 200


def main():
    init_db()
    t = threading.Thread(target=consume_estoque_reservado, daemon=True)
    t.start()
    port = int(os.environ.get("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
