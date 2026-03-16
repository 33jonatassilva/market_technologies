"""
Serviço de Pagamentos: consome EstoqueReservado de estoque.reservado,
simula processamento e publica PagamentoAprovado ou PagamentoRecusado em pagamentos.processados.
"""
import json
import logging
import os
import threading
import random
from flask import Flask, jsonify
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pagamentos")

app = Flask(__name__)
KAFKA_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")

TOPIC_ESTOQUE_RESERVADO = "estoque.reservado"
TOPIC_PAGAMENTOS_PROCESSADOS = "pagamentos.processados"

# Para demonstração: ~80% aprovação (simula gateway)
SIMULAR_REJEICAO = os.environ.get("PAGAMENTOS_SIMULAR_REJEICAO", "false").lower() == "true"


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
            # Simula processamento: aprovação aleatória se SIMULAR_REJEICAO, senão sempre aprova
            approved = random.random() > 0.2 if SIMULAR_REJEICAO else True
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


def main():
    t = threading.Thread(target=consume_estoque_reservado, daemon=True)
    t.start()
    port = int(os.environ.get("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
