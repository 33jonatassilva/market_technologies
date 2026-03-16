# Exchanges e tipos

Este documento descreve os **exchanges** e seus **tipos** no modelo AMQP 0-9-1, conforme a documentação do RabbitMQ.

## O que é um exchange?

Um **exchange** é a entidade para onde os **publishers** enviam mensagens. O exchange **não armazena** mensagens; ele recebe cada mensagem e a **roteia** para uma ou mais queues (ou para outros exchanges) com base em:

- O **tipo** do exchange (direct, fanout, topic, headers).
- As **bindings** definidas entre o exchange e as queues (e opcionalmente a routing key ou padrão do binding).

Cada exchange pertence a um **virtual host** (vhost). Exchanges podem ser **durable** (sobrevivem a reinício) ou **transient**, e podem ser **auto-delete** (excluídos quando a última binding for removida).

## Default exchange

O **default exchange** é um exchange **direct** pré-declarado, com nome vazio (`""`). Ele tem uma propriedade especial:

- Toda **queue** criada é automaticamente **ligada** a ele com **routing key igual ao nome da queue**.

Assim, para publicar “diretamente” em uma queue chamada `minha-fila`, o publisher envia para o default exchange (nome `""`) com routing key `minha-fila`. Não é permitido criar bindings adicionais no default exchange; ele serve apenas a esse uso direto por nome de fila.

## Direct exchange

- Roteamento por **igualdade** da **routing key**.
- A mensagem vai para toda queue que estiver **bound** ao exchange com uma routing key **igual** à routing key da mensagem.
- Uso típico: **unicast** (uma fila por “assunto”) ou multicast quando várias queues usam a mesma routing key.

Exemplo: binding `routing_key = "pagamentos"` → mensagens com `routing_key = "pagamentos"` vão para essa queue.

## Fanout exchange

- **Ignora** a routing key.
- Envia uma **cópia** da mensagem para **todas** as queues (e exchanges) ligadas a ele.
- Uso típico: **broadcast** — notificar todos os assinantes (ex.: atualização de configuração, evento “pedido criado” para estoque, notificações e analytics).

## Topic exchange

- Roteamento por **padrão** sobre a routing key.
- A routing key é tratada como segmentos separados por `.` (ex.: `pedidos.vendas.pago`).
- **Wildcards** no binding:
  - `*` — corresponde a **exatamente um** segmento.
  - `#` — corresponde a **zero ou mais** segmentos.

Exemplos de bindings:

- `"#"` → recebe todas as mensagens (como um fanout para essa binding).
- `"pedidos.#"` → `pedidos`, `pedidos.vendas`, `pedidos.vendas.pago`, etc.
- `"pedidos.*.pago"` → `pedidos.vendas.pago`, `pedidos.loja.pago`, mas não `pedidos.pago` (falta um segmento no meio) nem `pedidos.vendas.outro.pago`.

Uso típico: **pub/sub** com seleção por “tópico” ou categoria (eventos por tipo, por região, etc.).

## Headers exchange

- Roteamento com base em **headers** (atributos) da mensagem, não na routing key.
- Cada binding define condições sobre os headers (e opcionalmente `x-match`: **any** ou **all**).
  - **all**: todos os headers especificados devem bater.
  - **any**: basta um bater.
- Útil quando o critério de roteamento é multi-dimensional (ex.: `região=br` e `prioridade=alta`) ou quando não se quer usar uma string única como routing key.

## Resumo

| Tipo      | Critério de roteamento        | Uso típico              |
|-----------|-------------------------------|--------------------------|
| default   | Routing key = nome da queue   | Publicar “direto” na fila |
| direct    | Routing key exata             | Unicast / roteamento simples |
| fanout    | Nenhum (broadcast)            | Broadcast para todos     |
| topic     | Padrão com `*` e `#`          | Pub/sub por tópico       |
| headers   | Match em headers (any/all)    | Roteamento por atributos |

## Referências

- [AMQP 0-9-1 Model — Exchanges](https://www.rabbitmq.com/tutorials/amqp-concepts.html#exchanges)
- [Exchanges — RabbitMQ](https://www.rabbitmq.com/docs/exchanges)
