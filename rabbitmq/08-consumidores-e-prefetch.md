# Consumidores e prefetch

Este documento cobre o comportamento dos **consumers** e o uso de **prefetch** no RabbitMQ, conforme a documentação oficial.

## Inscrição na queue (push)

- O consumer **se inscreve** em uma queue (registra um consumer / subscription). A partir daí, o broker **entrega** mensagens (push) para esse consumer.
- Cada inscrição tem um **consumer tag** (identificador), usado para cancelar a inscrição (unsubscribe).
- É possível ter **vários consumers** na mesma queue: o broker distribui as mensagens entre eles (round-robin entre consumers prontos). Ou usar **consumer exclusivo**, que impede outros consumers na mesma queue enquanto estiver ativo.

## Prefetch (Qos)

- **Prefetch** limita quantas mensagens **não confirmadas** (unacked) um consumer pode ter “em voo” ao mesmo tempo. O broker não envia mais mensagens para esse consumer até que ele confirme (ack ou nack) algumas.
- Objetivos:
  - **Balanceamento de carga**: consumers mais lentos não acumulam todas as mensagens; as mais rápidas recebem mais.
  - **Controle de throughput**: evitar que um consumer receba um volume maior do que consegue processar, acumulando em memória.
- No RabbitMQ o prefetch é por **canal** (**channel-level**), não por conexão nem por tamanho em bytes (em outras palavras: prefetch-count apenas).
- Valores típicos: começar com algo como 10–50 mensagens; aumentar se o processamento for muito rápido, diminuir se for pesado e você quiser distribuir melhor entre consumers.

## Múltiplos consumers na mesma queue

- Várias instâncias do mesmo serviço podem consumir da **mesma queue**. O broker entrega cada mensagem a **um** consumer (não broadcast). Assim, a carga é distribuída e a fila funciona como **task queue**.
- Para **broadcast** (uma cópia para cada assinante), use um **exchange fanout** (ou topic) com **uma queue por consumer** (ex.: queue exclusiva ou nomeada por instância), e cada queue ligada ao mesmo exchange.

## Single active consumer (SAC)

- Em **quorum queues** (e em cenários suportados), o recurso **single active consumer** garante que apenas **um** consumer ativo processe mensagens da queue por vez; se esse consumer cair, outro assume. Útil para garantir ordem de processamento sem particionar a fila.

## Resumo

| Aspecto | Ideia principal |
|--------|------------------|
| Push | Consumer se inscreve; broker entrega mensagens quando há disponível |
| Vários consumers | Mesma queue → distribuição de carga (uma mensagem por consumer) |
| Prefetch | Limite de mensagens unacked por canal; balanceamento e controle de carga |
| Single active consumer | Apenas um consumer ativo por vez (em quorum queues); ordem garantida |

## Referências

- [Consumers — RabbitMQ](https://www.rabbitmq.com/docs/consumers)
- [AMQP 0-9-1 — Prefetching](https://www.rabbitmq.com/tutorials/amqp-concepts.html#prefetching)
- [Quorum Queues — Single Active Consumer](https://www.rabbitmq.com/docs/quorum-queues#single-active-consumer)
