# Queues e bindings

Este documento cobre **queues** (filas) e **bindings** (vinculações) no RabbitMQ, conforme a documentação oficial.

## Queues (filas)

As **queues** são as estruturas que **armazenam** mensagens até que um consumer as consuma. Antes de usar uma queue, ela precisa ser **declarada** (criação idempotente: se já existir com os mesmos parâmetros, a declaração não faz nada; se os parâmetros forem diferentes, o broker pode retornar erro).

### Propriedades principais

- **Nome**: até 255 bytes UTF-8. Pode ser escolhido pela aplicação ou deixado vazio para o broker gerar um nome único (útil para filas temporárias). Nomes que começam com `amq.` são reservados.
- **Durable**: queue **durable** tem metadados persistidos em disco e sobrevive a reinício do broker. Queue **transient** existe apenas em memória (quando possível).
- **Exclusive**: se verdadeiro, a queue é usada apenas pela conexão que a declarou e é removida quando essa conexão fechar.
- **Auto-delete**: a queue é removida quando o **último consumer** se desinscreve (e ela teve pelo menos um consumer em algum momento).

Para **produção**, em geral usa-se queues **durable** e mensagens **persistent**, para não perder dados em reinícios.

### Durabilidade da mensagem

A durabilidade da **queue** (metadados em disco) é independente da durabilidade da **mensagem**. Para que mensagens sobrevivam a reinício, o **publisher** deve publicar com **delivery mode = persistent**. Só assim o broker persiste o corpo da mensagem em disco. Queue durable + mensagem non-persistent ainda pode perder o corpo da mensagem em crash.

## Bindings (vinculações)

**Bindings** são regras que ligam um **exchange** a uma **queue** (ou a outro exchange). Sem bindings, um exchange não sabe para onde enviar as mensagens.

- **Routing key (opcional)**: usada por exchanges **direct** e **topic** para filtrar quais mensagens vão para aquela queue. No direct é comparação exata; no topic é match por padrão (`*`, `#`).
- **Arguments (opcional)**: usados por alguns tipos (ex.: **headers** exchange com `x-match`).

Se uma mensagem chega a um exchange e **nenhuma** binding a encaminha para alguma queue, a mensagem pode ser **descartada** ou **devolvida** ao publisher, conforme as opções de publicação (e recursos como **alternate exchange** ou **dead letter**).

### Durabilidade dos bindings

Bindings herdam noção de “durabilidade” do exchange e do destino: se ambos forem durable, o binding é considerado durable. Em cenários com muitas filas transient, bindings semi-durable ou transient podem causar comportamento confuso após reinício; a documentação recomenda preferir queues durable (ou quorum queues) em produção.

## Declaração idempotente

- **queue.declare** com os mesmos parâmetros em queue existente → sucesso sem alterar a queue.
- **queue.declare** com parâmetros **diferentes** em queue já existente → o broker pode retornar erro (código 406 PRECONDITION_FAILED). O mesmo vale para **exchange.declare**.

Por isso, aplicações devem usar sempre os mesmos argumentos ao declarar queues e exchanges (ou tratar o erro e ajustar topologia).

## Resumo

| Conceito | Descrição |
|----------|-----------|
| Queue | Armazena mensagens; deve ser declarada antes do uso |
| Queue durable | Metadados em disco; sobrevive a reinício |
| Mensagem persistent | Publisher marca para persistir corpo em disco |
| Binding | Regra exchange → queue (com optional routing key/arguments) |
| Sem binding compatível | Mensagem pode ser descartada ou devolvida |

## Referências

- [Queues — RabbitMQ](https://www.rabbitmq.com/docs/queues)
- [AMQP 0-9-1 — Queues and Bindings](https://www.rabbitmq.com/tutorials/amqp-concepts.html#queues)
