# Sistema de vendas — microserviços e Kafka (implementação)

Implementação em Docker do sistema descrito em [sistema-vendas-microservicos-kafka.md](sistema-vendas-microservicos-kafka.md): quatro serviços (Pedidos, Estoque, Pagamentos, Notificações) comunicando via Apache Kafka.

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/install/) instalados.

## Como subir o sistema

Na pasta `microservices+kafka`:

```bash
docker compose up -d --build
```

Isso sobe:

- **Kafka** — imagem oficial [apache/kafka](https://hub.docker.com/r/apache/kafka) (modo KRaft, sem Zookeeper) na porta **9092**.
- **Pedidos** — API REST na porta **5001**.
- **Estoque** — API de saúde/consulta na porta **5002**.
- **Pagamentos** — health na porta **5003**.
- **Notificações** — health na porta **5004**.

O Kafka possui healthcheck; os serviços de aplicação só iniciam após o Kafka estar saudável. Na primeira subida, o Kafka pode levar cerca de 15–30 segundos para ficar pronto; se um serviço falhar ao conectar, aguarde e reinicie os containers (`docker compose restart pedidos estoque pagamentos notificacoes`).

## Como testar o fluxo

1. **Criar um pedido** (serviço Pedidos):

   ```bash
   curl -X POST http://localhost:5001/pedidos \
     -H "Content-Type: application/json" \
     -d '{"customerId": "cli-1", "items": [{"productId": "P1", "quantity": 2}], "total": 19.90}'
   ```

   A resposta traz `orderId` e `status: criado`.

2. **Consultar o status do pedido**:

   ```bash
   curl http://localhost:5001/pedidos/<ORDER_ID>
   ```

   Após alguns segundos o status deve ir para `confirmado` (fluxo: estoque reservado → pagamento aprovado → pedido confirmado).

3. **Ver a “notificação”** (simulada em log):

   ```bash
   docker logs notificacoes
   ```

   Deve aparecer uma linha indicando pedido confirmado e “E-mail/SMS enviado (simulado)”.

4. **Consultar estoque** (opcional):

   ```bash
   curl http://localhost:5002/estoque
   ```

   Mostra quantidades disponíveis e reservas por pedido.

## Endpoints por serviço

| Serviço       | Porta | Endpoints |
|---------------|-------|-----------|
| Pedidos       | 5001  | `POST /pedidos`, `GET /pedidos/<id>`, `GET /health` |
| Estoque       | 5002  | `GET /estoque`, `GET /health` |
| Pagamentos    | 5003  | `GET /health` |
| Notificações  | 5004  | `GET /health` |

## Tópicos Kafka utilizados

- `pedidos.criados` — Pedidos publica; Estoque consome.
- `estoque.reservado` — Estoque publica (EstoqueReservado / EstoqueInsuficiente); Pagamentos e Pedidos consomem.
- `pagamentos.processados` — Pagamentos publica; Pedidos consome.
- `pedidos.confirmados` — Pedidos publica; Notificações consome.

Os tópicos são criados automaticamente na primeira publicação (Kafka com auto-create habilitado).

## Parar o ambiente

```bash
docker compose down
```

## Documentação da arquitetura

A arquitetura, fluxo de eventos, resiliência e papel do Kafka estão descritos em [sistema-vendas-microservicos-kafka.md](sistema-vendas-microservicos-kafka.md).
