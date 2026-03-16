# Semânticas e confirmações

Este documento cobre **garantias de entrega** e **confirmações** (acknowledgements e publisher confirms) no RabbitMQ, conforme a documentação oficial.

## Quando o broker remove a mensagem da queue?

No AMQP 0-9-1, o **consumer** controla quando a mensagem pode ser removida da queue:

- **Manual ack (recomendado)**: o broker só remove a mensagem quando o consumer envia **basic.ack** (ou basic.nack com discard). Assim, se o consumer cair antes de processar, a mensagem volta a ficar disponível (ou é reenviada) e pode ser processada por outro consumer.
- **Auto ack**: o broker considera a mensagem entregue assim que a envia ao consumer (equivalente a remover da queue na entrega). Se o consumer cair depois de receber e antes de processar, a mensagem é **perdida**. Só use quando a perda for aceitável.

Para **at-least-once** (não perder, mas aceitar possível reprocessamento), use **manual ack** e confirme **apenas após** processar com sucesso (e, se aplicável, persistir em banco ou downstream).

## Semânticas de entrega

| Semântica | Descrição |
|-----------|-----------|
| **At most once** | Mensagem pode ser perdida (ex.: auto ack e consumer cai). Não é reenviada. |
| **At least once** | Mensagem não é removida até o ack; se o consumer cair, pode ser reenviada e processada mais de uma vez. |
| **Exactly once** | Requer idempotência no consumer e/ou transações/distributed protocols; o RabbitMQ em si não oferece exactly-once end-to-end nativo. |

Na prática: use **manual ack** após processamento bem-sucedido para **at-least-once**; implemente **idempotência** no consumer para tolerar duplicatas (ex.: chave única no banco, ou “já processado” por message-id).

## Rejeição e requeue

- **basic.reject**: o consumer indica que não processou (ou não pode processar) a mensagem. Pode pedir **requeue** (mensagem volta para a queue) ou **discard**.
- **basic.nack** (extensão RabbitMQ): como reject, mas permite rejeitar **várias** mensagens de uma vez (útil com prefetch > 1), com opção de requeue.

Cuidado com **requeue** quando há um único consumer: se o consumer rejeitar e requeuear sempre (ex.: erro persistente), pode gerar loop infinito de entrega. Use **dead letter queue (DLQ)** para mensagens que falham após N tentativas.

## Publisher confirms

Do lado do **publisher**, enviar uma mensagem não garante que ela foi **aceita** pelo broker (pode falhar disco, memória, etc.). O RabbitMQ oferece **publisher confirms** (modo confirm): o broker envia um **ack** (ou **nack**) para cada mensagem (ou lote) publicada. Assim o publisher sabe se a mensagem foi persistida e pode retentar ou gravar em log.

- **Confirmar em modo publisher** é ativar o canal em “confirm mode”; depois cada **basic.publish** é confirmado com **basic.ack** ou **basic.nack** pelo broker.
- Em produção, use **publisher confirms** quando não puder perder mensagens no caminho até o broker.

## Resumo

| Aspecto | Ideia principal |
|--------|------------------|
| Manual ack | Broker só remove mensagem após basic.ack; evita perda se consumer cair |
| Auto ack | Entrega = remoção; risco de perda; use só se aceitável |
| At-least-once | Manual ack após processar + idempotência no consumer |
| Reject/Nack | Requeue ou discard; evitar loops com DLQ para falhas permanentes |
| Publisher confirms | Garantir que o broker aceitou a mensagem antes de considerar “enviado” |

## Referências

- [Consumer Acknowledgements and Publisher Confirms — RabbitMQ](https://www.rabbitmq.com/docs/confirms)
- [AMQP 0-9-1 — Message Acknowledgements](https://www.rabbitmq.com/tutorials/amqp-concepts.html#message-acknowledgements)
- [Negative Acknowledgements (nack)](https://www.rabbitmq.com/docs/nack)
