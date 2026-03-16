# Quick Start

Este é um resumo dos passos para subir um ambiente RabbitMQ local e testar o básico. Para detalhes, use a [documentação oficial](https://www.rabbitmq.com/docs) e os [tutoriais](https://www.rabbitmq.com/tutorials).

## Pré-requisitos

- **Docker** (recomendado) ou instalação nativa do Erlang e RabbitMQ no seu sistema.

## 1. Subir o RabbitMQ com Docker

```bash
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:4-management
```

- **5672**: porta AMQP (clientes).
- **15672**: interface web do **Management plugin** (usuário/senha padrão: `guest` / `guest`; em produção altere e não exponha guest).

Acesse: http://localhost:15672

## 2. Criar uma queue e publicar “direto” nela (default exchange)

Com a imagem `rabbitmq:4-management` você pode usar a aba **Queues** para criar uma queue, por exemplo `minha-fila`. Ou use um cliente AMQP (ex.: Python com `pika`, Node com `amqplib`).

Exemplo conceitual (Python com `pika`):

```python
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declara a queue (idempotente)
channel.queue_declare(queue='minha-fila', durable=True)

# Publica no default exchange com routing key = nome da queue
channel.basic_publish(
    exchange='',
    routing_key='minha-fila',
    body='Olá, RabbitMQ!',
    properties=pika.BasicProperties(delivery_mode=2)  # persistent
)

connection.close()
```

## 3. Consumir mensagens

```python
import pika

def callback(ch, method, properties, body):
    print(f"Recebido: {body.decode()}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='minha-fila', durable=True)
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='minha-fila', on_message_callback=callback)

channel.start_consuming()
```

## 4. Testar com a Management UI

- Em **Queues**, crie uma queue (ex.: `teste`).
- Em **Publish message**, escolha o default exchange (``) e routing key `teste`, envie um corpo e publique.
- Em **Get messages** na queue `teste`, você pode puxar mensagens manualmente para inspecionar.

## 5. Encerrar

```bash
docker stop rabbitmq
docker rm rabbitmq
```

## Próximo passo

Depois do Quick Start, vale revisar [Operações e monitoramento](11-operacoes-e-monitoramento.md), [Melhores práticas](09-melhores-praticas.md) e os [tutoriais oficiais](https://www.rabbitmq.com/tutorials) (Hello World, Work Queues, Pub/Sub, Routing, Topics).

## Referências

- [Get Started — RabbitMQ](https://www.rabbitmq.com/docs/get-started)
- [Tutorials — RabbitMQ](https://www.rabbitmq.com/tutorials)
- [Docker — RabbitMQ](https://www.rabbitmq.com/docs/download#docker)
